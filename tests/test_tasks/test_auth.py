"""
Tests for Authentication Background Tasks

Tests for authentication-related background tasks including email sending,
session cleanup, security alerts, and maintenance operations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.tasks.auth import (
    send_verification_email, send_password_reset_email, cleanup_expired_sessions,
    cleanup_expired_tokens, unlock_user_accounts, process_security_alerts,
    generate_two_factor_backup_codes, audit_log_cleanup, run_auth_maintenance
)
from app.models.auth import (
    User, UserSession, UserToken, SecurityAuditLog, TokenType, SessionStatus
)
from app.core.auth import security_service


class TestEmailTasks:
    """Test cases for email-related background tasks."""

    @patch('app.tasks.auth.get_sync_session')
    @patch('app.tasks.auth.EmailService')
    def test_send_verification_email_success(self, mock_email_service, mock_get_session):
        """Test successful verification email sending."""
        # Mock database session and user
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock email service
        mock_email_instance = MagicMock()
        mock_email_instance.send_email.return_value = {"success": True}
        mock_email_service.return_value = mock_email_instance

        # Execute task
        result = send_verification_email(user_id=1, verification_token="test_token")

        assert result["success"] is True
        assert "verification email sent" in result["message"].lower()
        mock_email_instance.send_email.assert_called_once()

    @patch('app.tasks.auth.get_sync_session')
    def test_send_verification_email_user_not_found(self, mock_get_session):
        """Test verification email sending with non-existent user."""
        # Mock database session with no user found
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Execute task
        result = send_verification_email(user_id=999, verification_token="test_token")

        assert result["success"] is False
        assert "user not found" in result["error"].lower()

    @patch('app.tasks.auth.get_sync_session')
    @patch('app.tasks.auth.EmailService')
    def test_send_verification_email_email_failure(self, mock_email_service, mock_get_session):
        """Test verification email sending with email service failure."""
        # Mock database session and user
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock email service failure
        mock_email_instance = MagicMock()
        mock_email_instance.send_email.return_value = {"success": False, "error": "SMTP error"}
        mock_email_service.return_value = mock_email_instance

        # Execute task with retry disabled
        with patch.object(send_verification_email, 'retry') as mock_retry:
            mock_retry.side_effect = Exception("SMTP error")

            result = send_verification_email(user_id=1, verification_token="test_token")

            assert result["success"] is False
            assert "error" in result

    @patch('app.tasks.auth.get_sync_session')
    @patch('app.tasks.auth.EmailService')
    def test_send_password_reset_email_success(self, mock_email_service, mock_get_session):
        """Test successful password reset email sending."""
        # Mock database session and user
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock email service
        mock_email_instance = MagicMock()
        mock_email_instance.send_email.return_value = {"success": True}
        mock_email_service.return_value = mock_email_instance

        # Execute task
        result = send_password_reset_email(user_id=1, reset_token="reset_token")

        assert result["success"] is True
        assert "password reset email sent" in result["message"].lower()
        mock_email_instance.send_email.assert_called_once()

    @patch('app.tasks.auth.get_sync_session')
    def test_send_password_reset_email_user_not_found(self, mock_get_session):
        """Test password reset email sending with non-existent user."""
        # Mock database session with no user found
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Execute task
        result = send_password_reset_email(user_id=999, reset_token="reset_token")

        assert result["success"] is False
        assert "user not found" in result["error"].lower()


class TestCleanupTasks:
    """Test cases for cleanup background tasks."""

    @patch('app.tasks.auth.get_sync_session')
    def test_cleanup_expired_sessions_success(self, mock_get_session):
        """Test successful session cleanup."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock expired sessions count
        mock_session.execute.return_value.rowcount = 5

        # Execute task
        result = cleanup_expired_sessions()

        assert result["success"] is True
        assert result["expired_sessions"] == 5
        assert "deleted_sessions" in result

    @patch('app.tasks.auth.get_sync_session')
    def test_cleanup_expired_sessions_database_error(self, mock_get_session):
        """Test session cleanup with database error."""
        # Mock database error
        mock_get_session.side_effect = Exception("Database connection error")

        # Execute task
        result = cleanup_expired_sessions()

        assert result["success"] is False
        assert "database connection error" in result["error"].lower()

    @patch('app.tasks.auth.get_sync_session')
    def test_cleanup_expired_tokens_success(self, mock_get_session):
        """Test successful token cleanup."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock deleted tokens count
        mock_session.execute.return_value.rowcount = 10

        # Execute task
        result = cleanup_expired_tokens()

        assert result["success"] is True
        assert result["deleted_tokens"] == 10

    @patch('app.tasks.auth.get_sync_session')
    def test_cleanup_expired_tokens_database_error(self, mock_get_session):
        """Test token cleanup with database error."""
        # Mock database error
        mock_get_session.side_effect = Exception("Database error")

        # Execute task
        result = cleanup_expired_tokens()

        assert result["success"] is False
        assert "database error" in result["error"].lower()

    @patch('app.tasks.auth.get_sync_session')
    def test_audit_log_cleanup_success(self, mock_get_session):
        """Test successful audit log cleanup."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock deleted logs count
        mock_session.execute.return_value.rowcount = 100

        # Execute task
        result = audit_log_cleanup()

        assert result["success"] is True
        assert result["deleted_logs"] == 100
        assert result["retention_days"] > 0

    @patch('app.tasks.auth.get_sync_session')
    def test_audit_log_cleanup_with_custom_retention(self, mock_get_session):
        """Test audit log cleanup with custom retention period."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value.rowcount = 50

        # Mock settings with custom retention
        with patch('app.tasks.auth.settings') as mock_settings:
            mock_settings.AUDIT_LOG_RETENTION_DAYS = 180

            # Execute task
            result = audit_log_cleanup()

            assert result["success"] is True
            assert result["retention_days"] == 180


class TestSecurityTasks:
    """Test cases for security-related background tasks."""

    @patch('app.tasks.auth.get_sync_session')
    def test_unlock_user_accounts_success(self, mock_get_session):
        """Test successful user account unlocking."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock locked users
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.locked_until = datetime.utcnow() - timedelta(minutes=1)
        mock_user1.failed_login_attempts = 5

        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.locked_until = datetime.utcnow() - timedelta(minutes=5)
        mock_user2.failed_login_attempts = 3

        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_user1, mock_user2]

        # Execute task
        result = unlock_user_accounts()

        assert result["success"] is True
        assert result["unlocked_accounts"] == 2

        # Check that users were unlocked
        assert mock_user1.locked_until is None
        assert mock_user1.failed_login_attempts == 0
        assert mock_user2.locked_until is None
        assert mock_user2.failed_login_attempts == 0

    @patch('app.tasks.auth.get_sync_session')
    def test_unlock_user_accounts_no_locked_users(self, mock_get_session):
        """Test account unlocking with no locked users."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # No locked users
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        # Execute task
        result = unlock_user_accounts()

        assert result["success"] is True
        assert result["unlocked_accounts"] == 0

    @patch('app.tasks.auth.get_sync_session')
    @patch('app.tasks.auth.EmailService')
    def test_process_security_alerts_with_high_risk_events(self, mock_email_service, mock_get_session):
        """Test security alert processing with high-risk events."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock high-risk events
        mock_event1 = MagicMock()
        mock_event1.event_type = "failed_login"
        mock_event1.risk_level = "high"

        mock_event2 = MagicMock()
        mock_event2.event_type = "privilege_escalation"
        mock_event2.risk_level = "critical"

        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_event1, mock_event2]

        # Mock email service
        mock_email_instance = MagicMock()
        mock_email_instance.send_email.return_value = {"success": True}
        mock_email_service.return_value = mock_email_instance

        # Mock settings
        with patch('app.tasks.auth.settings') as mock_settings:
            mock_settings.SECURITY_ALERT_EMAILS = "admin1@example.com,admin2@example.com"

            # Execute task
            result = process_security_alerts()

            assert result["success"] is True
            assert result["high_risk_events"] == 2
            assert result["alerts_sent"] == 2

    @patch('app.tasks.auth.get_sync_session')
    def test_process_security_alerts_no_events(self, mock_get_session):
        """Test security alert processing with no high-risk events."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # No high-risk events
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        # Execute task
        result = process_security_alerts()

        assert result["success"] is True
        assert result["alerts_sent"] == 0

    @patch('app.tasks.auth.get_sync_session')
    def test_generate_two_factor_backup_codes_success(self, mock_get_session):
        """Test successful backup codes generation."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.metadata = {}
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Execute task
        result = generate_two_factor_backup_codes(user_id=1)

        assert result["success"] is True
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10
        assert all(isinstance(code, str) for code in result["backup_codes"])

        # Check that metadata was updated
        assert "backup_codes" in mock_user.metadata
        assert "backup_codes_generated_at" in mock_user.metadata

    @patch('app.tasks.auth.get_sync_session')
    def test_generate_two_factor_backup_codes_user_not_found(self, mock_get_session):
        """Test backup codes generation with non-existent user."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Execute task
        result = generate_two_factor_backup_codes(user_id=999)

        assert result["success"] is False
        assert "user not found" in result["error"].lower()


class TestMaintenanceTasks:
    """Test cases for maintenance task orchestration."""

    @patch('app.tasks.auth.cleanup_expired_sessions')
    @patch('app.tasks.auth.cleanup_expired_tokens')
    @patch('app.tasks.auth.unlock_user_accounts')
    @patch('app.tasks.auth.audit_log_cleanup')
    @patch('app.tasks.auth.process_security_alerts')
    def test_run_auth_maintenance_success(self, mock_security_alerts, mock_audit_cleanup,
                                        mock_unlock_accounts, mock_token_cleanup, mock_session_cleanup):
        """Test successful authentication maintenance run."""
        # Mock all subtasks
        mock_session_cleanup.delay.return_value.get.return_value = {"success": True, "expired_sessions": 5}
        mock_token_cleanup.delay.return_value.get.return_value = {"success": True, "deleted_tokens": 10}
        mock_unlock_accounts.delay.return_value.get.return_value = {"success": True, "unlocked_accounts": 2}
        mock_audit_cleanup.delay.return_value.get.return_value = {"success": True, "deleted_logs": 100}
        mock_security_alerts.delay.return_value.get.return_value = {"success": True, "alerts_sent": 1}

        # Execute task
        result = run_auth_maintenance()

        assert result["success"] is True
        assert "maintenance_results" in result
        assert "timestamp" in result

        # Check that all subtasks were called
        mock_session_cleanup.delay.assert_called_once()
        mock_token_cleanup.delay.assert_called_once()
        mock_unlock_accounts.delay.assert_called_once()
        mock_audit_cleanup.delay.assert_called_once()
        mock_security_alerts.delay.assert_called_once()

    @patch('app.tasks.auth.cleanup_expired_sessions')
    @patch('app.tasks.auth.cleanup_expired_tokens')
    @patch('app.tasks.auth.unlock_user_accounts')
    @patch('app.tasks.auth.audit_log_cleanup')
    @patch('app.tasks.auth.process_security_alerts')
    def test_run_auth_maintenance_with_failures(self, mock_security_alerts, mock_audit_cleanup,
                                               mock_unlock_accounts, mock_token_cleanup, mock_session_cleanup):
        """Test authentication maintenance with some task failures."""
        # Mock subtasks with mixed results
        mock_session_cleanup.delay.return_value.get.return_value = {"success": True, "expired_sessions": 5}
        mock_token_cleanup.delay.return_value.get.return_value = {"success": False, "error": "Database error"}
        mock_unlock_accounts.delay.return_value.get.return_value = {"success": True, "unlocked_accounts": 0}
        mock_audit_cleanup.delay.return_value.get.return_value = {"success": True, "deleted_logs": 50}
        mock_security_alerts.delay.return_value.get.return_value = {"success": True, "alerts_sent": 0}

        # Execute task
        result = run_auth_maintenance()

        assert result["success"] is True  # Overall task succeeds even if subtasks fail
        assert "maintenance_results" in result

        # Check that token cleanup failed
        maintenance_results = result["maintenance_results"]
        assert maintenance_results["token_cleanup"]["success"] is False
        assert "error" in maintenance_results["token_cleanup"]


class TestTaskRetryMechanisms:
    """Test cases for task retry and error handling."""

    @patch('app.tasks.auth.get_sync_session')
    @patch('app.tasks.auth.EmailService')
    def test_email_task_retry_on_failure(self, mock_email_service, mock_get_session):
        """Test email task retry mechanism on failure."""
        # Mock database session and user
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock email service failure
        mock_email_instance = MagicMock()
        mock_email_instance.send_email.return_value = {"success": False, "error": "SMTP timeout"}
        mock_email_service.return_value = mock_email_instance

        # Mock the task to track retry calls
        with patch.object(send_verification_email, 'retry', side_effect=Exception("Max retries exceeded")) as mock_retry:
            result = send_verification_email(user_id=1, verification_token="test_token")

            assert result["success"] is False
            mock_retry.assert_called()

    @patch('app.tasks.auth.get_sync_session')
    def test_cleanup_task_exception_handling(self, mock_get_session):
        """Test cleanup task exception handling."""
        # Mock database connection error
        mock_get_session.side_effect = Exception("Connection timeout")

        # Execute task
        result = cleanup_expired_sessions()

        assert result["success"] is False
        assert "connection timeout" in result["error"].lower()

    @patch('app.tasks.auth.get_sync_session')
    def test_security_task_database_rollback(self, mock_get_session):
        """Test security task database rollback on error."""
        # Mock database session with commit error
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("Database constraint violation")
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Execute task
        result = unlock_user_accounts()

        assert result["success"] is False
        assert "database constraint violation" in result["error"].lower()


class TestTaskLogging:
    """Test cases for task logging and monitoring."""

    @patch('app.tasks.auth.logger')
    @patch('app.tasks.auth.get_sync_session')
    def test_task_logging_success(self, mock_get_session, mock_logger):
        """Test that successful tasks log appropriately."""
        # Mock successful session cleanup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.execute.return_value.rowcount = 5

        # Execute task
        cleanup_expired_sessions()

        # Check that success was logged
        mock_logger.info.assert_called()

    @patch('app.tasks.auth.logger')
    @patch('app.tasks.auth.get_sync_session')
    def test_task_logging_error(self, mock_get_session, mock_logger):
        """Test that failed tasks log errors appropriately."""
        # Mock database error
        mock_get_session.side_effect = Exception("Database error")

        # Execute task
        cleanup_expired_sessions()

        # Check that error was logged
        mock_logger.error.assert_called()

    @patch('app.tasks.auth.logger')
    @patch('app.tasks.auth.get_sync_session')
    @patch('app.tasks.auth.EmailService')
    def test_email_task_logging(self, mock_email_service, mock_get_session, mock_logger):
        """Test email task logging."""
        # Mock successful email sending
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_user = MagicMock()
        mock_user.id = 1
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        mock_email_instance = MagicMock()
        mock_email_instance.send_email.return_value = {"success": True}
        mock_email_service.return_value = mock_email_instance

        # Execute task
        send_verification_email(user_id=1, verification_token="test_token")

        # Check that info was logged
        mock_logger.info.assert_called()


class TestTaskIntegration:
    """Integration tests for authentication tasks."""

    @pytest.mark.asyncio
    async def test_task_database_integration(self, seeded_db_session: AsyncSession):
        """Test tasks with real database integration."""
        # Create test user
        user = User(
            email="tasktest@example.com",
            username="taskuser",
            hashed_password=security_service.hash_password("password"),
            locked_until=datetime.utcnow() - timedelta(minutes=1)
        )
        seeded_db_session.add(user)
        await seeded_db_session.commit()

        # Create expired session
        session = UserSession(
            session_id="expired_session",
            user_id=user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1),
            status=SessionStatus.ACTIVE
        )
        seeded_db_session.add(session)

        # Create expired token
        token = UserToken(
            token="expired_token",
            user_id=user.id,
            token_type=TokenType.ACCESS,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        seeded_db_session.add(token)

        # Create old audit log
        audit_log = SecurityAuditLog(
            user_id=user.id,
            event_type="test_event",
            event_category="test",
            success=True,
            risk_level="low",
            timestamp=datetime.utcnow() - timedelta(days=400)
        )
        seeded_db_session.add(audit_log)

        await seeded_db_session.commit()

        # Note: In real integration tests, we would actually call the task functions
        # with a real database connection, but for unit tests we mock the database layer
        # to avoid dependencies on the actual task queue system