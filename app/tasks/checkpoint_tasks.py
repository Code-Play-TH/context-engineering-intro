"""
Celery tasks for content checkpoint processing.

This module contains background tasks for processing content checkpoints
(D+1, D+3, D+7) and generating automated reports.
"""

from typing import Any, Dict, List
from celery import shared_task
import logging

from app.services.content_tracking_service import (
    ContentTrackingService,
    CheckpointType
)
from app.services.communication_service import CommunicationService
from app.utils.datetime_utils import get_current_utc

logger = logging.getLogger(__name__)


@shared_task
def process_d_plus_1_checkpoints() -> Dict[str, Any]:
    """
    Process D+1 checkpoints for recently published content.

    Returns:
        Dict[str, Any]: Processing results.
    """
    logger.info("Starting D+1 checkpoint processing")

    from app.core.database import get_db_session
    db = next(get_db_session())

    tracking_service = ContentTrackingService(db)

    # Get content ready for D+1 checkpoint
    content_list = tracking_service.get_checkpoint_content(
        checkpoint_type=CheckpointType.D_PLUS_1,
        tolerance_hours=2
    )

    results = {
        "checkpoint": CheckpointType.D_PLUS_1,
        "total_content": len(content_list),
        "processed": 0,
        "failed": 0,
        "analyses": []
    }

    for content in content_list:
        try:
            # Analyze checkpoint
            analysis = tracking_service.analyze_checkpoint(
                content_id=content.id,
                checkpoint_type=CheckpointType.D_PLUS_1
            )

            results["analyses"].append(analysis)
            results["processed"] += 1

            # Send notification if underperforming
            if analysis.get("performance_rating") in ["poor", "average"]:
                _send_underperformance_alert(content.id, analysis)

            logger.info(f"D+1 checkpoint processed for content {content.id}")

        except Exception as e:
            logger.error(f"Failed to process D+1 checkpoint for content {content.id}: {e}")
            results["failed"] += 1

    logger.info(f"D+1 checkpoint processing completed: {results['processed']} processed")

    return results


@shared_task
def process_d_plus_3_checkpoints() -> Dict[str, Any]:
    """
    Process D+3 checkpoints for content.

    Returns:
        Dict[str, Any]: Processing results.
    """
    logger.info("Starting D+3 checkpoint processing")

    from app.core.database import get_db_session
    db = next(get_db_session())

    tracking_service = ContentTrackingService(db)

    content_list = tracking_service.get_checkpoint_content(
        checkpoint_type=CheckpointType.D_PLUS_3,
        tolerance_hours=4
    )

    results = {
        "checkpoint": CheckpointType.D_PLUS_3,
        "total_content": len(content_list),
        "processed": 0,
        "failed": 0,
        "analyses": []
    }

    for content in content_list:
        try:
            analysis = tracking_service.analyze_checkpoint(
                content_id=content.id,
                checkpoint_type=CheckpointType.D_PLUS_3
            )

            results["analyses"].append(analysis)
            results["processed"] += 1

            # Generate checkpoint report
            _generate_checkpoint_report(content.id, analysis)

            logger.info(f"D+3 checkpoint processed for content {content.id}")

        except Exception as e:
            logger.error(f"Failed to process D+3 checkpoint for content {content.id}: {e}")
            results["failed"] += 1

    logger.info(f"D+3 checkpoint processing completed: {results['processed']} processed")

    return results


@shared_task
def process_d_plus_7_checkpoints() -> Dict[str, Any]:
    """
    Process D+7 checkpoints for content.

    Returns:
        Dict[str, Any]: Processing results.
    """
    logger.info("Starting D+7 checkpoint processing")

    from app.core.database import get_db_session
    db = next(get_db_session())

    tracking_service = ContentTrackingService(db)

    content_list = tracking_service.get_checkpoint_content(
        checkpoint_type=CheckpointType.D_PLUS_7,
        tolerance_hours=6
    )

    results = {
        "checkpoint": CheckpointType.D_PLUS_7,
        "total_content": len(content_list),
        "processed": 0,
        "failed": 0,
        "analyses": []
    }

    for content in content_list:
        try:
            # Get full performance trend
            trend = tracking_service.get_content_performance_trend(content.id)

            results["analyses"].append(trend)
            results["processed"] += 1

            # Generate comprehensive report
            _generate_final_content_report(content.id, trend)

            logger.info(f"D+7 checkpoint processed for content {content.id}")

        except Exception as e:
            logger.error(f"Failed to process D+7 checkpoint for content {content.id}: {e}")
            results["failed"] += 1

    logger.info(f"D+7 checkpoint processing completed: {results['processed']} processed")

    return results


@shared_task
def analyze_content_checkpoint(content_id: int, checkpoint_type: str) -> Dict[str, Any]:
    """
    Analyze specific content checkpoint.

    Args:
        content_id (int): Content ID.
        checkpoint_type (str): Checkpoint type.

    Returns:
        Dict[str, Any]: Analysis results.
    """
    logger.info(f"Analyzing {checkpoint_type} checkpoint for content {content_id}")

    from app.core.database import get_db_session
    db = next(get_db_session())

    tracking_service = ContentTrackingService(db)

    analysis = tracking_service.analyze_checkpoint(content_id, checkpoint_type)

    logger.info(f"Checkpoint analysis completed for content {content_id}")

    return analysis


# Helper functions

def _send_underperformance_alert(content_id: int, analysis: Dict[str, Any]) -> None:
    """Send alert for underperforming content."""
    from app.core.database import get_db_session
    from app.models.campaign_content import CampaignContent
    from app.services.communication_service import NotificationChannel

    db = next(get_db_session())
    comm_service = CommunicationService(db)

    content = db.query(CampaignContent).filter(
        CampaignContent.id == content_id
    ).first()

    if content:
        # Send notification to campaign manager
        comm_service.send_notification(
            recipient_id=1,  # Would be campaign creator/manager
            title=f"Content Underperforming: {content.content_type}",
            message=f"Content {content_id} is showing {analysis['performance_rating']} performance at D+1 checkpoint. Engagement rate: {analysis['metrics']['engagement_rate']}%",
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            metadata={"content_id": content_id, "checkpoint": "d+1"}
        )

        logger.info(f"Underperformance alert sent for content {content_id}")


def _generate_checkpoint_report(content_id: int, analysis: Dict[str, Any]) -> None:
    """Generate checkpoint report."""
    logger.info(f"Generating checkpoint report for content {content_id}")

    # In production, this would generate a PDF/email report
    # For now, just log the analysis

    logger.info(f"Checkpoint report: {analysis}")


def _generate_final_content_report(content_id: int, trend: Dict[str, Any]) -> None:
    """Generate final comprehensive content report."""
    logger.info(f"Generating final content report for {content_id}")

    from app.core.database import get_db_session
    from app.models.campaign_content import CampaignContent

    db = next(get_db_session())
    comm_service = CommunicationService(db)

    content = db.query(CampaignContent).filter(
        CampaignContent.id == content_id
    ).first()

    if content:
        # Send comprehensive report
        report_summary = f"""
        Content Performance Report (D+7)

        Content ID: {content_id}
        Published: {trend['published_at']}
        Days Live: {trend['days_since_publish']}

        Trend: {trend['trend_summary']['trend']}
        Initial Engagement: {trend['trend_summary'].get('initial_engagement', 'N/A')}%
        Current Engagement: {trend['trend_summary'].get('current_engagement', 'N/A')}%

        Total Checkpoints: {len(trend['checkpoints'])}
        """

        comm_service.send_notification(
            recipient_id=1,  # Campaign manager
            title=f"D+7 Content Report: {content.content_type}",
            message=report_summary,
            channels=[NotificationChannel.EMAIL],
            metadata={"content_id": content_id, "report_type": "d+7_final"}
        )

        logger.info(f"Final report sent for content {content_id}")
