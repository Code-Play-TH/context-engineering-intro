"""
Content Monitoring Background Tasks

Celery tasks for automated content monitoring and statistics collection.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_session
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.content import ContentPost, ContentStats
from app.services.content_monitoring.content_monitor import ContentMonitorService
from app.services.social_media.factory import SocialMediaServiceFactory
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def detect_campaign_content(self, campaign_id: int):
    """
    Detect content for all KOLs in a campaign.

    Args:
        campaign_id: ID of the campaign to monitor
    """
    try:
        import asyncio
        return asyncio.run(_detect_campaign_content_async(campaign_id))
    except Exception as exc:
        logger.error(f"Content detection failed for campaign {campaign_id}: {exc}")
        # Exponential backoff retry
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown, max_retries=3)


async def _detect_campaign_content_async(campaign_id: int) -> Dict[str, Any]:
    """
    Async implementation of campaign content detection.

    Args:
        campaign_id: ID of the campaign to monitor

    Returns:
        Detection results summary
    """
    async with get_session() as db:
        # Get campaign with KOLs
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get all KOLs in this campaign
        stmt = select(KOL).join(Campaign.kols).where(Campaign.id == campaign_id)
        result = await db.execute(stmt)
        kols = result.scalars().all()

        if not kols:
            logger.warning(f"No KOLs found for campaign {campaign_id}")
            return {"detected_posts": 0, "kols_processed": 0}

        monitor_service = ContentMonitorService(db)
        total_detected = 0

        for kol in kols:
            try:
                detected_posts = await monitor_service.detect_new_content(kol, campaign)
                total_detected += len(detected_posts)
                logger.info(f"Detected {len(detected_posts)} posts for KOL {kol.id}")
            except Exception as e:
                logger.error(f"Failed to detect content for KOL {kol.id}: {e}")
                continue

        return {
            "detected_posts": total_detected,
            "kols_processed": len(kols),
            "campaign_id": campaign_id
        }


@celery_app.task(bind=True, max_retries=3)
def collect_content_stats(self, content_post_id: int):
    """
    Collect statistics for a specific content post.

    Args:
        content_post_id: ID of the content post
    """
    try:
        import asyncio
        return asyncio.run(_collect_content_stats_async(content_post_id))
    except Exception as exc:
        logger.error(f"Stats collection failed for post {content_post_id}: {exc}")
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown, max_retries=3)


async def _collect_content_stats_async(content_post_id: int) -> Dict[str, Any]:
    """
    Async implementation of content statistics collection.

    Args:
        content_post_id: ID of the content post

    Returns:
        Collected statistics
    """
    async with get_session() as db:
        # Get content post
        stmt = select(ContentPost).where(ContentPost.id == content_post_id)
        result = await db.execute(stmt)
        content_post = result.scalar_one_or_none()

        if not content_post:
            raise ValueError(f"Content post {content_post_id} not found")

        # Get social media service for the platform
        factory = SocialMediaServiceFactory()
        service = factory.get_service(content_post.platform)

        if not service:
            raise ValueError(f"No service available for platform {content_post.platform}")

        try:
            # Collect current statistics
            stats_data = await service.get_post_statistics(
                content_post.platform_post_id
            )

            # Create new stats record
            content_stats = ContentStats(
                content_post_id=content_post.id,
                collected_at=datetime.utcnow(),
                likes=stats_data.get('likes', 0),
                comments=stats_data.get('comments', 0),
                shares=stats_data.get('shares', 0),
                views=stats_data.get('views', 0),
                reach=stats_data.get('reach', 0),
                engagement_rate=stats_data.get('engagement_rate', 0.0),
                collection_interval=_get_collection_interval(content_post.posted_at)
            )

            db.add(content_stats)
            await db.commit()

            logger.info(f"Collected stats for post {content_post_id}: {stats_data}")

            return {
                "content_post_id": content_post_id,
                "statistics": stats_data,
                "collection_time": content_stats.collected_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to collect stats for post {content_post_id}: {e}")
            raise


def _get_collection_interval(posted_at: datetime) -> str:
    """
    Determine the collection interval based on when the post was created.

    Args:
        posted_at: When the post was originally created

    Returns:
        Collection interval identifier
    """
    now = datetime.utcnow()
    days_since_post = (now - posted_at).days

    if days_since_post <= 1:
        return "24hr"
    elif days_since_post <= 3:
        return "3day"
    elif days_since_post <= 5:
        return "5day"
    else:
        return "7day"


@celery_app.task(bind=True)
def schedule_content_monitoring(self, campaign_id: int):
    """
    Schedule regular content monitoring for a campaign.

    Args:
        campaign_id: ID of the campaign to monitor
    """
    try:
        # Schedule content detection every 6 hours
        detect_campaign_content.apply_async(
            args=[campaign_id],
            countdown=6 * 3600  # 6 hours
        )

        logger.info(f"Scheduled content monitoring for campaign {campaign_id}")

        return {"scheduled": True, "campaign_id": campaign_id}

    except Exception as exc:
        logger.error(f"Failed to schedule monitoring for campaign {campaign_id}: {exc}")
        raise


@celery_app.task(bind=True, max_retries=3)
def batch_collect_stats(self, content_post_ids: List[int]):
    """
    Collect statistics for multiple content posts in batch.

    Args:
        content_post_ids: List of content post IDs
    """
    try:
        import asyncio
        return asyncio.run(_batch_collect_stats_async(content_post_ids))
    except Exception as exc:
        logger.error(f"Batch stats collection failed: {exc}")
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown, max_retries=3)


async def _batch_collect_stats_async(content_post_ids: List[int]) -> Dict[str, Any]:
    """
    Async implementation of batch statistics collection.

    Args:
        content_post_ids: List of content post IDs

    Returns:
        Batch collection results
    """
    async with get_session() as db:
        results = {
            "total_posts": len(content_post_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        for post_id in content_post_ids:
            try:
                await _collect_content_stats_async(post_id)
                results["successful"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "post_id": post_id,
                    "error": str(e)
                })
                logger.error(f"Failed to collect stats for post {post_id}: {e}")

        return results


@celery_app.task(bind=True)
def cleanup_old_stats(self, days_to_keep: int = 90):
    """
    Clean up old content statistics to manage database size.

    Args:
        days_to_keep: Number of days of statistics to keep
    """
    try:
        import asyncio
        return asyncio.run(_cleanup_old_stats_async(days_to_keep))
    except Exception as exc:
        logger.error(f"Stats cleanup failed: {exc}")
        raise


async def _cleanup_old_stats_async(days_to_keep: int) -> Dict[str, Any]:
    """
    Async implementation of statistics cleanup.

    Args:
        days_to_keep: Number of days of statistics to keep

    Returns:
        Cleanup results
    """
    async with get_session() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old statistics
        stmt = select(ContentStats).where(ContentStats.collected_at < cutoff_date)
        result = await db.execute(stmt)
        old_stats = result.scalars().all()

        deleted_count = len(old_stats)

        for stat in old_stats:
            await db.delete(stat)

        await db.commit()

        logger.info(f"Cleaned up {deleted_count} old statistics records")

        return {
            "deleted_records": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }


@celery_app.task(bind=True)
def generate_content_alerts(self, campaign_id: int):
    """
    Generate alerts for content that needs attention.

    Args:
        campaign_id: ID of the campaign to check
    """
    try:
        import asyncio
        return asyncio.run(_generate_content_alerts_async(campaign_id))
    except Exception as exc:
        logger.error(f"Alert generation failed for campaign {campaign_id}: {exc}")
        raise


async def _generate_content_alerts_async(campaign_id: int) -> Dict[str, Any]:
    """
    Async implementation of content alert generation.

    Args:
        campaign_id: ID of the campaign to check

    Returns:
        Generated alerts summary
    """
    async with get_session() as db:
        alerts = []

        # Check for posts with low engagement
        stmt = (
            select(ContentPost, ContentStats)
            .join(ContentStats)
            .where(
                and_(
                    ContentPost.campaign_id == campaign_id,
                    ContentStats.engagement_rate < 0.01,  # Less than 1% engagement
                    ContentStats.collected_at > datetime.utcnow() - timedelta(days=3)
                )
            )
        )
        result = await db.execute(stmt)
        low_engagement_posts = result.all()

        for post, stats in low_engagement_posts:
            alerts.append({
                "type": "low_engagement",
                "content_post_id": post.id,
                "message": f"Post {post.id} has low engagement rate: {stats.engagement_rate:.2%}",
                "severity": "warning"
            })

        # Check for posts pending verification for too long
        stmt = select(ContentPost).where(
            and_(
                ContentPost.campaign_id == campaign_id,
                ContentPost.verification_status == "pending",
                ContentPost.detected_at < datetime.utcnow() - timedelta(days=7)
            )
        )
        result = await db.execute(stmt)
        pending_posts = result.scalars().all()

        for post in pending_posts:
            alerts.append({
                "type": "pending_verification",
                "content_post_id": post.id,
                "message": f"Post {post.id} has been pending verification for over 7 days",
                "severity": "info"
            })

        logger.info(f"Generated {len(alerts)} alerts for campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "alert_count": len(alerts),
            "alerts": alerts
        }


# Periodic task configurations
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Set up periodic tasks for content monitoring.
    """
    # Run content monitoring every hour for active campaigns
    sender.add_periodic_task(
        3600.0,  # Every hour
        detect_active_campaigns.s(),
        name='detect_content_for_active_campaigns'
    )

    # Clean up old statistics weekly
    sender.add_periodic_task(
        604800.0,  # Every week
        cleanup_old_stats.s(),
        name='cleanup_old_content_stats'
    )


@celery_app.task
def detect_active_campaigns():
    """
    Detect content for all currently active campaigns.
    """
    try:
        import asyncio
        return asyncio.run(_detect_active_campaigns_async())
    except Exception as e:
        logger.error(f"Active campaign detection failed: {e}")
        raise


async def _detect_active_campaigns_async() -> Dict[str, Any]:
    """
    Async implementation of active campaign detection.

    Returns:
        Detection results for all active campaigns
    """
    async with get_session() as db:
        # Get all active campaigns
        now = datetime.utcnow()
        stmt = select(Campaign).where(
            and_(
                Campaign.start_date <= now,
                Campaign.end_date >= now,
                Campaign.status == "active"
            )
        )
        result = await db.execute(stmt)
        active_campaigns = result.scalars().all()

        results = {
            "active_campaigns": len(active_campaigns),
            "campaign_results": []
        }

        for campaign in active_campaigns:
            try:
                # Schedule content detection for this campaign
                task_result = detect_campaign_content.delay(campaign.id)
                results["campaign_results"].append({
                    "campaign_id": campaign.id,
                    "task_id": task_result.id,
                    "status": "scheduled"
                })
            except Exception as e:
                logger.error(f"Failed to schedule detection for campaign {campaign.id}: {e}")
                results["campaign_results"].append({
                    "campaign_id": campaign.id,
                    "status": "failed",
                    "error": str(e)
                })

        return results