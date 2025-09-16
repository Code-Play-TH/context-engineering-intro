"""
Authentication Background Tasks

Background task functions for authentication operations including:
- Email verification processing
- Password reset handling
- Session cleanup and management
- Security audit log processing
- Account lockout management
- Two-factor authentication setup
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.config import get_settings
from app.models.auth import User, UserSession, UserToken, SecurityAuditLog, TokenType, SessionStatus
from app.services.email import EmailService
from app.core.auth import security_service

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id: int, verification_token: str):
    """
    Send email verification email to user.

    Args:
        user_id: User ID to send verification email to
        verification_token: Email verification token

    Returns:
        Dict with success status and details
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            # Get user
            user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if not user:
                logger.error(f"User {user_id} not found for verification email")
                return {"success": False, "error": "User not found"}

            # Prepare email content
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

            email_content = {
                "subject": "Verify Your Email Address - KOL Management System",
                "template": "email_verification",
                "context": {
                    "user_name": user.full_name or user.username or user.email,
                    "verification_url": verification_url,
                    "app_name": "KOL Management System",
                    "support_email": settings.SUPPORT_EMAIL
                }
            }

            # Send email
            email_service = EmailService()
            result = email_service.send_email(
                to_email=user.email,
                **email_content
            )

            if result.get("success"):
                logger.info(f"Verification email sent successfully to user {user_id}")
                return {"success": True, "message": "Verification email sent"}
            else:
                logger.error(f"Failed to send verification email to user {user_id}: {result.get('error')}")
                raise Exception(f"Email sending failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error sending verification email to user {user_id}: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id: int, reset_token: str):
    """
    Send password reset email to user.

    Args:
        user_id: User ID to send reset email to
        reset_token: Password reset token

    Returns:
        Dict with success status and details
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            # Get user
            user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if not user:
                logger.error(f"User {user_id} not found for password reset email")
                return {"success": False, "error": "User not found"}

            # Prepare email content
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

            email_content = {
                "subject": "Password Reset Request - KOL Management System",
                "template": "password_reset",
                "context": {
                    "user_name": user.full_name or user.username or user.email,
                    "reset_url": reset_url,
                    "app_name": "KOL Management System",
                    "support_email": settings.SUPPORT_EMAIL,
                    "expiry_hours": 24
                }
            }

            # Send email
            email_service = EmailService()
            result = email_service.send_email(
                to_email=user.email,
                **email_content
            )

            if result.get("success"):
                logger.info(f"Password reset email sent successfully to user {user_id}")
                return {"success": True, "message": "Password reset email sent"}
            else:
                logger.error(f"Failed to send password reset email to user {user_id}: {result.get('error')}")
                raise Exception(f"Email sending failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error sending password reset email to user {user_id}: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_expired_sessions():
    """
    Clean up expired and terminated sessions.

    Returns:
        Dict with cleanup statistics
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            # Mark expired sessions
            current_time = datetime.utcnow()

            # Update expired sessions
            expired_count = db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.expires_at < current_time,
                        UserSession.status == SessionStatus.ACTIVE
                    )
                )
            ).rowcount

            if expired_count > 0:
                db.execute(
                    UserSession.__table__.update().where(
                        and_(
                            UserSession.expires_at < current_time,
                            UserSession.status == SessionStatus.ACTIVE
                        )
                    ).values(status=SessionStatus.EXPIRED)
                )

            # Delete old terminated sessions (older than 30 days)
            cleanup_date = current_time - timedelta(days=30)
            deleted_count = db.execute(
                delete(UserSession).where(
                    and_(
                        UserSession.status.in_([SessionStatus.EXPIRED, SessionStatus.TERMINATED]),
                        UserSession.terminated_at < cleanup_date
                    )
                )
            ).rowcount

            db.commit()

            logger.info(f"Session cleanup: {expired_count} expired, {deleted_count} deleted")
            return {
                "success": True,
                "expired_sessions": expired_count,
                "deleted_sessions": deleted_count
            }

    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired authentication tokens.

    Returns:
        Dict with cleanup statistics
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            current_time = datetime.utcnow()

            # Delete expired tokens
            deleted_count = db.execute(
                delete(UserToken).where(
                    or_(
                        UserToken.expires_at < current_time,
                        UserToken.is_revoked == True
                    )
                )
            ).rowcount

            db.commit()

            logger.info(f"Token cleanup: {deleted_count} tokens deleted")
            return {
                "success": True,
                "deleted_tokens": deleted_count
            }

    except Exception as e:
        logger.error(f"Error during token cleanup: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def unlock_user_accounts():
    """
    Unlock user accounts that have passed their lockout period.

    Returns:
        Dict with unlock statistics
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            current_time = datetime.utcnow()

            # Find locked users whose lockout period has expired
            users_to_unlock = db.execute(
                select(User).where(
                    and_(
                        User.locked_until.isnot(None),
                        User.locked_until < current_time
                    )
                )
            ).scalars().all()

            unlock_count = 0
            for user in users_to_unlock:
                user.locked_until = None
                user.failed_login_attempts = 0
                unlock_count += 1

                # Log unlock event
                audit_log = SecurityAuditLog(
                    user_id=user.id,
                    event_type="account_unlock",
                    event_category="security",
                    action="unlock",
                    resource="user_account",
                    details={"reason": "lockout_period_expired"},
                    success=True,
                    risk_level="low"
                )
                db.add(audit_log)

            db.commit()

            logger.info(f"Account unlock: {unlock_count} accounts unlocked")
            return {
                "success": True,
                "unlocked_accounts": unlock_count
            }

    except Exception as e:
        logger.error(f"Error during account unlock: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def process_security_alerts():
    """
    Process high-risk security events and send alerts.

    Returns:
        Dict with processing statistics
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            # Find high-risk events from the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            high_risk_events = db.execute(
                select(SecurityAuditLog).where(
                    and_(
                        SecurityAuditLog.risk_level.in_(["high", "critical"]),
                        SecurityAuditLog.timestamp > one_hour_ago
                    )
                ).options(selectinload(SecurityAuditLog.user))
            ).scalars().all()

            if not high_risk_events:
                return {"success": True, "alerts_sent": 0}

            # Group events by type for better reporting
            event_summary = {}
            for event in high_risk_events:
                event_type = event.event_type
                if event_type not in event_summary:
                    event_summary[event_type] = []
                event_summary[event_type].append(event)

            # Send alert email to administrators
            email_service = EmailService()
            admin_emails = settings.SECURITY_ALERT_EMAILS.split(",") if settings.SECURITY_ALERT_EMAILS else []

            if admin_emails:
                alert_content = {
                    "subject": f"Security Alert - {len(high_risk_events)} High-Risk Events Detected",
                    "template": "security_alert",
                    "context": {
                        "event_count": len(high_risk_events),
                        "event_summary": event_summary,
                        "time_period": "last hour",
                        "dashboard_url": f"{settings.FRONTEND_URL}/admin/security"
                    }
                }

                for admin_email in admin_emails:
                    email_service.send_email(to_email=admin_email.strip(), **alert_content)

            logger.info(f"Security alerts processed: {len(high_risk_events)} events, alerts sent to {len(admin_emails)} administrators")
            return {
                "success": True,
                "high_risk_events": len(high_risk_events),
                "alerts_sent": len(admin_emails)
            }

    except Exception as e:
        logger.error(f"Error processing security alerts: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def generate_two_factor_backup_codes(user_id: int) -> Dict[str, Any]:
    """
    Generate new backup codes for two-factor authentication.

    Args:
        user_id: User ID to generate backup codes for

    Returns:
        Dict with success status and backup codes
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            # Get user
            user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if not user:
                return {"success": False, "error": "User not found"}

            # Generate backup codes
            backup_codes = security_service.generate_backup_codes(count=10)

            # Store hashed backup codes in user metadata
            hashed_codes = [security_service.hash_password(code) for code in backup_codes]

            if not user.metadata:
                user.metadata = {}
            user.metadata["backup_codes"] = hashed_codes
            user.metadata["backup_codes_generated_at"] = datetime.utcnow().isoformat()

            db.commit()

            # Log the event
            audit_log = SecurityAuditLog(
                user_id=user.id,
                event_type="backup_codes_generated",
                event_category="security",
                action="generate",
                resource="two_factor_backup_codes",
                details={"code_count": len(backup_codes)},
                success=True,
                risk_level="low"
            )
            db.add(audit_log)
            db.commit()

            logger.info(f"Generated backup codes for user {user_id}")
            return {
                "success": True,
                "backup_codes": backup_codes,  # Return plain codes to show user once
                "message": "Backup codes generated successfully"
            }

    except Exception as e:
        logger.error(f"Error generating backup codes for user {user_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def audit_log_cleanup():
    """
    Clean up old audit logs to maintain database performance.
    Keeps logs for configurable retention period (default 1 year).

    Returns:
        Dict with cleanup statistics
    """
    try:
        from app.core.database import get_sync_session

        with get_sync_session() as db:
            # Calculate retention period (default 1 year)
            retention_days = getattr(settings, "AUDIT_LOG_RETENTION_DAYS", 365)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Delete old audit logs
            deleted_count = db.execute(
                delete(SecurityAuditLog).where(
                    SecurityAuditLog.timestamp < cutoff_date
                )
            ).rowcount

            db.commit()

            logger.info(f"Audit log cleanup: {deleted_count} logs deleted (older than {retention_days} days)")
            return {
                "success": True,
                "deleted_logs": deleted_count,
                "retention_days": retention_days
            }

    except Exception as e:
        logger.error(f"Error during audit log cleanup: {str(e)}")
        return {"success": False, "error": str(e)}


# Scheduled task runners
@shared_task
def run_auth_maintenance():
    """
    Run all authentication maintenance tasks.
    This is the main task that should be scheduled to run periodically.

    Returns:
        Dict with all maintenance results
    """
    logger.info("Starting authentication maintenance tasks")

    results = {
        "session_cleanup": cleanup_expired_sessions.delay().get(),
        "token_cleanup": cleanup_expired_tokens.delay().get(),
        "account_unlock": unlock_user_accounts.delay().get(),
        "audit_cleanup": audit_log_cleanup.delay().get(),
        "security_alerts": process_security_alerts.delay().get()
    }

    logger.info("Authentication maintenance tasks completed")
    return {
        "success": True,
        "maintenance_results": results,
        "timestamp": datetime.utcnow().isoformat()
    }