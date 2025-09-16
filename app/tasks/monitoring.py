"""
Monitoring and alerting background tasks for KOL Management System.
Handles health checks, performance monitoring, and automated alerts.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.tasks.celery_app import celery_app
from app.core.database import get_db
from app.services.social_media import social_media_factory, check_communication_health
from app.services.communication import communication_factory
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.content import ContentPost, ContentStats, ContentAlert, VerificationStatus
from app.models.communication import Message, MessageStatus

logger = logging.getLogger(__name__)


@celery_app.task
def monitor_social_media_content() -> Dict[str, Any]:
    """
    Monitor social media platforms for new content from tracked KOLs.

    Returns:
        Dict with monitoring results
    """
    logger.info("Starting social media content monitoring")

    with next(get_db()) as db:
        try:
            # Get active campaigns for monitoring
            active_campaigns = db.query(Campaign).filter(
                Campaign.status == "active",
                Campaign.start_date <= datetime.utcnow(),
                Campaign.end_date >= datetime.utcnow()
            ).all()

            results = {
                "total_campaigns_monitored": len(active_campaigns),
                "total_content_found": 0,
                "verified_content": 0,
                "pending_review": 0,
                "alerts_generated": 0,
                "campaign_results": []
            }

            # Monitor each active campaign
            for campaign in active_campaigns:
                try:
                    # Get campaign KOLs
                    campaign_kols = db.query(KOL).join(KOL.campaigns).filter(
                        Campaign.id == campaign.id
                    ).all()

                    campaign_result = {
                        "campaign_id": campaign.id,
                        "campaign_title": campaign.title,
                        "kols_monitored": len(campaign_kols),
                        "content_found": 0,
                        "new_content": 0
                    }

                    # Monitor each KOL's content
                    for kol in campaign_kols:
                        for platform, account_data in kol.social_media_accounts.items():
                            try:
                                user_id = account_data.get("handle") or account_data.get("id")
                                if not user_id:
                                    continue

                                # Get recent content (last 2 hours)
                                service = social_media_factory.get_service(platform)
                                async with service:
                                    recent_content = await service.get_user_media(
                                        user_id=user_id,
                                        access_token=account_data.get("access_token"),
                                        limit=10
                                    )

                                # Process each content item
                                for content_item in recent_content.get("data", []):
                                    platform_post_id = content_item.get("platform_post_id")
                                    if not platform_post_id:
                                        continue

                                    # Check if content is new (within last 2 hours)
                                    posted_at = datetime.fromisoformat(
                                        content_item["posted_at"].replace("Z", "+00:00")
                                    ) if content_item.get("posted_at") else None

                                    if not posted_at or posted_at < datetime.utcnow() - timedelta(hours=2):
                                        continue

                                    # Check if already exists
                                    existing = db.query(ContentPost).filter(
                                        ContentPost.platform_post_id == platform_post_id,
                                        ContentPost.platform == platform
                                    ).first()

                                    if existing:
                                        continue

                                    # Verify if content matches campaign
                                    is_match, confidence, match_criteria = await service.verify_content_match(
                                        content_item,
                                        {
                                            "required_hashtags": campaign.hashtags or [],
                                            "keywords": campaign.keywords or [],
                                            "start_date": campaign.start_date,
                                            "end_date": campaign.end_date
                                        }
                                    )

                                    if is_match and confidence > 0.3:  # Lower threshold for monitoring
                                        # Create content record
                                        content_post = ContentPost(
                                            kol_id=kol.id,
                                            campaign_id=campaign.id,
                                            platform=platform,
                                            platform_post_id=platform_post_id,
                                            url=content_item.get("permalink", ""),
                                            content=content_item.get("content", ""),
                                            hashtags=content_item.get("hashtags", []),
                                            mentions=content_item.get("mentions", []),
                                            posted_at=posted_at,
                                            detected_at=datetime.utcnow(),
                                            verification_status=VerificationStatus.AUTO_VERIFIED if confidence > 0.8 else VerificationStatus.PENDING,
                                            confidence_score=confidence,
                                            match_criteria=match_criteria
                                        )

                                        db.add(content_post)
                                        db.flush()  # Get content ID

                                        campaign_result["new_content"] += 1
                                        results["total_content_found"] += 1

                                        if confidence > 0.8:
                                            results["verified_content"] += 1
                                        else:
                                            results["pending_review"] += 1

                                        # Generate alerts for high-engagement content
                                        if content_item.get("like_count", 0) > 1000:
                                            alert = ContentAlert(
                                                content_post_id=content_post.id,
                                                campaign_id=campaign.id,
                                                alert_type="high_engagement",
                                                severity="medium",
                                                title=f"High engagement detected: {content_item.get('like_count', 0)} likes",
                                                description=f"Content from {kol.name} has received significant engagement",
                                                trigger_conditions={"min_likes": 1000},
                                                actual_values={"likes": content_item.get("like_count", 0)}
                                            )
                                            db.add(alert)
                                            results["alerts_generated"] += 1

                            except Exception as e:
                                logger.error(f"Failed to monitor {platform} for KOL {kol.id}: {str(e)}")

                    results["campaign_results"].append(campaign_result)

                except Exception as e:
                    logger.error(f"Failed to monitor campaign {campaign.id}: {str(e)}")

            db.commit()

            logger.info(f"Content monitoring completed: {results['total_content_found']} new content, {results['alerts_generated']} alerts")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Content monitoring task failed: {str(e)}")
            raise


@celery_app.task
def health_check() -> Dict[str, Any]:
    """
    Perform comprehensive health check of all services.

    Returns:
        Dict with health status
    """
    logger.info("Performing system health check")

    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_healthy": True,
        "services": {},
        "database": {},
        "celery": {},
        "alerts": []
    }

    try:
        # Check database health
        with next(get_db()) as db:
            try:
                # Test database connectivity
                db.execute("SELECT 1")

                # Check table counts
                kol_count = db.query(func.count(KOL.id)).scalar()
                campaign_count = db.query(func.count(Campaign.id)).scalar()
                content_count = db.query(func.count(ContentPost.id)).scalar()

                health_status["database"] = {
                    "healthy": True,
                    "kol_count": kol_count,
                    "campaign_count": campaign_count,
                    "content_count": content_count
                }

            except Exception as e:
                health_status["database"] = {
                    "healthy": False,
                    "error": str(e)
                }
                health_status["overall_healthy"] = False

        # Check social media services
        try:
            import asyncio

            async def check_social_services():
                platforms = ["instagram", "youtube", "tiktok", "twitter", "facebook"]
                social_health = {}

                for platform in platforms:
                    try:
                        service = social_media_factory.get_service(platform)
                        async with service:
                            service_health = await service.check_service_health()
                            social_health[platform] = service_health
                    except Exception as e:
                        social_health[platform] = {
                            "healthy": False,
                            "error": str(e)
                        }
                        health_status["overall_healthy"] = False

                return social_health

            health_status["services"]["social_media"] = asyncio.run(check_social_services())

        except Exception as e:
            health_status["services"]["social_media"] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["overall_healthy"] = False

        # Check communication services
        try:
            import asyncio
            comm_health = asyncio.run(communication_factory.check_all_services_health())
            health_status["services"]["communication"] = comm_health

            # Check if any communication service is unhealthy
            for service_name, service_health in comm_health.items():
                if not service_health.get("healthy", False):
                    health_status["overall_healthy"] = False

        except Exception as e:
            health_status["services"]["communication"] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["overall_healthy"] = False

        # Check Celery worker health
        try:
            from app.tasks.celery_app import get_celery_health
            celery_health = get_celery_health()
            health_status["celery"] = celery_health

            if not celery_health.get("healthy", False):
                health_status["overall_healthy"] = False

        except Exception as e:
            health_status["celery"] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["overall_healthy"] = False

        # Generate alerts for unhealthy services
        if not health_status["overall_healthy"]:
            health_status["alerts"].append({
                "type": "system_health",
                "severity": "high",
                "message": "One or more services are unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            })

        logger.info(f"Health check completed: {'HEALTHY' if health_status['overall_healthy'] else 'UNHEALTHY'}")
        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_healthy": False,
            "error": str(e)
        }


@celery_app.task
def monitor_performance_alerts() -> Dict[str, Any]:
    """
    Monitor content performance and generate alerts for underperforming or viral content.

    Returns:
        Dict with monitoring results
    """
    logger.info("Monitoring content performance for alerts")

    with next(get_db()) as db:
        try:
            # Get recent content (last 24 hours) with performance data
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

            recent_content = db.query(ContentPost).filter(
                ContentPost.posted_at >= twenty_four_hours_ago,
                ContentPost.verification_status == VerificationStatus.VERIFIED
            ).all()

            results = {
                "total_content_analyzed": len(recent_content),
                "underperforming_alerts": 0,
                "viral_alerts": 0,
                "compliance_alerts": 0,
                "alerts_generated": []
            }

            for content in recent_content:
                try:
                    # Get latest performance stats
                    latest_stats = content.get_latest_stats()
                    if not latest_stats:
                        continue

                    # Calculate engagement rate
                    engagement_rate = content.calculate_engagement_rate(latest_stats)

                    # Get KOL's average engagement rate for comparison
                    kol_avg_engagement = 0
                    if content.kol and content.kol.engagement_rates:
                        kol_avg_engagement = content.kol.engagement_rates.get(content.platform, 0)

                    # Check for underperforming content
                    if kol_avg_engagement > 0 and engagement_rate < (kol_avg_engagement * 0.5):
                        alert = ContentAlert(
                            content_post_id=content.id,
                            campaign_id=content.campaign_id,
                            alert_type="underperforming",
                            severity="medium",
                            title=f"Underperforming content detected",
                            description=f"Content engagement rate ({engagement_rate:.2f}%) is significantly below KOL average ({kol_avg_engagement:.2f}%)",
                            trigger_conditions={"min_engagement_rate": kol_avg_engagement * 0.5},
                            threshold_values={"kol_average": kol_avg_engagement},
                            actual_values={"engagement_rate": engagement_rate}
                        )

                        db.add(alert)
                        results["underperforming_alerts"] += 1
                        results["alerts_generated"].append({
                            "type": "underperforming",
                            "content_id": content.id,
                            "kol_name": content.kol.name if content.kol else "Unknown",
                            "engagement_rate": engagement_rate
                        })

                    # Check for viral content
                    elif engagement_rate > (kol_avg_engagement * 3) and engagement_rate > 10:
                        alert = ContentAlert(
                            content_post_id=content.id,
                            campaign_id=content.campaign_id,
                            alert_type="viral",
                            severity="high",
                            title=f"Viral content detected",
                            description=f"Content has gone viral with {engagement_rate:.2f}% engagement rate",
                            trigger_conditions={"min_viral_rate": kol_avg_engagement * 3},
                            threshold_values={"viral_threshold": kol_avg_engagement * 3},
                            actual_values={"engagement_rate": engagement_rate}
                        )

                        db.add(alert)
                        results["viral_alerts"] += 1
                        results["alerts_generated"].append({
                            "type": "viral",
                            "content_id": content.id,
                            "kol_name": content.kol.name if content.kol else "Unknown",
                            "engagement_rate": engagement_rate
                        })

                    # Check for compliance issues
                    if not content.compliant_with_guidelines or content.compliance_issues:
                        alert = ContentAlert(
                            content_post_id=content.id,
                            campaign_id=content.campaign_id,
                            alert_type="compliance_issue",
                            severity="critical",
                            title=f"Compliance issue detected",
                            description=f"Content has compliance issues: {', '.join(content.compliance_issues)}",
                            trigger_conditions={"compliance_check": True},
                            actual_values={"compliance_issues": content.compliance_issues}
                        )

                        db.add(alert)
                        results["compliance_alerts"] += 1
                        results["alerts_generated"].append({
                            "type": "compliance",
                            "content_id": content.id,
                            "kol_name": content.kol.name if content.kol else "Unknown",
                            "issues": content.compliance_issues
                        })

                except Exception as e:
                    logger.error(f"Failed to analyze content {content.id}: {str(e)}")

            db.commit()

            logger.info(f"Performance monitoring completed: {len(results['alerts_generated'])} alerts generated")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Performance monitoring task failed: {str(e)}")
            raise


@celery_app.task
def monitor_communication_delivery() -> Dict[str, Any]:
    """
    Monitor communication delivery and generate alerts for failed messages.

    Returns:
        Dict with monitoring results
    """
    logger.info("Monitoring communication delivery")

    with next(get_db()) as db:
        try:
            # Get messages from last hour that might have delivery issues
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            # Check for stuck messages (queued for more than 1 hour)
            stuck_messages = db.query(Message).filter(
                Message.status == MessageStatus.QUEUED,
                Message.created_at <= one_hour_ago
            ).all()

            # Check for messages that failed after retries
            failed_messages = db.query(Message).filter(
                Message.status == MessageStatus.FAILED,
                Message.updated_at >= one_hour_ago,
                Message.retry_count >= Message.max_retries
            ).all()

            results = {
                "stuck_messages": len(stuck_messages),
                "failed_messages": len(failed_messages),
                "total_issues": len(stuck_messages) + len(failed_messages),
                "alerts_generated": 0,
                "message_issues": []
            }

            # Handle stuck messages
            for message in stuck_messages:
                # Retry stuck messages
                message.status = MessageStatus.QUEUED
                message.scheduled_for = datetime.utcnow()
                message.retry_count += 1

                results["message_issues"].append({
                    "type": "stuck",
                    "message_id": message.id,
                    "recipient": message.recipient,
                    "channel": message.channel,
                    "stuck_duration_hours": (datetime.utcnow() - message.created_at).total_seconds() / 3600
                })

            # Handle failed messages
            for message in failed_messages:
                results["message_issues"].append({
                    "type": "failed",
                    "message_id": message.id,
                    "recipient": message.recipient,
                    "channel": message.channel,
                    "error": message.error_message,
                    "retry_count": message.retry_count
                })

            # Generate system alert if too many issues
            if results["total_issues"] > 10:
                results["alerts_generated"] += 1
                logger.warning(f"High number of communication issues detected: {results['total_issues']}")

            db.commit()

            logger.info(f"Communication monitoring completed: {results['total_issues']} issues found")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Communication monitoring task failed: {str(e)}")
            raise


@celery_app.task
def cleanup_old_data() -> Dict[str, Any]:
    """
    Clean up old data to maintain system performance.

    Returns:
        Dict with cleanup results
    """
    logger.info("Starting data cleanup")

    with next(get_db()) as db:
        try:
            results = {
                "old_content_stats_deleted": 0,
                "old_messages_archived": 0,
                "old_alerts_cleaned": 0,
                "old_task_results_cleaned": 0
            }

            # Clean up old content stats (keep only last 90 days)
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            old_stats = db.query(ContentStats).filter(
                ContentStats.collected_at < ninety_days_ago
            ).delete()
            results["old_content_stats_deleted"] = old_stats

            # Archive old messages (older than 1 year)
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            old_messages = db.query(Message).filter(
                Message.created_at < one_year_ago,
                Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.FAILED])
            ).count()

            # Instead of deleting, we could archive to a separate table
            # For now, just count them
            results["old_messages_archived"] = old_messages

            # Clean up resolved alerts (older than 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            old_alerts = db.query(ContentAlert).filter(
                ContentAlert.status.in_(["resolved", "dismissed"]),
                ContentAlert.resolved_at < thirty_days_ago
            ).delete()
            results["old_alerts_cleaned"] = old_alerts

            db.commit()

            logger.info(f"Data cleanup completed: {sum(results.values())} items processed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Data cleanup task failed: {str(e)}")
            raise


@celery_app.task
def generate_system_metrics() -> Dict[str, Any]:
    """
    Generate system-wide metrics for monitoring.

    Returns:
        Dict with system metrics
    """
    logger.info("Generating system metrics")

    with next(get_db()) as db:
        try:
            # Calculate various system metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "kol_metrics": {},
                "campaign_metrics": {},
                "content_metrics": {},
                "communication_metrics": {}
            }

            # KOL metrics
            total_kols = db.query(func.count(KOL.id)).scalar()
            active_kols = db.query(func.count(KOL.id)).filter(KOL.status == "active").scalar()

            metrics["kol_metrics"] = {
                "total_kols": total_kols,
                "active_kols": active_kols,
                "inactive_kols": total_kols - active_kols
            }

            # Campaign metrics
            total_campaigns = db.query(func.count(Campaign.id)).scalar()
            active_campaigns = db.query(func.count(Campaign.id)).filter(
                Campaign.status == "active",
                Campaign.start_date <= datetime.utcnow(),
                Campaign.end_date >= datetime.utcnow()
            ).scalar()

            metrics["campaign_metrics"] = {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "completed_campaigns": db.query(func.count(Campaign.id)).filter(Campaign.status == "completed").scalar()
            }

            # Content metrics (last 24 hours)
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

            new_content_24h = db.query(func.count(ContentPost.id)).filter(
                ContentPost.detected_at >= twenty_four_hours_ago
            ).scalar()

            verified_content_24h = db.query(func.count(ContentPost.id)).filter(
                ContentPost.detected_at >= twenty_four_hours_ago,
                ContentPost.verification_status == VerificationStatus.VERIFIED
            ).scalar()

            metrics["content_metrics"] = {
                "new_content_24h": new_content_24h,
                "verified_content_24h": verified_content_24h,
                "pending_verification": db.query(func.count(ContentPost.id)).filter(
                    ContentPost.verification_status == VerificationStatus.PENDING
                ).scalar()
            }

            # Communication metrics (last 24 hours)
            sent_messages_24h = db.query(func.count(Message.id)).filter(
                Message.sent_at >= twenty_four_hours_ago,
                Message.status == MessageStatus.SENT
            ).scalar()

            failed_messages_24h = db.query(func.count(Message.id)).filter(
                Message.updated_at >= twenty_four_hours_ago,
                Message.status == MessageStatus.FAILED
            ).scalar()

            metrics["communication_metrics"] = {
                "sent_messages_24h": sent_messages_24h,
                "failed_messages_24h": failed_messages_24h,
                "pending_messages": db.query(func.count(Message.id)).filter(
                    Message.status == MessageStatus.QUEUED
                ).scalar()
            }

            logger.info("System metrics generated successfully")
            return metrics

        except Exception as e:
            logger.error(f"Failed to generate system metrics: {str(e)}")
            raise