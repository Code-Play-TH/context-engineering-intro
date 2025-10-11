"""Celery tasks for notification operations."""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import Task
from sqlmodel import Session, create_engine, select
import logging

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.performance_alert import PerformanceAlert, AlertSeverity
from app.models.user import User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""
    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(str(settings.DATABASE_URL))
        return self._engine

    def get_db(self) -> Session:
        """Get database session."""
        return Session(self.engine)


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.notification_tasks.send_alert_notification")
def send_alert_notification(self, alert_id: int) -> Dict[str, Any]:
    """Send notification for a performance alert."""
    try:
        with self.get_db() as db:
            alert = db.get(PerformanceAlert, alert_id)
            if not alert:
                return {
                    "success": False,
                    "error": f"Alert not found: {alert_id}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get users to notify based on alert severity
            if alert.severity == AlertSeverity.CRITICAL:
                # Notify all admins and campaign managers
                users = db.exec(
                    select(User).where(
                        User.role.in_(["admin", "campaign_manager"])
                    )
                ).all()
            elif alert.severity == AlertSeverity.WARNING:
                # Notify campaign managers only
                users = db.exec(
                    select(User).where(User.role == "campaign_manager")
                ).all()
            else:
                # Info alerts - no automatic notifications
                users = []
            
            if not users:
                return {
                    "success": True,
                    "notifications_sent": 0,
                    "reason": "no_users_to_notify",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Send email notifications
            email_service = EmailService()
            sent_count = 0
            errors = []
            
            for user in users:
                try:
                    # Run async function in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(
                            email_service.send_alert_notification(user.email, alert)
                        )
                        if success:
                            sent_count += 1
                        else:
                            errors.append(f"Failed to send to {user.email}")
                    finally:
                        loop.close()
                except Exception as e:
                    errors.append(f"Error sending to {user.email}: {str(e)}")
            
            # Mark alert as notified
            alert.is_notified = True
            alert.notified_at = datetime.utcnow()
            db.add(alert)
            db.commit()
            
            return {
                "success": True,
                "notifications_sent": sent_count,
                "total_users": len(users),
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error sending alert notification {alert_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "alert_id": alert_id,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.notification_tasks.send_daily_summary")
def send_daily_summary(self) -> Dict[str, Any]:
    """Send daily summary of performance alerts."""
    try:
        with self.get_db() as db:
            # Get alerts from the last 24 hours
            yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            alerts = db.exec(
                select(PerformanceAlert).where(
                    PerformanceAlert.created_at >= yesterday
                )
            ).all()
            
            if not alerts:
                return {
                    "success": True,
                    "alerts_count": 0,
                    "reason": "no_alerts_to_summarize",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Group alerts by severity
            critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
            warning_alerts = [a for a in alerts if a.severity == AlertSeverity.WARNING]
            info_alerts = [a for a in alerts if a.severity == AlertSeverity.INFO]
            
            # Get campaign managers and admins
            users = db.exec(
                select(User).where(
                    User.role.in_(["admin", "campaign_manager"])
                )
            ).all()
            
            if not users:
                return {
                    "success": True,
                    "alerts_count": len(alerts),
                    "notifications_sent": 0,
                    "reason": "no_users_to_notify",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Send summary emails
            email_service = EmailService()
            sent_count = 0
            errors = []
            
            summary_data = {
                "date": yesterday.strftime("%Y-%m-%d"),
                "total_alerts": len(alerts),
                "critical_count": len(critical_alerts),
                "warning_count": len(warning_alerts),
                "info_count": len(info_alerts),
                "critical_alerts": critical_alerts[:5],  # Top 5 critical
                "warning_alerts": warning_alerts[:10]    # Top 10 warnings
            }
            
            for user in users:
                try:
                    # Run async function in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(
                            email_service.send_daily_summary(user.email, summary_data)
                        )
                        if success:
                            sent_count += 1
                        else:
                            errors.append(f"Failed to send to {user.email}")
                    finally:
                        loop.close()
                except Exception as e:
                    errors.append(f"Error sending to {user.email}: {str(e)}")
            
            return {
                "success": True,
                "alerts_count": len(alerts),
                "notifications_sent": sent_count,
                "total_users": len(users),
                "summary": summary_data,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.notification_tasks.process_pending_alerts")
def process_pending_alerts(self) -> Dict[str, Any]:
    """Process alerts that haven't been notified yet."""
    try:
        with self.get_db() as db:
            # Get unnotified alerts
            pending_alerts = db.exec(
                select(PerformanceAlert).where(
                    PerformanceAlert.is_notified == False
                )
            ).all()
            
            if not pending_alerts:
                return {
                    "success": True,
                    "processed": 0,
                    "reason": "no_pending_alerts",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Process each alert
            processed = 0
            errors = []
            
            for alert in pending_alerts:
                try:
                    # Send notification task
                    send_alert_notification.delay(alert.id)
                    processed += 1
                except Exception as e:
                    errors.append({
                        "alert_id": alert.id,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "processed": processed,
                "total_pending": len(pending_alerts),
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error processing pending alerts: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }