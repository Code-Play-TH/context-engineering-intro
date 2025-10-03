"""
Alert service for monitoring and notifications.

This module handles alert rules, threshold monitoring,
and automated notifications for critical events.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.campaign import Campaign, CampaignStatus
from app.models.collaboration import Collaboration, CollaborationStatus
from app.models.campaign_content import CampaignContent, ContentStatus
from app.services.communication_service import CommunicationService, NotificationChannel
from app.utils.datetime_utils import get_current_utc
import logging

logger = logging.getLogger(__name__)


class AlertType:
    """Alert type constants."""
    BUDGET_THRESHOLD = "budget_threshold"
    DEADLINE_APPROACHING = "deadline_approaching"
    CONTENT_UNDERPERFORMING = "content_underperforming"
    COLLABORATION_PENDING = "collaboration_pending"
    CAMPAIGN_DELAYED = "campaign_delayed"
    SYSTEM_ERROR = "system_error"


class AlertSeverity:
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertService:
    """
    Service for alert monitoring and notifications.

    Handles:
    - Threshold monitoring
    - Automated alert generation
    - Alert distribution
    - Alert history tracking
    """

    def __init__(self, db: Session):
        """
        Initialize alert service.

        Args:
            db (Session): Database session.
        """
        self.db = db
        self.comm_service = CommunicationService(db)

    def check_budget_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for budget threshold alerts.

        Returns:
            List[Dict[str, Any]]: List of budget alerts.
        """
        alerts = []

        # Get all active campaigns
        campaigns = self.db.query(Campaign).filter(
            Campaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.PENDING_APPROVAL])
        ).all()

        for campaign in campaigns:
            # Calculate budget utilization
            allocated = self.db.query(func.sum(Collaboration.compensation)).filter(
                Collaboration.campaign_id == campaign.id
            ).scalar() or 0

            utilization = (allocated / campaign.budget * 100) if campaign.budget > 0 else 0

            # Alert thresholds
            if utilization >= 95:
                alerts.append(self._create_alert(
                    alert_type=AlertType.BUDGET_THRESHOLD,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Budget Critical: {campaign.name}",
                    message=f"Campaign budget is {utilization:.1f}% utilized (${allocated:,.2f} of ${campaign.budget:,.2f})",
                    entity_type="campaign",
                    entity_id=campaign.id,
                    metadata={"utilization": utilization, "allocated": allocated, "budget": campaign.budget}
                ))
            elif utilization >= 80:
                alerts.append(self._create_alert(
                    alert_type=AlertType.BUDGET_THRESHOLD,
                    severity=AlertSeverity.WARNING,
                    title=f"Budget Warning: {campaign.name}",
                    message=f"Campaign budget is {utilization:.1f}% utilized",
                    entity_type="campaign",
                    entity_id=campaign.id,
                    metadata={"utilization": utilization}
                ))

        return alerts

    def check_deadline_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for approaching deadlines.

        Returns:
            List[Dict[str, Any]]: List of deadline alerts.
        """
        alerts = []
        now = get_current_utc()

        # Check campaign end dates
        campaigns = self.db.query(Campaign).filter(
            and_(
                Campaign.status == CampaignStatus.ACTIVE,
                Campaign.end_date >= now,
                Campaign.end_date <= now + timedelta(days=7)
            )
        ).all()

        for campaign in campaigns:
            days_remaining = (campaign.end_date - now).days

            severity = AlertSeverity.CRITICAL if days_remaining <= 2 else AlertSeverity.WARNING

            alerts.append(self._create_alert(
                alert_type=AlertType.DEADLINE_APPROACHING,
                severity=severity,
                title=f"Campaign Ending Soon: {campaign.name}",
                message=f"Campaign ends in {days_remaining} days",
                entity_type="campaign",
                entity_id=campaign.id,
                metadata={"days_remaining": days_remaining, "end_date": campaign.end_date.isoformat()}
            ))

        return alerts

    def check_content_performance_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for underperforming content.

        Returns:
            List[Dict[str, Any]]: List of content performance alerts.
        """
        alerts = []

        # Get content published 3+ days ago
        cutoff_date = get_current_utc() - timedelta(days=3)

        content_list = self.db.query(CampaignContent).filter(
            and_(
                CampaignContent.status == ContentStatus.PUBLISHED,
                CampaignContent.published_at <= cutoff_date
            )
        ).all()

        for content in content_list:
            # Check if engagement rate is below threshold
            if content.engagement_rate is not None and content.engagement_rate < 1.0:
                alerts.append(self._create_alert(
                    alert_type=AlertType.CONTENT_UNDERPERFORMING,
                    severity=AlertSeverity.WARNING,
                    title=f"Underperforming Content Detected",
                    message=f"Content on {content.platform} has {content.engagement_rate:.2f}% engagement rate",
                    entity_type="content",
                    entity_id=content.id,
                    metadata={
                        "engagement_rate": content.engagement_rate,
                        "reach": content.reach,
                        "platform": content.platform
                    }
                ))

        return alerts

    def check_pending_collaborations(self) -> List[Dict[str, Any]]:
        """
        Check for collaborations pending too long.

        Returns:
            List[Dict[str, Any]]: List of pending collaboration alerts.
        """
        alerts = []

        # Get collaborations pending for 3+ days
        cutoff_date = get_current_utc() - timedelta(days=3)

        pending_collabs = self.db.query(Collaboration).filter(
            and_(
                Collaboration.status == CollaborationStatus.PENDING,
                Collaboration.created_at <= cutoff_date
            )
        ).all()

        for collab in pending_collabs:
            days_pending = (get_current_utc() - collab.created_at).days

            alerts.append(self._create_alert(
                alert_type=AlertType.COLLABORATION_PENDING,
                severity=AlertSeverity.INFO,
                title="Collaboration Awaiting Response",
                message=f"Collaboration has been pending for {days_pending} days",
                entity_type="collaboration",
                entity_id=collab.id,
                metadata={"days_pending": days_pending, "kol_id": collab.kol_id}
            ))

        return alerts

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all alert checks.

        Returns:
            Dict[str, Any]: Summary of all alerts.
        """
        logger.info("Running all alert checks")

        budget_alerts = self.check_budget_alerts()
        deadline_alerts = self.check_deadline_alerts()
        performance_alerts = self.check_content_performance_alerts()
        collaboration_alerts = self.check_pending_collaborations()

        all_alerts = budget_alerts + deadline_alerts + performance_alerts + collaboration_alerts

        # Send critical alerts
        critical_alerts = [a for a in all_alerts if a["severity"] == AlertSeverity.CRITICAL]
        for alert in critical_alerts:
            self._send_alert_notification(alert)

        return {
            "total_alerts": len(all_alerts),
            "by_severity": {
                "critical": len([a for a in all_alerts if a["severity"] == AlertSeverity.CRITICAL]),
                "error": len([a for a in all_alerts if a["severity"] == AlertSeverity.ERROR]),
                "warning": len([a for a in all_alerts if a["severity"] == AlertSeverity.WARNING]),
                "info": len([a for a in all_alerts if a["severity"] == AlertSeverity.INFO])
            },
            "by_type": {
                "budget": len(budget_alerts),
                "deadline": len(deadline_alerts),
                "performance": len(performance_alerts),
                "collaboration": len(collaboration_alerts)
            },
            "alerts": all_alerts,
            "checked_at": get_current_utc().isoformat()
        }

    def _create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        entity_type: str,
        entity_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create alert object."""
        return {
            "id": f"alert_{get_current_utc().timestamp()}",
            "type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": metadata or {},
            "created_at": get_current_utc().isoformat(),
            "acknowledged": False
        }

    def _send_alert_notification(self, alert: Dict[str, Any]) -> None:
        """Send notification for alert."""
        # Determine notification channels based on severity
        if alert["severity"] == AlertSeverity.CRITICAL:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP, NotificationChannel.SMS]
        elif alert["severity"] == AlertSeverity.ERROR:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        else:
            channels = [NotificationChannel.IN_APP]

        # Send to system admins (would be configurable)
        self.comm_service.send_notification(
            recipient_id=1,  # Admin user
            title=f"[{alert['severity'].upper()}] {alert['title']}",
            message=alert["message"],
            channels=channels,
            metadata=alert["metadata"]
        )

        logger.info(f"Alert notification sent: {alert['title']}")


def get_alert_service(db: Session) -> AlertService:
    """
    Dependency for FastAPI to inject AlertService.

    Args:
        db (Session): Database session.

    Returns:
        AlertService: Service instance.
    """
    return AlertService(db)
