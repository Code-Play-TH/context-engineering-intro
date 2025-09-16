"""
Social media background tasks for KOL Management System.
Handles content monitoring, data collection, and performance tracking.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import current_task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import get_db
from app.services.social_media import (
    social_media_factory, get_kol_profile_data, get_kol_recent_content,
    verify_campaign_content, search_content_by_hashtag
)
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.content import ContentPost, ContentStats, ContentAlert, VerificationStatus, ContentType
from app.schemas.content import ContentPostCreate, ContentStatsCreate

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def collect_kol_profile_data(self, kol_id: int, platforms: List[str] = None) -> Dict[str, Any]:
    """
    Collect and update KOL profile data from social media platforms.

    Args:
        kol_id: KOL ID
        platforms: List of platforms to collect from (default: all)

    Returns:
        Dict with collection results
    """
    task_id = self.request.id
    logger.info(f"Collecting profile data for KOL {kol_id}")

    with next(get_db()) as db:
        try:
            # Get KOL
            kol = db.query(KOL).filter(KOL.id == kol_id).first()
            if not kol:
                raise ValueError(f"KOL {kol_id} not found")

            # Default to all platforms if none specified
            if not platforms:
                platforms = list(kol.social_media_accounts.keys())

            results = {
                "task_id": task_id,
                "kol_id": kol_id,
                "platforms": platforms,
                "successful": 0,
                "failed": 0,
                "updates": []
            }

            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 0, "total": len(platforms), "status": "Starting data collection"}
            )

            # Collect data from each platform
            for i, platform in enumerate(platforms):
                try:
                    account_data = kol.social_media_accounts.get(platform, {})
                    user_id = account_data.get("handle") or account_data.get("id")

                    if not user_id:
                        logger.warning(f"No user ID found for KOL {kol_id} on {platform}")
                        results["failed"] += 1
                        continue

                    # Get access token if available
                    access_token = account_data.get("access_token")

                    # Collect profile data
                    import asyncio
                    profile_data = asyncio.run(get_kol_profile_data(platform, user_id, access_token))

                    # Update KOL record
                    follower_count = profile_data.get("follower_count", 0)
                    kol.follower_counts[platform] = follower_count

                    # Update social media account data
                    kol.social_media_accounts[platform].update({
                        "display_name": profile_data.get("display_name"),
                        "bio": profile_data.get("bio"),
                        "profile_picture_url": profile_data.get("profile_picture_url"),
                        "verified": profile_data.get("verified", False),
                        "updated_at": datetime.utcnow().isoformat()
                    })

                    results["updates"].append({
                        "platform": platform,
                        "follower_count": follower_count,
                        "verified": profile_data.get("verified", False),
                        "success": True
                    })

                    results["successful"] += 1

                    # Update progress
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i + 1,
                            "total": len(platforms),
                            "status": f"Updated {platform}"
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to collect data for KOL {kol_id} on {platform}: {str(e)}")
                    results["updates"].append({
                        "platform": platform,
                        "success": False,
                        "error": str(e)
                    })
                    results["failed"] += 1

                # Small delay between platforms to respect rate limits
                import time
                time.sleep(1)

            # Update KOL record
            kol.last_performance_update = datetime.utcnow()
            db.commit()

            logger.info(f"Profile data collection for KOL {kol_id} completed: {results['successful']} successful, {results['failed']} failed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Profile data collection task failed: {str(e)}")
            raise self.retry(countdown=300, exc=e)  # Retry in 5 minutes


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def collect_kol_content_data(self, kol_id: int, platforms: List[str] = None, limit: int = 25) -> Dict[str, Any]:
    """
    Collect recent content from KOL's social media platforms.

    Args:
        kol_id: KOL ID
        platforms: List of platforms to collect from
        limit: Number of recent posts to collect per platform

    Returns:
        Dict with collection results
    """
    task_id = self.request.id
    logger.info(f"Collecting content data for KOL {kol_id}")

    with next(get_db()) as db:
        try:
            # Get KOL
            kol = db.query(KOL).filter(KOL.id == kol_id).first()
            if not kol:
                raise ValueError(f"KOL {kol_id} not found")

            # Default to all platforms if none specified
            if not platforms:
                platforms = list(kol.social_media_accounts.keys())

            results = {
                "task_id": task_id,
                "kol_id": kol_id,
                "platforms": platforms,
                "total_content": 0,
                "new_content": 0,
                "updated_content": 0,
                "platform_results": []
            }

            # Collect content from each platform
            for platform in platforms:
                try:
                    account_data = kol.social_media_accounts.get(platform, {})
                    user_id = account_data.get("handle") or account_data.get("id")

                    if not user_id:
                        continue

                    access_token = account_data.get("access_token")

                    # Get recent content
                    import asyncio
                    content_data = asyncio.run(get_kol_recent_content(platform, user_id, access_token, limit))

                    platform_result = {
                        "platform": platform,
                        "total_posts": len(content_data.get("data", [])),
                        "new_posts": 0,
                        "updated_posts": 0
                    }

                    # Process each content item
                    for content_item in content_data.get("data", []):
                        platform_post_id = content_item.get("platform_post_id")
                        if not platform_post_id:
                            continue

                        # Check if content already exists
                        existing_content = db.query(ContentPost).filter(
                            ContentPost.platform_post_id == platform_post_id,
                            ContentPost.platform == platform
                        ).first()

                        if existing_content:
                            # Update existing content stats
                            existing_content.like_count = content_item.get("like_count", 0)
                            existing_content.comment_count = content_item.get("comment_count", 0)
                            existing_content.share_count = content_item.get("share_count", 0)
                            existing_content.view_count = content_item.get("view_count", 0)
                            existing_content.updated_at = datetime.utcnow()

                            platform_result["updated_posts"] += 1
                            results["updated_content"] += 1
                        else:
                            # Create new content record
                            content_post = ContentPost(
                                kol_id=kol_id,
                                campaign_id=None,  # Will be linked during campaign matching
                                platform=platform,
                                platform_post_id=platform_post_id,
                                url=content_item.get("permalink", ""),
                                content=content_item.get("content", ""),
                                content_type=ContentType(content_item.get("content_type", "post")),
                                hashtags=content_item.get("hashtags", []),
                                mentions=content_item.get("mentions", []),
                                media_urls=content_item.get("media", []),
                                posted_at=datetime.fromisoformat(content_item["posted_at"].replace("Z", "+00:00")) if content_item.get("posted_at") else datetime.utcnow(),
                                detected_at=datetime.utcnow(),
                                verification_status=VerificationStatus.PENDING,
                                confidence_score=0.8,  # Default confidence for direct collection
                                match_criteria=["direct_collection"]
                            )

                            db.add(content_post)
                            platform_result["new_posts"] += 1
                            results["new_content"] += 1

                    results["platform_results"].append(platform_result)
                    results["total_content"] += platform_result["total_posts"]

                except Exception as e:
                    logger.error(f"Failed to collect content for KOL {kol_id} on {platform}: {str(e)}")
                    results["platform_results"].append({
                        "platform": platform,
                        "error": str(e),
                        "success": False
                    })

            db.commit()

            logger.info(f"Content collection for KOL {kol_id} completed: {results['new_content']} new, {results['updated_content']} updated")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Content collection task failed: {str(e)}")
            raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True)
def monitor_campaign_content(self, campaign_id: int) -> Dict[str, Any]:
    """
    Monitor social media for content related to a specific campaign.

    Args:
        campaign_id: Campaign ID

    Returns:
        Dict with monitoring results
    """
    task_id = self.request.id
    logger.info(f"Monitoring content for campaign {campaign_id}")

    with next(get_db()) as db:
        try:
            # Get campaign
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Get campaign criteria
            hashtags = campaign.hashtags or []
            keywords = campaign.keywords or []

            results = {
                "task_id": task_id,
                "campaign_id": campaign_id,
                "hashtags_monitored": hashtags,
                "keywords_monitored": keywords,
                "total_found": 0,
                "verified_matches": 0,
                "potential_matches": 0,
                "platform_results": []
            }

            # Monitor each platform
            platforms = ["instagram", "youtube", "tiktok", "twitter", "facebook"]

            for platform in platforms:
                try:
                    platform_content = []

                    # Search by hashtags
                    for hashtag in hashtags:
                        import asyncio
                        content = asyncio.run(search_content_by_hashtag(platform, hashtag, limit=20))
                        platform_content.extend(content)

                    platform_result = {
                        "platform": platform,
                        "total_found": len(platform_content),
                        "new_matches": 0,
                        "verified_matches": 0
                    }

                    # Process found content
                    for content_item in platform_content:
                        platform_post_id = content_item.get("platform_post_id")
                        if not platform_post_id:
                            continue

                        # Check if already exists
                        existing = db.query(ContentPost).filter(
                            ContentPost.platform_post_id == platform_post_id,
                            ContentPost.platform == platform
                        ).first()

                        if existing:
                            continue

                        # Verify content matches campaign criteria
                        import asyncio
                        is_match, confidence, match_criteria = asyncio.run(verify_campaign_content(
                            platform,
                            content_item,
                            {
                                "required_hashtags": hashtags,
                                "keywords": keywords,
                                "start_date": campaign.start_date,
                                "end_date": campaign.end_date
                            }
                        ))

                        if is_match and confidence > 0.5:
                            # Try to find the KOL
                            kol = None
                            author_handle = content_item.get("author", {}).get("username")
                            if author_handle:
                                # Search for KOL by handle
                                kol = db.query(KOL).filter(
                                    KOL.social_media_accounts.op('?')(platform),
                                    KOL.social_media_accounts[platform]["handle"].astext == author_handle
                                ).first()

                            # Create content record
                            content_post = ContentPost(
                                kol_id=kol.id if kol else None,
                                campaign_id=campaign_id,
                                platform=platform,
                                platform_post_id=platform_post_id,
                                url=content_item.get("permalink", ""),
                                content=content_item.get("content", ""),
                                content_type=ContentType(content_item.get("content_type", "post")),
                                hashtags=content_item.get("hashtags", []),
                                mentions=content_item.get("mentions", []),
                                media_urls=content_item.get("media", []),
                                posted_at=datetime.fromisoformat(content_item["posted_at"].replace("Z", "+00:00")) if content_item.get("posted_at") else datetime.utcnow(),
                                detected_at=datetime.utcnow(),
                                verification_status=VerificationStatus.AUTO_VERIFIED if confidence > 0.8 else VerificationStatus.PENDING,
                                confidence_score=confidence,
                                match_criteria=match_criteria
                            )

                            db.add(content_post)
                            platform_result["new_matches"] += 1

                            if confidence > 0.8:
                                platform_result["verified_matches"] += 1
                                results["verified_matches"] += 1
                            else:
                                results["potential_matches"] += 1

                    results["platform_results"].append(platform_result)
                    results["total_found"] += platform_result["total_found"]

                except Exception as e:
                    logger.error(f"Failed to monitor {platform} for campaign {campaign_id}: {str(e)}")

            db.commit()

            logger.info(f"Campaign monitoring completed: {results['verified_matches']} verified, {results['potential_matches']} potential")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Campaign monitoring task failed: {str(e)}")
            raise


@celery_app.task(bind=True)
def collect_performance_data(self, content_post_ids: List[int] = None) -> Dict[str, Any]:
    """
    Collect performance data for content posts.

    Args:
        content_post_ids: Specific content post IDs (optional)

    Returns:
        Dict with collection results
    """
    task_id = self.request.id
    logger.info("Collecting performance data for content posts")

    with next(get_db()) as db:
        try:
            # Get content posts to update
            if content_post_ids:
                content_posts = db.query(ContentPost).filter(ContentPost.id.in_(content_post_ids)).all()
            else:
                # Get recent posts that need updates (last 7 days, not updated in last hour)
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                seven_days_ago = datetime.utcnow() - timedelta(days=7)

                content_posts = db.query(ContentPost).filter(
                    ContentPost.posted_at >= seven_days_ago,
                    ContentPost.updated_at <= one_hour_ago
                ).limit(100).all()  # Limit to prevent overwhelming APIs

            results = {
                "task_id": task_id,
                "total_posts": len(content_posts),
                "successful": 0,
                "failed": 0,
                "stats_collected": []
            }

            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 0, "total": len(content_posts), "status": "Starting performance collection"}
            )

            # Collect performance data for each post
            for i, post in enumerate(content_posts):
                try:
                    # Get platform service
                    service = social_media_factory.get_service(post.platform)

                    # Get KOL's access token if available
                    access_token = None
                    if post.kol and post.kol.social_media_accounts.get(post.platform):
                        access_token = post.kol.social_media_accounts[post.platform].get("access_token")

                    # Collect performance data based on platform
                    performance_data = {}
                    async with service:
                        if post.platform == "instagram":
                            performance_data = await service.get_media_insights(post.platform_post_id, access_token)
                        elif post.platform == "youtube":
                            performance_data = await service.get_video_analytics(post.platform_post_id, access_token)
                        elif post.platform == "facebook":
                            performance_data = await service.get_post_insights(post.platform_post_id, access_token)
                        # Add other platform-specific analytics as needed

                    if performance_data:
                        # Create content stats record
                        stats = ContentStats(
                            content_post_id=post.id,
                            collected_at=datetime.utcnow(),
                            collection_interval="1hr",
                            likes=performance_data.get("likes", 0),
                            comments=performance_data.get("comments", 0),
                            shares=performance_data.get("shares", 0),
                            views=performance_data.get("views"),
                            reach=performance_data.get("reach"),
                            impressions=performance_data.get("impressions"),
                            platform_specific_metrics=performance_data,
                            collection_method="api"
                        )

                        # Calculate engagement rate
                        stats.calculate_engagement_rate()

                        db.add(stats)

                        results["stats_collected"].append({
                            "post_id": post.id,
                            "platform": post.platform,
                            "likes": stats.likes,
                            "comments": stats.comments,
                            "engagement_rate": stats.engagement_rate
                        })

                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                    # Update progress
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i + 1,
                            "total": len(content_posts),
                            "status": f"Processed {post.platform} post"
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to collect performance data for post {post.id}: {str(e)}")
                    results["failed"] += 1

                # Rate limiting delay
                import time
                time.sleep(0.5)

            db.commit()

            logger.info(f"Performance data collection completed: {results['successful']} successful, {results['failed']} failed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Performance data collection task failed: {str(e)}")
            raise


@celery_app.task
def update_kol_engagement_rates(kol_ids: List[int] = None) -> Dict[str, Any]:
    """
    Update engagement rates for KOLs based on recent content performance.

    Args:
        kol_ids: Specific KOL IDs (optional)

    Returns:
        Dict with update results
    """
    logger.info("Updating KOL engagement rates")

    with next(get_db()) as db:
        try:
            # Get KOLs to update
            if kol_ids:
                kols = db.query(KOL).filter(KOL.id.in_(kol_ids)).all()
            else:
                # Get all active KOLs
                kols = db.query(KOL).filter(KOL.status == "active").all()

            results = {
                "total_kols": len(kols),
                "updated": 0,
                "failed": 0,
                "engagement_rates": []
            }

            # Calculate engagement rates for each KOL
            for kol in kols:
                try:
                    # Get recent content (last 30 days)
                    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                    recent_content = db.query(ContentPost).filter(
                        ContentPost.kol_id == kol.id,
                        ContentPost.posted_at >= thirty_days_ago
                    ).all()

                    if not recent_content:
                        continue

                    platform_engagement = {}

                    # Calculate engagement rate by platform
                    for platform in kol.follower_counts.keys():
                        platform_posts = [p for p in recent_content if p.platform == platform]
                        if not platform_posts:
                            continue

                        # Get latest stats for each post
                        total_engagement = 0
                        total_reach = 0
                        posts_with_stats = 0

                        for post in platform_posts:
                            latest_stats = post.get_latest_stats()
                            if latest_stats and latest_stats.reach:
                                total_engagement += latest_stats.likes + latest_stats.comments + latest_stats.shares
                                total_reach += latest_stats.reach
                                posts_with_stats += 1

                        if posts_with_stats > 0 and total_reach > 0:
                            engagement_rate = (total_engagement / total_reach) * 100
                            platform_engagement[platform] = round(engagement_rate, 2)

                    # Update KOL engagement rates
                    kol.engagement_rates = platform_engagement
                    kol.last_performance_update = datetime.utcnow()

                    results["engagement_rates"].append({
                        "kol_id": kol.id,
                        "kol_name": kol.name,
                        "engagement_rates": platform_engagement
                    })

                    results["updated"] += 1

                except Exception as e:
                    logger.error(f"Failed to update engagement rate for KOL {kol.id}: {str(e)}")
                    results["failed"] += 1

            db.commit()

            logger.info(f"Engagement rate update completed: {results['updated']} updated, {results['failed']} failed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Engagement rate update task failed: {str(e)}")
            raise