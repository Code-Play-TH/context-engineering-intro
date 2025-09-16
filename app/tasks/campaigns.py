"""
Campaign automation and management background tasks.
Handles campaign workflow automation, content scheduling, and performance tracking.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.tasks.celery_app import celery_app
from app.core.database import get_session
from app.services.social_media.factory import social_media_factory
from app.services.communication.factory import communication_factory
from app.models.campaigns import Campaign, CampaignBrief, CampaignContent
from app.models.kols import KOL
from app.models.collaboration import Collaboration

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def process_campaign_automations(self) -> Dict[str, Any]:
    """
    Process all active campaign automations and trigger appropriate actions.

    Returns:
        Dict with processing results and statistics
    """
    results = {
        "processed_campaigns": 0,
        "triggered_actions": 0,
        "errors": [],
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        with get_session() as db:
            # Get campaigns with pending automations
            active_campaigns = db.query(Campaign).filter(
                Campaign.status == "active",
                Campaign.start_date <= datetime.utcnow(),
                Campaign.end_date >= datetime.utcnow()
            ).all()

            for campaign in active_campaigns:
                try:
                    # Check for content deadline reminders
                    content_reminders = _check_content_deadlines(db, campaign)
                    results["triggered_actions"] += content_reminders

                    # Check for campaign milestone notifications
                    milestone_notifications = _check_campaign_milestones(db, campaign)
                    results["triggered_actions"] += milestone_notifications

                    # Check for performance alerts
                    performance_alerts = _check_performance_thresholds(db, campaign)
                    results["triggered_actions"] += performance_alerts

                    # Check for approval workflows
                    approval_workflows = _process_approval_workflows(db, campaign)
                    results["triggered_actions"] += approval_workflows

                    results["processed_campaigns"] += 1

                except Exception as e:
                    error_msg = f"Error processing campaign {campaign.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            logger.info(f"Campaign automation processing completed: {results}")
            return results

    except Exception as e:
        logger.error(f"Campaign automation processing failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def schedule_campaign_content(self, campaign_id: int, content_schedule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule content publishing for a campaign across multiple platforms.

    Args:
        campaign_id: Campaign identifier
        content_schedule: Schedule configuration with timing and content

    Returns:
        Dict with scheduling results
    """
    results = {
        "campaign_id": campaign_id,
        "scheduled_posts": 0,
        "failed_posts": 0,
        "errors": [],
        "scheduled_ids": []
    }

    try:
        with get_session() as db:
            campaign = db.query(Campaign).filter_by(id=campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Get campaign content and KOL collaborations
            collaborations = db.query(Collaboration).filter_by(
                campaign_id=campaign_id,
                status="approved"
            ).all()

            for collaboration in collaborations:
                kol = collaboration.kol
                content_items = content_schedule.get(str(collaboration.id), [])

                for content_item in content_items:
                    try:
                        # Schedule content publication
                        schedule_result = asyncio.run(_schedule_content_publication(
                            kol, content_item, campaign
                        ))

                        if schedule_result["success"]:
                            results["scheduled_posts"] += 1
                            results["scheduled_ids"].append(schedule_result["schedule_id"])
                        else:
                            results["failed_posts"] += 1
                            results["errors"].append(schedule_result["error"])

                    except Exception as e:
                        error_msg = f"Failed to schedule content for KOL {kol.id}: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
                        results["failed_posts"] += 1

            logger.info(f"Content scheduling completed for campaign {campaign_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Content scheduling failed for campaign {campaign_id}: {str(e)}")
        raise self.retry(countdown=180, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def generate_campaign_brief(self, campaign_id: int, brief_template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized campaign briefs for KOLs based on template and data.

    Args:
        campaign_id: Campaign identifier
        brief_template: Template structure and customization rules

    Returns:
        Dict with brief generation results
    """
    results = {
        "campaign_id": campaign_id,
        "generated_briefs": 0,
        "sent_briefs": 0,
        "errors": [],
        "brief_ids": []
    }

    try:
        with get_session() as db:
            campaign = db.query(Campaign).filter_by(id=campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Get approved collaborations for the campaign
            collaborations = db.query(Collaboration).filter_by(
                campaign_id=campaign_id,
                status="approved"
            ).all()

            for collaboration in collaborations:
                try:
                    # Generate personalized brief
                    brief_data = _generate_personalized_brief(
                        collaboration, campaign, brief_template
                    )

                    # Create brief record
                    brief = CampaignBrief(
                        campaign_id=campaign_id,
                        kol_id=collaboration.kol_id,
                        collaboration_id=collaboration.id,
                        content=brief_data["content"],
                        requirements=brief_data["requirements"],
                        deliverables=brief_data["deliverables"],
                        timeline=brief_data["timeline"],
                        compensation=brief_data["compensation"],
                        status="draft"
                    )

                    db.add(brief)
                    db.commit()

                    results["generated_briefs"] += 1
                    results["brief_ids"].append(brief.id)

                    # Send brief to KOL if auto-send is enabled
                    if brief_template.get("auto_send", False):
                        send_result = asyncio.run(_send_campaign_brief(
                            collaboration.kol, brief, campaign
                        ))

                        if send_result["success"]:
                            brief.status = "sent"
                            brief.sent_at = datetime.utcnow()
                            db.commit()
                            results["sent_briefs"] += 1
                        else:
                            results["errors"].append(send_result["error"])

                except Exception as e:
                    error_msg = f"Failed to generate brief for collaboration {collaboration.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            logger.info(f"Brief generation completed for campaign {campaign_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Brief generation failed for campaign {campaign_id}: {str(e)}")
        raise self.retry(countdown=120, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def monitor_campaign_performance(self, campaign_id: int) -> Dict[str, Any]:
    """
    Monitor campaign performance metrics and trigger alerts if needed.

    Args:
        campaign_id: Campaign identifier

    Returns:
        Dict with performance monitoring results
    """
    results = {
        "campaign_id": campaign_id,
        "monitored_content": 0,
        "performance_alerts": 0,
        "optimization_suggestions": [],
        "errors": []
    }

    try:
        with get_session() as db:
            campaign = db.query(Campaign).filter_by(id=campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Get campaign content that should be monitored
            content_items = db.query(CampaignContent).filter_by(
                campaign_id=campaign_id,
                status="published"
            ).all()

            total_engagement = 0
            total_reach = 0
            underperforming_content = []

            for content in content_items:
                try:
                    # Collect latest performance metrics
                    performance_data = asyncio.run(_collect_content_performance(content))

                    if performance_data:
                        # Update content metrics
                        content.engagement_rate = performance_data.get("engagement_rate", 0)
                        content.reach = performance_data.get("reach", 0)
                        content.impressions = performance_data.get("impressions", 0)
                        content.last_updated = datetime.utcnow()

                        total_engagement += content.engagement_rate
                        total_reach += content.reach

                        # Check performance thresholds
                        if _is_content_underperforming(content, campaign):
                            underperforming_content.append({
                                "content_id": content.id,
                                "kol_id": content.kol_id,
                                "platform": content.platform,
                                "engagement_rate": content.engagement_rate,
                                "expected_rate": campaign.target_engagement_rate
                            })

                        results["monitored_content"] += 1

                except Exception as e:
                    error_msg = f"Failed to monitor content {content.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Generate optimization suggestions
            if underperforming_content:
                results["optimization_suggestions"] = _generate_optimization_suggestions(
                    underperforming_content, campaign
                )

                # Send performance alerts
                alert_result = asyncio.run(_send_performance_alerts(
                    campaign, underperforming_content
                ))
                results["performance_alerts"] = alert_result.get("alerts_sent", 0)

            # Update campaign performance summary
            if results["monitored_content"] > 0:
                campaign.avg_engagement_rate = total_engagement / results["monitored_content"]
                campaign.total_reach = total_reach
                campaign.last_performance_check = datetime.utcnow()

            db.commit()

            logger.info(f"Performance monitoring completed for campaign {campaign_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Performance monitoring failed for campaign {campaign_id}: {str(e)}")
        raise self.retry(countdown=240, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def process_campaign_payments(self, campaign_id: int) -> Dict[str, Any]:
    """
    Process campaign payments and milestone-based compensation.

    Args:
        campaign_id: Campaign identifier

    Returns:
        Dict with payment processing results
    """
    results = {
        "campaign_id": campaign_id,
        "processed_payments": 0,
        "total_amount": 0.0,
        "errors": [],
        "payment_ids": []
    }

    try:
        with get_session() as db:
            campaign = db.query(Campaign).filter_by(id=campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Get collaborations eligible for payment
            eligible_collaborations = db.query(Collaboration).filter(
                Collaboration.campaign_id == campaign_id,
                Collaboration.status == "completed",
                Collaboration.payment_status.in_(["pending", "milestone_due"])
            ).all()

            for collaboration in eligible_collaborations:
                try:
                    # Calculate payment amount based on milestones
                    payment_amount = _calculate_milestone_payment(collaboration, campaign)

                    if payment_amount > 0:
                        # Process payment
                        payment_result = asyncio.run(_process_kol_payment(
                            collaboration, payment_amount, campaign
                        ))

                        if payment_result["success"]:
                            collaboration.payment_status = "paid"
                            collaboration.payment_date = datetime.utcnow()
                            collaboration.payment_amount = payment_amount

                            results["processed_payments"] += 1
                            results["total_amount"] += payment_amount
                            results["payment_ids"].append(payment_result["payment_id"])
                        else:
                            results["errors"].append(payment_result["error"])

                except Exception as e:
                    error_msg = f"Failed to process payment for collaboration {collaboration.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            db.commit()

            logger.info(f"Payment processing completed for campaign {campaign_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Payment processing failed for campaign {campaign_id}: {str(e)}")
        raise self.retry(countdown=300, exc=e)


# Helper functions
def _check_content_deadlines(db: Session, campaign: Campaign) -> int:
    """Check for content deadlines and send reminders."""
    tomorrow = datetime.utcnow() + timedelta(days=1)

    upcoming_deadlines = db.query(CampaignContent).filter(
        CampaignContent.campaign_id == campaign.id,
        CampaignContent.deadline <= tomorrow,
        CampaignContent.status == "pending"
    ).all()

    reminders_sent = 0
    for content in upcoming_deadlines:
        # Send reminder logic would go here
        reminders_sent += 1

    return reminders_sent


def _check_campaign_milestones(db: Session, campaign: Campaign) -> int:
    """Check for campaign milestone notifications."""
    # Implementation for milestone checking
    return 0


def _check_performance_thresholds(db: Session, campaign: Campaign) -> int:
    """Check for performance threshold alerts."""
    # Implementation for performance threshold checking
    return 0


def _process_approval_workflows(db: Session, campaign: Campaign) -> int:
    """Process pending approval workflows."""
    # Implementation for approval workflow processing
    return 0


async def _schedule_content_publication(kol: KOL, content_item: Dict, campaign: Campaign) -> Dict[str, Any]:
    """Schedule content for future publication."""
    # Implementation for content scheduling
    return {"success": True, "schedule_id": "sched_123"}


def _generate_personalized_brief(collaboration, campaign: Campaign, template: Dict) -> Dict[str, Any]:
    """Generate personalized campaign brief."""
    return {
        "content": f"Personalized brief for {collaboration.kol.name}",
        "requirements": template.get("requirements", []),
        "deliverables": template.get("deliverables", []),
        "timeline": template.get("timeline", {}),
        "compensation": collaboration.compensation_amount
    }


async def _send_campaign_brief(kol: KOL, brief, campaign: Campaign) -> Dict[str, Any]:
    """Send campaign brief to KOL."""
    # Implementation for sending brief
    return {"success": True}


async def _collect_content_performance(content) -> Dict[str, Any]:
    """Collect performance metrics for content."""
    # Implementation for performance collection
    return {"engagement_rate": 3.5, "reach": 10000, "impressions": 50000}


def _is_content_underperforming(content, campaign: Campaign) -> bool:
    """Check if content is underperforming."""
    return content.engagement_rate < campaign.target_engagement_rate * 0.7


def _generate_optimization_suggestions(underperforming_content: List, campaign: Campaign) -> List[str]:
    """Generate optimization suggestions."""
    return ["Consider adjusting posting times", "Review content strategy"]


async def _send_performance_alerts(campaign: Campaign, underperforming_content: List) -> Dict[str, Any]:
    """Send performance alert notifications."""
    return {"alerts_sent": len(underperforming_content)}


def _calculate_milestone_payment(collaboration, campaign: Campaign) -> float:
    """Calculate milestone-based payment amount."""
    return collaboration.compensation_amount


async def _process_kol_payment(collaboration, amount: float, campaign: Campaign) -> Dict[str, Any]:
    """Process payment to KOL."""
    # Implementation for payment processing
    return {"success": True, "payment_id": "pay_123"}