"""
Authentication and Authorization Models

Database models for user authentication, authorization, and security including:
- User accounts and profiles
- Role-based access control (RBAC)
- API keys and tokens
- Authentication sessions
- Security audit logs
- Permission management
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    KOL = "kol"
    CLIENT = "client"


class UserStatus(str, enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class TokenType(str, enum.Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALID = "invalid"


# Association table for user roles (many-to-many)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', Integer, ForeignKey('users.id')),
    Column('expires_at', DateTime, nullable=True)
)

# Association table for role permissions (many-to-many)
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow),
    Column('granted_by', Integer, ForeignKey('users.id'))
)


class User(Base):
    """
    User model for authentication and profile management.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)

    # Basic Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    phone_number = Column(String(20))

    # Status and Settings
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # Profile Information
    avatar_url = Column(String(500))
    bio = Column(Text)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")

    # Security Settings
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(100))
    password_reset_required = Column(Boolean, default=False)
    last_password_change = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    email_verified_at = Column(DateTime)

    # Additional Data
    preferences = Column(JSONB, default=dict)
    metadata = Column(JSONB, default=dict)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("SecurityAuditLog", back_populates="user")

    # KOL relationship (if user is a KOL)
    kol_profile = relationship("KOL", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', status='{self.status}')>"

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        return self.locked_until and self.locked_until > datetime.utcnow()

    @property
    def primary_role(self) -> Optional[str]:
        """Get the primary role of the user."""
        if self.roles:
            return self.roles[0].name
        return None

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False


class Role(Base):
    """
    Role model for role-based access control.
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)

    # Status and Settings
    is_active = Column(Boolean, default=True)
    is_system_role = Column(Boolean, default=False)

    # Hierarchy
    level = Column(Integer, default=0)  # For role hierarchy
    parent_role_id = Column(Integer, ForeignKey('roles.id'))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    parent_role = relationship("Role", remote_side=[id])
    child_roles = relationship("Role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        return any(perm.name == permission_name for perm in self.permissions)


class Permission(Base):
    """
    Permission model for fine-grained access control.
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)

    # Permission Details
    resource = Column(String(100))  # e.g., 'campaigns', 'kols', 'analytics'
    action = Column(String(50))     # e.g., 'create', 'read', 'update', 'delete'
    scope = Column(String(50))      # e.g., 'own', 'team', 'all'

    # Status
    is_active = Column(Boolean, default=True)
    is_system_permission = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"


class UserSession(Base):
    """
    User session model for tracking active sessions.
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Session Details
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_info = Column(JSONB, default=dict)
    location = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    terminated_at = Column(DateTime)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, status='{self.status}')>"

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired


class UserToken(Base):
    """
    User token model for various authentication tokens.
    """
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    token_hash = Column(String(255), index=True)  # Hashed version for security
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Token Details
    token_type = Column(SQLEnum(TokenType), nullable=False)
    purpose = Column(String(100))  # Additional purpose description

    # Status and Validity
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    revoked_at = Column(DateTime)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, type='{self.token_type}')>"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid and usable."""
        return self.is_active and not self.is_revoked and not self.is_expired


class APIKey(Base):
    """
    API Key model for API authentication.
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(100), unique=True, index=True, nullable=False)
    key_hash = Column(String(255), nullable=False)  # Hashed API key
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # API Key Details
    name = Column(String(200))
    description = Column(Text)
    scopes = Column(JSONB, default=list)  # List of allowed scopes/permissions

    # Status and Limits
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    revoked_at = Column(DateTime)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, key_id='{self.key_id}', user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        return self.expires_at and datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid and usable."""
        return self.is_active and not self.is_revoked and not self.is_expired


class SecurityAuditLog(Base):
    """
    Security audit log model for tracking security events.
    """
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Event Details
    event_type = Column(String(100), nullable=False)  # login, logout, permission_change, etc.
    event_category = Column(String(50))  # authentication, authorization, security
    action = Column(String(100))
    resource = Column(String(100))

    # Event Data
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Status and Risk
    success = Column(Boolean, default=True)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<SecurityAuditLog(id={self.id}, event_type='{self.event_type}', user_id={self.user_id})>"


class OAuth2Client(Base):
    """
    OAuth2 client model for third-party integrations.
    """
    __tablename__ = "oauth2_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(100), unique=True, index=True, nullable=False)
    client_secret_hash = Column(String(255), nullable=False)

    # Client Details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    logo_url = Column(String(500))
    website_url = Column(String(500))

    # OAuth2 Configuration
    redirect_uris = Column(JSONB, default=list)
    allowed_scopes = Column(JSONB, default=list)
    grant_types = Column(JSONB, default=list)  # authorization_code, client_credentials, etc.

    # Status
    is_active = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional Data
    metadata = Column(JSONB, default=dict)

    def __repr__(self):
        return f"<OAuth2Client(id={self.id}, client_id='{self.client_id}', name='{self.name}')>"


class OAuth2AuthorizationCode(Base):
    """
    OAuth2 authorization code model.
    """
    __tablename__ = "oauth2_authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, index=True, nullable=False)
    client_id = Column(String(100), ForeignKey('oauth2_clients.client_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Authorization Details
    redirect_uri = Column(String(500), nullable=False)
    scopes = Column(JSONB, default=list)
    code_challenge = Column(String(255))  # For PKCE
    code_challenge_method = Column(String(20))  # plain or S256

    # Status
    is_used = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)

    def __repr__(self):
        return f"<OAuth2AuthorizationCode(id={self.id}, client_id='{self.client_id}', user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if authorization code is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if authorization code is valid and usable."""
        return not self.is_used and not self.is_expired