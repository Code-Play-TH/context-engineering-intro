"""
Tests for Authentication Models

Tests for User, Role, Permission, UserSession, UserToken, APIKey, SecurityAuditLog models.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.auth import (
    User, Role, Permission, UserSession, UserToken, APIKey, SecurityAuditLog,
    UserRole, UserStatus, TokenType, SessionStatus, user_roles, role_permissions
)
from app.core.auth import security_service


class TestUserModel:
    """Test cases for User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=security_service.hash_password("password123"),
            full_name="Test User",
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.status == UserStatus.ACTIVE
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_user_password_verification(self, db_session: AsyncSession):
        """Test password verification."""
        password = "TestPassword123!"
        user = User(
            email="test@example.com",
            hashed_password=security_service.hash_password(password)
        )
        db_session.add(user)
        await db_session.commit()

        # Test correct password
        assert security_service.verify_password(password, user.hashed_password)

        # Test incorrect password
        assert not security_service.verify_password("wrongpassword", user.hashed_password)

    @pytest.mark.asyncio
    async def test_user_is_locked_property(self, db_session: AsyncSession):
        """Test user account lockout functionality."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()

        # User not locked initially
        assert not user.is_locked

        # Lock user for 30 minutes
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        await db_session.commit()
        assert user.is_locked

        # User should not be locked after lockout period
        user.locked_until = datetime.utcnow() - timedelta(minutes=1)
        await db_session.commit()
        assert not user.is_locked

    @pytest.mark.asyncio
    async def test_user_role_assignment(self, db_session: AsyncSession, seeded_db_session: AsyncSession):
        """Test user role assignment."""
        # Create user
        user = User(
            email="test@example.com",
            hashed_password=security_service.hash_password("password")
        )
        seeded_db_session.add(user)
        await seeded_db_session.flush()

        # Get admin role
        admin_role = await seeded_db_session.execute(
            select(Role).where(Role.name == "admin")
        )
        role = admin_role.scalar_one()

        # Assign role to user
        await seeded_db_session.execute(
            user_roles.insert().values(user_id=user.id, role_id=role.id)
        )
        await seeded_db_session.commit()

        # Refresh user with roles
        await seeded_db_session.refresh(user)
        stmt = select(User).where(User.id == user.id).options(
            select(User).options(selectinload(User.roles))
        )
        result = await seeded_db_session.execute(stmt)
        user_with_roles = result.scalar_one()

        assert user_with_roles.has_role("admin")
        assert not user_with_roles.has_role("viewer")

    @pytest.mark.asyncio
    async def test_user_permission_check(self, seeded_db_session: AsyncSession):
        """Test user permission checking through roles."""
        # Create user
        user = User(
            email="test@example.com",
            hashed_password=security_service.hash_password("password")
        )
        seeded_db_session.add(user)
        await seeded_db_session.flush()

        # Get manager role (should have kol permissions)
        manager_role = await seeded_db_session.execute(
            select(Role).where(Role.name == "manager")
        )
        role = manager_role.scalar_one()

        # Assign role to user
        await seeded_db_session.execute(
            user_roles.insert().values(user_id=user.id, role_id=role.id)
        )
        await seeded_db_session.commit()

        # Refresh user with roles and permissions
        stmt = select(User).where(User.id == user.id).options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        result = await seeded_db_session.execute(stmt)
        user_with_roles = result.scalar_one()

        # Manager should have kol read permission
        assert user_with_roles.has_permission("kols.read")

    def test_user_primary_role_property(self):
        """Test getting primary role of user."""
        user = User(email="test@example.com", hashed_password="hash")

        # No roles
        assert user.primary_role is None

        # With roles
        role1 = Role(name="admin", display_name="Administrator")
        role2 = Role(name="user", display_name="User")
        user.roles = [role1, role2]

        assert user.primary_role == "admin"


class TestRoleModel:
    """Test cases for Role model."""

    @pytest.mark.asyncio
    async def test_create_role(self, db_session: AsyncSession):
        """Test creating a new role."""
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="A test role",
            level=50
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        assert role.id is not None
        assert role.name == "test_role"
        assert role.display_name == "Test Role"
        assert role.description == "A test role"
        assert role.level == 50
        assert role.is_active is True
        assert role.is_system_role is False

    @pytest.mark.asyncio
    async def test_role_permission_assignment(self, seeded_db_session: AsyncSession):
        """Test assigning permissions to role."""
        # Get role and permission
        role = await seeded_db_session.execute(
            select(Role).where(Role.name == "viewer")
        )
        role = role.scalar_one()

        permission = await seeded_db_session.execute(
            select(Permission).where(Permission.name == "kols.read")
        )
        permission = permission.scalar_one()

        # Assign permission to role
        await seeded_db_session.execute(
            role_permissions.insert().values(
                role_id=role.id,
                permission_id=permission.id
            )
        )
        await seeded_db_session.commit()

        # Check permission assignment
        stmt = select(Role).where(Role.id == role.id).options(
            selectinload(Role.permissions)
        )
        result = await seeded_db_session.execute(stmt)
        role_with_perms = result.scalar_one()

        assert role_with_perms.has_permission("kols.read")

    def test_role_has_permission_method(self):
        """Test role permission checking method."""
        role = Role(name="test_role")
        perm1 = Permission(name="test.read")
        perm2 = Permission(name="test.write")

        role.permissions = [perm1]

        assert role.has_permission("test.read")
        assert not role.has_permission("test.write")


class TestPermissionModel:
    """Test cases for Permission model."""

    @pytest.mark.asyncio
    async def test_create_permission(self, db_session: AsyncSession):
        """Test creating a new permission."""
        permission = Permission(
            name="test.action",
            display_name="Test Action",
            description="Test permission",
            resource="test",
            action="action",
            scope="all"
        )
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)

        assert permission.id is not None
        assert permission.name == "test.action"
        assert permission.display_name == "Test Action"
        assert permission.resource == "test"
        assert permission.action == "action"
        assert permission.scope == "all"
        assert permission.is_active is True
        assert permission.is_system_permission is False


class TestUserSessionModel:
    """Test cases for UserSession model."""

    @pytest.mark.asyncio
    async def test_create_user_session(self, db_session: AsyncSession):
        """Test creating a user session."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        session = UserSession(
            session_id=security_service.create_session_id(),
            user_id=user.id,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            expires_at=datetime.utcnow() + timedelta(hours=8)
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert session.user_id == user.id
        assert session.status == SessionStatus.ACTIVE
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Test Browser"

    @pytest.mark.asyncio
    async def test_session_expiry_properties(self, db_session: AsyncSession):
        """Test session expiry properties."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        # Active session
        active_session = UserSession(
            session_id="active_session",
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        # Expired session
        expired_session = UserSession(
            session_id="expired_session",
            user_id=user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )

        db_session.add_all([active_session, expired_session])
        await db_session.commit()

        assert not active_session.is_expired
        assert active_session.is_active

        assert expired_session.is_expired
        assert not expired_session.is_active


class TestUserTokenModel:
    """Test cases for UserToken model."""

    @pytest.mark.asyncio
    async def test_create_user_token(self, db_session: AsyncSession):
        """Test creating a user token."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        token = UserToken(
            token=security_service.generate_secure_token(),
            user_id=user.id,
            token_type=TokenType.EMAIL_VERIFICATION,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            purpose="email_verification"
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.id is not None
        assert token.user_id == user.id
        assert token.token_type == TokenType.EMAIL_VERIFICATION
        assert token.purpose == "email_verification"
        assert token.is_active is True
        assert token.is_revoked is False

    @pytest.mark.asyncio
    async def test_token_validity_properties(self, db_session: AsyncSession):
        """Test token validity properties."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        # Valid token
        valid_token = UserToken(
            token="valid_token",
            user_id=user.id,
            token_type=TokenType.ACCESS,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        # Expired token
        expired_token = UserToken(
            token="expired_token",
            user_id=user.id,
            token_type=TokenType.ACCESS,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )

        # Revoked token
        revoked_token = UserToken(
            token="revoked_token",
            user_id=user.id,
            token_type=TokenType.ACCESS,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_revoked=True
        )

        db_session.add_all([valid_token, expired_token, revoked_token])
        await db_session.commit()

        assert valid_token.is_valid
        assert not valid_token.is_expired

        assert not expired_token.is_valid
        assert expired_token.is_expired

        assert not revoked_token.is_valid
        assert not revoked_token.is_expired


class TestAPIKeyModel:
    """Test cases for APIKey model."""

    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession):
        """Test creating an API key."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        key_id, api_key = security_service.generate_api_key()
        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=security_service.hash_api_key(api_key),
            user_id=user.id,
            name="Test API Key",
            description="API key for testing",
            scopes=["read", "write"],
            rate_limit=1000
        )
        db_session.add(api_key_obj)
        await db_session.commit()
        await db_session.refresh(api_key_obj)

        assert api_key_obj.id is not None
        assert api_key_obj.user_id == user.id
        assert api_key_obj.name == "Test API Key"
        assert api_key_obj.scopes == ["read", "write"]
        assert api_key_obj.rate_limit == 1000
        assert api_key_obj.is_active is True
        assert api_key_obj.is_revoked is False

    @pytest.mark.asyncio
    async def test_api_key_verification(self, db_session: AsyncSession):
        """Test API key verification."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        key_id, api_key = security_service.generate_api_key()
        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=security_service.hash_api_key(api_key),
            user_id=user.id,
            name="Test API Key"
        )
        db_session.add(api_key_obj)
        await db_session.commit()

        # Test correct API key
        assert security_service.verify_api_key(api_key, api_key_obj.key_hash)

        # Test incorrect API key
        assert not security_service.verify_api_key("wrong_key", api_key_obj.key_hash)

    @pytest.mark.asyncio
    async def test_api_key_validity_properties(self, db_session: AsyncSession):
        """Test API key validity properties."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        # Valid API key
        valid_key = APIKey(
            key_id="valid_key",
            key_hash="hash",
            user_id=user.id,
            name="Valid Key"
        )

        # Expired API key
        expired_key = APIKey(
            key_id="expired_key",
            key_hash="hash",
            user_id=user.id,
            name="Expired Key",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )

        # Revoked API key
        revoked_key = APIKey(
            key_id="revoked_key",
            key_hash="hash",
            user_id=user.id,
            name="Revoked Key",
            is_revoked=True
        )

        db_session.add_all([valid_key, expired_key, revoked_key])
        await db_session.commit()

        assert valid_key.is_valid
        assert not valid_key.is_expired

        assert not expired_key.is_valid
        assert expired_key.is_expired

        assert not revoked_key.is_valid
        assert not revoked_key.is_expired


class TestSecurityAuditLogModel:
    """Test cases for SecurityAuditLog model."""

    @pytest.mark.asyncio
    async def test_create_audit_log(self, db_session: AsyncSession):
        """Test creating a security audit log entry."""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        await db_session.flush()

        audit_log = SecurityAuditLog(
            user_id=user.id,
            event_type="login",
            event_category="authentication",
            action="authenticate",
            resource="user_account",
            details={"ip_address": "192.168.1.1", "user_agent": "Test Browser"},
            success=True,
            risk_level="low",
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)

        assert audit_log.id is not None
        assert audit_log.user_id == user.id
        assert audit_log.event_type == "login"
        assert audit_log.event_category == "authentication"
        assert audit_log.action == "authenticate"
        assert audit_log.resource == "user_account"
        assert audit_log.success is True
        assert audit_log.risk_level == "low"
        assert audit_log.details["ip_address"] == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_audit_log_without_user(self, db_session: AsyncSession):
        """Test creating audit log entry without associated user."""
        audit_log = SecurityAuditLog(
            event_type="failed_login",
            event_category="security",
            action="authenticate",
            resource="user_account",
            details={"attempted_email": "nonexistent@example.com"},
            success=False,
            risk_level="medium",
            ip_address="192.168.1.1"
        )
        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)

        assert audit_log.id is not None
        assert audit_log.user_id is None
        assert audit_log.event_type == "failed_login"
        assert audit_log.success is False