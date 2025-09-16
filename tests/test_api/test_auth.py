"""
Tests for Authentication API Endpoints

Tests for user registration, login, logout, token management, password operations,
session management, and other authentication-related endpoints.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.auth import User, UserSession, UserToken, TokenType, SecurityAuditLog
from app.schemas.auth import UserCreate, LoginRequest, PasswordResetRequest
from app.core.auth import security_service


class TestUserRegistration:
    """Test cases for user registration endpoints."""

    def test_register_user_success(self, client: TestClient, db_session: AsyncSession):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["full_name"] == user_data["full_name"]
        assert data["user"]["is_active"] is True
        assert data["user"]["is_verified"] is False
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_user_with_existing_email(self, client: TestClient, test_user: User):
        """Test registration with existing email."""
        user_data = {
            "email": test_user.email,  # Use existing email
            "username": "newuser",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_user_with_existing_username(self, client: TestClient, test_user: User):
        """Test registration with existing username."""
        user_data = {
            "email": "newemail@example.com",
            "username": test_user.username,  # Use existing username
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()

    def test_register_user_password_mismatch(self, client: TestClient):
        """Test registration with password mismatch."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPassword123!",
            "confirm_password": "DifferentPassword123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_register_user_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "weak",
            "confirm_password": "weak"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "username": "newuser",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test cases for user login endpoints."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful user login."""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == test_user.email
        assert "access_token" in data
        assert "refresh_token" in data
        assert "session_id" in data
        assert data["token_type"] == "bearer"
        assert data["requires_two_factor"] is False

    def test_login_invalid_email(self, client: TestClient):
        """Test login with invalid email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with invalid password."""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_inactive_user(self, client: TestClient, db_session: AsyncSession):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=security_service.hash_password("TestPassword123!"),
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()

        login_data = {
            "email": inactive_user.email,
            "password": "TestPassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_account_lockout(self, client: TestClient, test_user: User, db_session: AsyncSession):
        """Test account lockout after failed login attempts."""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword"
        }

        # Make 5 failed login attempts
        for i in range(5):
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 401

        # 6th attempt should trigger lockout
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 423  # Locked
        assert "locked" in response.json()["detail"].lower()

        # Even correct password should fail when locked
        correct_login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        response = client.post("/api/v1/auth/login", json=correct_login_data)
        assert response.status_code == 423

    def test_login_remember_me(self, client: TestClient, test_user: User):
        """Test login with remember me option."""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!",
            "remember_me": True
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        # Remember me should extend token expiry
        assert data["expires_in"] > 3600  # More than 1 hour


class TestTokenManagement:
    """Test cases for token management endpoints."""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First login to get tokens
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_invalid_token(self, client: TestClient):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 401

    def test_verify_token_valid(self, client: TestClient, auth_headers: dict):
        """Test token verification with valid token."""
        response = client.post("/api/v1/auth/verify-token", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user" in data

    def test_verify_token_invalid(self, client: TestClient):
        """Test token verification with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/auth/verify-token", headers=headers)

        assert response.status_code == 200  # Endpoint returns 200 with valid=False
        data = response.json()
        assert data["valid"] is False


class TestPasswordManagement:
    """Test cases for password management endpoints."""

    @patch('app.tasks.auth.send_password_reset_email.delay')
    def test_request_password_reset(self, mock_send_email, client: TestClient, test_user: User):
        """Test password reset request."""
        reset_data = {"email": test_user.email}
        response = client.post("/api/v1/auth/password-reset", json=reset_data)

        assert response.status_code == 200
        assert "email sent" in response.json()["message"].lower()
        mock_send_email.assert_called_once()

    def test_request_password_reset_nonexistent_email(self, client: TestClient):
        """Test password reset request for nonexistent email."""
        reset_data = {"email": "nonexistent@example.com"}
        response = client.post("/api/v1/auth/password-reset", json=reset_data)

        # Should return success for security (don't reveal if email exists)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_confirm_password_reset(self, client: TestClient, test_user: User, db_session: AsyncSession):
        """Test password reset confirmation."""
        # Create reset token
        reset_token = security_service.generate_secure_token()
        token_obj = UserToken(
            token=reset_token,
            user_id=test_user.id,
            token_type=TokenType.RESET_PASSWORD,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(token_obj)
        await db_session.commit()

        # Confirm password reset
        reset_data = {
            "token": reset_token,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/password-reset/confirm", json=reset_data)

        assert response.status_code == 200
        assert "password has been reset" in response.json()["message"].lower()

    def test_confirm_password_reset_invalid_token(self, client: TestClient):
        """Test password reset confirmation with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/password-reset/confirm", json=reset_data)

        assert response.status_code == 400

    def test_change_password_success(self, client: TestClient, auth_headers: dict):
        """Test successful password change."""
        change_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=auth_headers)

        assert response.status_code == 200
        assert "password has been changed" in response.json()["message"].lower()

    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test password change with wrong current password."""
        change_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=auth_headers)

        assert response.status_code == 400
        assert "current password is incorrect" in response.json()["detail"].lower()

    def test_change_password_mismatch(self, client: TestClient, auth_headers: dict):
        """Test password change with password mismatch."""
        change_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "DifferentPassword123!"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error


class TestEmailVerification:
    """Test cases for email verification endpoints."""

    @patch('app.tasks.auth.send_verification_email.delay')
    def test_resend_verification_email(self, mock_send_email, client: TestClient, auth_headers: dict):
        """Test resending verification email."""
        response = client.post("/api/v1/auth/resend-verification", headers=auth_headers)

        assert response.status_code == 200
        assert "verification email sent" in response.json()["message"].lower()
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_success(self, client: TestClient, test_user: User, db_session: AsyncSession):
        """Test successful email verification."""
        # Create verification token
        verification_token = security_service.generate_secure_token()
        token_obj = UserToken(
            token=verification_token,
            user_id=test_user.id,
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(token_obj)
        await db_session.commit()

        # Verify email
        verify_data = {"token": verification_token}
        response = client.post("/api/v1/auth/verify-email", json=verify_data)

        assert response.status_code == 200
        assert "email has been verified" in response.json()["message"].lower()

    def test_verify_email_invalid_token(self, client: TestClient):
        """Test email verification with invalid token."""
        verify_data = {"token": "invalid_token"}
        response = client.post("/api/v1/auth/verify-email", json=verify_data)

        assert response.status_code == 400


class TestSessionManagement:
    """Test cases for session management endpoints."""

    def test_get_active_sessions(self, client: TestClient, auth_headers: dict):
        """Test getting active sessions."""
        response = client.get("/api/v1/auth/sessions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.asyncio
    async def test_terminate_session(self, client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession):
        """Test terminating a specific session."""
        # Create a session
        session = UserSession(
            session_id=security_service.create_session_id(),
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=8)
        )
        db_session.add(session)
        await db_session.commit()

        # Terminate session
        terminate_data = {"session_id": session.session_id}
        response = client.post("/api/v1/auth/sessions/terminate", json=terminate_data, headers=auth_headers)

        assert response.status_code == 200
        assert "session terminated" in response.json()["message"].lower()

    def test_terminate_all_sessions(self, client: TestClient, auth_headers: dict):
        """Test terminating all sessions."""
        terminate_data = {"terminate_all": True}
        response = client.post("/api/v1/auth/sessions/terminate", json=terminate_data, headers=auth_headers)

        assert response.status_code == 200
        assert "all sessions terminated" in response.json()["message"].lower()


class TestUserProfile:
    """Test cases for user profile endpoints."""

    def test_get_profile(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting user profile."""
        response = client.get("/api/v1/auth/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username

    def test_update_profile_success(self, client: TestClient, auth_headers: dict):
        """Test successful profile update."""
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "timezone": "America/New_York"
        }
        response = client.put("/api/v1/auth/profile", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert data["timezone"] == "America/New_York"

    def test_update_profile_invalid_data(self, client: TestClient, auth_headers: dict):
        """Test profile update with invalid data."""
        update_data = {
            "email": "newemail@example.com"  # Email cannot be updated via profile
        }
        response = client.put("/api/v1/auth/profile", json=update_data, headers=auth_headers)

        # Should ignore invalid fields or return error
        assert response.status_code in [200, 422]


class TestSecurityStatistics:
    """Test cases for security statistics endpoints."""

    def test_get_security_stats_admin(self, client: TestClient, admin_auth_headers: dict):
        """Test getting security statistics as admin."""
        response = client.get("/api/v1/auth/security-stats", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "failed_logins_24h" in data
        assert "successful_logins_24h" in data
        assert "active_sessions" in data

    def test_get_security_stats_unauthorized(self, client: TestClient, auth_headers: dict):
        """Test getting security statistics as regular user."""
        response = client.get("/api/v1/auth/security-stats", headers=auth_headers)

        assert response.status_code == 403  # Forbidden


class TestAPIKeyManagement:
    """Test cases for API key management endpoints."""

    def test_create_api_key(self, client: TestClient, auth_headers: dict):
        """Test creating an API key."""
        key_data = {
            "name": "Test API Key",
            "description": "API key for testing",
            "scopes": ["read"],
            "rate_limit": 1000
        }
        response = client.post("/api/v1/auth/api-keys", json=key_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test API Key"
        assert data["scopes"] == ["read"]
        assert data["rate_limit"] == 1000
        assert "api_key" in data  # Should contain the actual key
        assert "key_id" in data

    def test_list_api_keys(self, client: TestClient, auth_headers: dict):
        """Test listing API keys."""
        response = client.get("/api/v1/auth/api-keys", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "api_keys" in data
        assert isinstance(data["api_keys"], list)

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession):
        """Test revoking an API key."""
        # Create API key
        from app.models.auth import APIKey
        key_id, api_key = security_service.generate_api_key()
        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=security_service.hash_api_key(api_key),
            user_id=test_user.id,
            name="Test Key"
        )
        db_session.add(api_key_obj)
        await db_session.commit()

        # Revoke key
        response = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=auth_headers)

        assert response.status_code == 200
        assert "revoked" in response.json()["message"].lower()


class TestAuthenticationMiddleware:
    """Test cases for authentication middleware and dependencies."""

    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/profile")

        assert response.status_code == 401

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/profile", headers=headers)

        assert response.status_code == 401

    def test_access_protected_endpoint_with_expired_token(self, client: TestClient, test_user: User):
        """Test accessing protected endpoint with expired token."""
        # Create expired token
        expired_token = security_service.create_access_token(
            {"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/profile", headers=headers)

        assert response.status_code == 401

    def test_access_admin_endpoint_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test accessing admin endpoint as regular user."""
        response = client.get("/api/v1/auth/security-stats", headers=auth_headers)

        assert response.status_code == 403


class TestSecurityAuditing:
    """Test cases for security audit logging."""

    @pytest.mark.asyncio
    async def test_login_creates_audit_log(self, client: TestClient, test_user: User, db_session: AsyncSession):
        """Test that login creates security audit log entry."""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        # Check audit log
        audit_logs = await db_session.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.user_id == test_user.id,
                SecurityAuditLog.event_type == "login"
            )
        )
        log_entry = audit_logs.scalar_one_or_none()

        assert log_entry is not None
        assert log_entry.event_category == "authentication"
        assert log_entry.success is True

    @pytest.mark.asyncio
    async def test_failed_login_creates_audit_log(self, client: TestClient, test_user: User, db_session: AsyncSession):
        """Test that failed login creates security audit log entry."""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401

        # Check audit log
        audit_logs = await db_session.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.user_id == test_user.id,
                SecurityAuditLog.event_type == "failed_login"
            )
        )
        log_entry = audit_logs.scalar_one_or_none()

        assert log_entry is not None
        assert log_entry.event_category == "security"
        assert log_entry.success is False