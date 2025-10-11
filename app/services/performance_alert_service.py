"""Performance alert service for managing KOL performance alerts and notifications."""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, or_, func
from fastapi import HTTPException, status
import logging
from enum import Enum

from app.models.performance_alert import PerformanceAlert, AlertType, AlertSeverity
from app.models.kol import KOL
from app.models.user import User
from app.models.campaign import Campaign
from app.models.brief import Brief
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AlertRule(str, Enum):
    """Alert rule types."""
    FOLLOWER_DROP_THRESHOLD = "follower_drop_threshold"
    ENGAGEMENT_DROP_THRESHOLD = "engagement_drop_threshold"
    INACTIVE_PERIOD = "inactive_period"
    SUSPICIOUS_GROWTH = "suspicious_growth"
    CAMPAIGN_UNDERPERFORMANCE = "campaign_underperformance"


class EscalationLevel(str, Enum):
    """Alert escalation levels."""
    NONE = "none"
    MANAGER = "manager"
    ADMIN = "admin"
    IMMEDIATE = "immediate"


class PerformanceAlertService:
    """Service for managing performance alerts and notifications."""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        
        # Default alert thresholds (can be customized per KOL/campaign)
        self.default_thresholds = {
            AlertRule.FOLLOWER_DROP_THRESHOLD: 10.0,      # % drop
            AlertRule.ENGAGEMENT_DROP_THRESHOLD: 20.0,    # % drop
            AlertRule.INACTIVE_PERIOD: 7,                 # days
            AlertRule.SUSPICIOUS_GROWTH: 50.0,            # % increase
            AlertRule.CAMPAIGN_UNDERPERFORMANCE: 30.0,    # % below target
        }
        
        # Escalation rules
        self.escalation_rules = {
            AlertSeverity.INFO: EscalationLevel.NONE,
            AlertSeverity.WARNING: EscalationLevel.NONE,
            AlertSeverity.CRITICAL: EscalationLevel.MANAGER,
        }
        
        # Auto-acknowledgment timeouts (hours)
        self.auto_ack_timeouts = {
            AlertSeverity.INFO: 24,
            AlertSeverity.WARNING: 48,
            AlertSeverity.CRITICAL: 72,
        }
    
    async def create_alert(
        self,
        kol_id: int,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        actual_value: Optional[float] = None,
        previous_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        context_data: Optional[Dict[str, Any]] = None,
        auto_notify: bool = True
    ) -> PerformanceAlert:
        """Create a new performance alert."""
        # Check if similar alert already exists (avoid duplicates)
        existing_alert = await self._check_duplicate_alert(
            kol_id, alert_type, severity, actual_value
        )
        
        if existing_alert:
            logger.info(f"Similar alert already exists for KOL {kol_id}, updating instead")
            return await self._update_existing_alert(existing_alert, message, actual_value, context_data)
        
        # Create new alert
        alert = PerformanceAlert(
            kol_id=kol_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            actual_value=actual_value,
            previous_value=previous_value,
            threshold_value=threshold_value,
            context_data=context_data or {}
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Created {severity.value} alert for KOL {kol_id}: {title}")
        
        # Send notifications if enabled
        if auto_notify:
            await self._send_alert_notifications(alert)
        
        # Check for escalation
        await self._check_escalation_rules(alert)
        
        return alert
    
    async def acknowledge_alert(
        self,
        alert_id: int,
        user_id: int,
        acknowledgment_note: Optional[str] = None
    ) -> PerformanceAlert:
        """Acknowledge a performance alert."""
        alert = self.db.get(PerformanceAlert, alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert not found: {alert_id}"
            )
        
        if alert.is_acknowledged:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert is already acknowledged"
            )
        
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        alert.acknowledgment_note = acknowledgment_note
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
        
        return alert
    
    async def bulk_acknowledge_alerts(
        self,
        alert_ids: List[int],
        user_id: int,
        acknowledgment_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Acknowledge multiple alerts at once."""
        acknowledged = []
        errors = []
        
        for alert_id in alert_ids:
            try:
                alert = await self.acknowledge_alert(alert_id, user_id, acknowledgment_note)
                acknowledged.append(alert.id)
            except Exception as e:
                errors.append({
                    "alert_id": alert_id,
                    "error": str(e)
                })
        
        return {
            "acknowledged": len(acknowledged),
            "failed": len(errors),
            "total": len(alert_ids),
            "acknowledged_alerts": acknowledged,
            "errors": errors
        }
    
    async def get_alerts(
        self,
        kol_id: Optional[int] = None,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        is_acknowledged: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[PerformanceAlert], int]:
        """Get alerts with filtering options."""
        statement = select(PerformanceAlert)
        
        # Apply filters
        if kol_id is not None:
            statement = statement.where(PerformanceAlert.kol_id == kol_id)
        
        if severity is not None:
            statement = statement.where(PerformanceAlert.severity == severity)
        
        if alert_type is not None:
            statement = statement.where(PerformanceAlert.alert_type == alert_type)
        
        if is_acknowledged is not None:
            statement = statement.where(PerformanceAlert.is_acknowledged == is_acknowledged)
        
        if start_date is not None:
            statement = statement.where(PerformanceAlert.created_at >= start_date)
        
        if end_date is not None:
            statement = statement.where(PerformanceAlert.created_at <= end_date)
        
        # Get total count
        count_statement = select(func.count(PerformanceAlert.id)).where(statement.whereclause)
        total = self.db.exec(count_statement).first()
        
        # Apply ordering and pagination
        statement = statement.order_by(
            PerformanceAlert.created_at.desc()
        ).offset(skip).limit(limit)
        
        alerts = self.db.exec(statement).all()
        
        return list(alerts), total
    
    async def get_alert_summary(
        self,
        kol_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get alert summary statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        statement = select(PerformanceAlert).where(
            PerformanceAlert.created_at >= cutoff_date
        )
        
        if kol_id is not None:
            statement = statement.where(PerformanceAlert.kol_id == kol_id)
        
        alerts = self.db.exec(statement).all()
        
        # Calculate statistics
        total_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        warning_alerts = len([a for a in alerts if a.severity == AlertSeverity.WARNING])
        info_alerts = len([a for a in alerts if a.severity == AlertSeverity.INFO])
        
        acknowledged_alerts = len([a for a in alerts if a.is_acknowledged])
        unacknowledged_alerts = total_alerts - acknowledged_alerts
        
        # Group by alert type
        alert_types = {}
        for alert in alerts:
            alert_type = alert.alert_type.value
            if alert_type not in alert_types:
                alert_types[alert_type] = 0
            alert_types[alert_type] += 1
        
        # Calculate response times for acknowledged alerts
        response_times = []
        for alert in alerts:
            if alert.is_acknowledged and alert.acknowledged_at:
                response_time = (alert.acknowledged_at - alert.created_at).total_seconds() / 3600  # hours
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "period_days": days,
            "total_alerts": total_alerts,
            "severity_breakdown": {
                "critical": critical_alerts,
                "warning": warning_alerts,
                "info": info_alerts
            },
            "acknowledgment_status": {
                "acknowledged": acknowledged_alerts,
                "unacknowledged": unacknowledged_alerts,
                "acknowledgment_rate": (acknowledged_alerts / total_alerts * 100) if total_alerts > 0 else 0
            },
            "alert_types": alert_types,
            "response_metrics": {
                "avg_response_time_hours": avg_response_time,
                "total_responses": len(response_times)
            },
            "generated_at": datetime.utcnow()
        }
    
    async def configure_alert_thresholds(
        self,
        kol_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        thresholds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Configure custom alert thresholds for KOL or campaign."""
        # This would typically store custom thresholds in a separate table
        # For now, we'll return the configuration structure
        
        if not thresholds:
            thresholds = self.default_thresholds.copy()
        
        config = {
            "kol_id": kol_id,
            "campaign_id": campaign_id,
            "thresholds": {rule.value: value for rule, value in thresholds.items()},
            "configured_at": datetime.utcnow()
        }
        
        # In a real implementation, you would save this to a configuration table
        logger.info(f"Alert thresholds configured for KOL {kol_id}, Campaign {campaign_id}")
        
        return config
    
    async def get_escalation_queue(self) -> List[Dict[str, Any]]:
        """Get alerts that need escalation."""
        # Get critical unacknowledged alerts older than 1 hour
        escalation_cutoff = datetime.utcnow() - timedelta(hours=1)
        
        alerts = self.db.exec(
            select(PerformanceAlert).where(
                and_(
                    PerformanceAlert.severity == AlertSeverity.CRITICAL,
                    PerformanceAlert.is_acknowledged == False,
                    PerformanceAlert.created_at <= escalation_cutoff
                )
            ).order_by(PerformanceAlert.created_at.asc())
        ).all()
        
        escalation_queue = []
        
        for alert in alerts:
            kol = self.db.get(KOL, alert.kol_id)
            
            # Check if KOL is in active campaigns
            active_campaigns = self._get_kol_active_campaigns(alert.kol_id)
            
            escalation_queue.append({
                "alert_id": alert.id,
                "kol_id": alert.kol_id,
                "kol_name": kol.name if kol else "Unknown",
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "created_at": alert.created_at.isoformat(),
                "hours_since_created": (datetime.utcnow() - alert.created_at).total_seconds() / 3600,
                "active_campaigns": len(active_campaigns),
                "escalation_level": self.escalation_rules[alert.severity].value
            })
        
        return escalation_queue
    
    async def auto_acknowledge_old_alerts(self) -> Dict[str, Any]:
        """Automatically acknowledge old alerts based on timeout rules."""
        acknowledged_count = 0
        
        for severity, timeout_hours in self.auto_ack_timeouts.items():
            cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)
            
            old_alerts = self.db.exec(
                select(PerformanceAlert).where(
                    and_(
                        PerformanceAlert.severity == severity,
                        PerformanceAlert.is_acknowledged == False,
                        PerformanceAlert.created_at <= cutoff_time
                    )
                )
            ).all()
            
            for alert in old_alerts:
                alert.is_acknowledged = True
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledgment_note = f"Auto-acknowledged after {timeout_hours} hours"
                self.db.add(alert)
                acknowledged_count += 1
        
        if acknowledged_count > 0:
            self.db.commit()
            logger.info(f"Auto-acknowledged {acknowledged_count} old alerts")
        
        return {
            "auto_acknowledged": acknowledged_count,
            "processed_at": datetime.utcnow()
        }
    
    async def _check_duplicate_alert(
        self,
        kol_id: int,
        alert_type: AlertType,
        severity: AlertSeverity,
        actual_value: Optional[float]
    ) -> Optional[PerformanceAlert]:
        """Check if a similar alert already exists."""
        # Look for unacknowledged alerts of the same type within the last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        existing_alert = self.db.exec(
            select(PerformanceAlert).where(
                and_(
                    PerformanceAlert.kol_id == kol_id,
                    PerformanceAlert.alert_type == alert_type,
                    PerformanceAlert.severity == severity,
                    PerformanceAlert.is_acknowledged == False,
                    PerformanceAlert.created_at >= cutoff_time
                )
            )
        ).first()
        
        return existing_alert
    
    async def _update_existing_alert(
        self,
        alert: PerformanceAlert,
        message: str,
        actual_value: Optional[float],
        context_data: Optional[Dict[str, Any]]
    ) -> PerformanceAlert:
        """Update an existing alert with new information."""
        alert.message = message
        if actual_value is not None:
            alert.actual_value = actual_value
        if context_data:
            alert.context_data.update(context_data)
        
        alert.updated_at = datetime.utcnow()
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    async def _send_alert_notifications(self, alert: PerformanceAlert) -> None:
        """Send notifications for a new alert."""
        try:
            # Get users to notify based on alert severity
            users_to_notify = await self._get_notification_recipients(alert)
            
            if not users_to_notify:
                return
            
            # Get KOL information
            kol = self.db.get(KOL, alert.kol_id)
            kol_name = kol.name if kol else f"KOL {alert.kol_id}"
            
            # Send email notifications
            for user in users_to_notify:
                try:
                    await self.email_service.send_performance_alert_notification(
                        user.email,
                        {
                            "alert_id": alert.id,
                            "kol_name": kol_name,
                            "alert_type": alert.alert_type.value,
                            "severity": alert.severity.value,
                            "title": alert.title,
                            "message": alert.message,
                            "created_at": alert.created_at.isoformat()
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send alert notification to {user.email}: {e}")
            
            # Mark as notified
            alert.is_notified = True
            alert.notified_at = datetime.utcnow()
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    async def _get_notification_recipients(self, alert: PerformanceAlert) -> List[User]:
        """Get users who should be notified about an alert."""
        # Get users based on alert severity
        if alert.severity == AlertSeverity.CRITICAL:
            # Notify admins and campaign managers
            users = self.db.exec(
                select(User).where(
                    User.role.in_(["admin", "campaign_manager"])
                )
            ).all()
        elif alert.severity == AlertSeverity.WARNING:
            # Notify campaign managers only
            users = self.db.exec(
                select(User).where(User.role == "campaign_manager")
            ).all()
        else:
            # Info alerts - no automatic notifications
            users = []
        
        return list(users)
    
    async def _check_escalation_rules(self, alert: PerformanceAlert) -> None:
        """Check if alert needs escalation."""
        escalation_level = self.escalation_rules.get(alert.severity)
        
        if escalation_level == EscalationLevel.IMMEDIATE:
            # Send immediate escalation (e.g., SMS, Slack)
            logger.warning(f"IMMEDIATE ESCALATION: Alert {alert.id} requires immediate attention")
            # Implementation would send urgent notifications
        
        elif escalation_level == EscalationLevel.ADMIN:
            # Escalate to admin after delay
            # This would typically be handled by a background task
            logger.info(f"Alert {alert.id} marked for admin escalation")
    
    def _get_kol_active_campaigns(self, kol_id: int) -> List[Campaign]:
        """Get active campaigns for a KOL."""
        # Get briefs for this KOL
        briefs = self.db.exec(
            select(Brief).where(Brief.kol_id == kol_id)
        ).all()
        
        campaign_ids = [brief.campaign_id for brief in briefs]
        
        if not campaign_ids:
            return []
        
        # Get active campaigns
        active_campaigns = self.db.exec(
            select(Campaign).where(
                and_(
                    Campaign.id.in_(campaign_ids),
                    Campaign.status.in_(["active", "running"])
                )
            )
        ).all()
        
        return list(active_campaigns)
    
    async def cleanup_old_alerts(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up old acknowledged alerts."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Only delete acknowledged alerts older than cutoff
        old_alerts = self.db.exec(
            select(PerformanceAlert).where(
                and_(
                    PerformanceAlert.is_acknowledged == True,
                    PerformanceAlert.created_at < cutoff_date
                )
            )
        ).all()
        
        deleted_count = len(old_alerts)
        
        for alert in old_alerts:
            self.db.delete(alert)
        
        if deleted_count > 0:
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old alerts")
        
        return {
            "deleted_alerts": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "cleaned_at": datetime.utcnow()
        }