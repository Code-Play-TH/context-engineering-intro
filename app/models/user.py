"""
User and authentication database models.
Handles user management, roles, and audit logging.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum
from passlib.context import CryptContext

from app.core.database import Base

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(PyEnum):
    """User role enumeration."""
    ADMIN = "admin"
    MANAGER = "manager"
    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserStatus(PyEnum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """
    User model for authentication and role-based access control.
    """
    __tablename__ = "users"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Role and permissions
    role: Mapped[UserRole] = mapped_column(String(50), nullable=False, default=UserRole.VIEWER, index=True)
    permissions: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Specific permissions for this user"
    )

    # Status and metadata
    status: Mapped[UserStatus] = mapped_column(String(50), nullable=False, default=UserStatus.ACTIVE, index=True)

    # Profile information
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Preferences and settings
    preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="User preferences and settings"
    )

    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    # Notification settings
    notification_settings: Mapped[Dict[str, bool]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "email_notifications": True,
            "browser_notifications": True,
            "sms_notifications": False,
            "campaign_updates": True,
            "content_alerts": True,
            "performance_reports": True
        },
        comment="Notification preferences"
    )

    # Security and session management
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Two-factor authentication
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Account verification
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    created_campaigns = relationship(
        "Campaign",
        foreign_keys="Campaign.created_by",
        back_populates="creator"
    )

    created_briefs = relationship(
        "Brief",
        foreign_keys="Brief.created_by",
        back_populates="creator"
    )

    approved_briefs = relationship(
        "Brief",
        foreign_keys="Brief.approved_by",
        back_populates="approver"
    )

    created_messages = relationship(
        "Message",
        foreign_keys="Message.created_by",
        back_populates="creator"
    )

    verified_content = relationship(
        "ContentPost",
        foreign_keys="ContentPost.verified_by",
        back_populates="verifier"
    )

    creator = relationship("User", remote_side=[id])

    def set_password(self, password: str) -> None:
        """Set user password with proper hashing."""
        self.hashed_password = pwd_context.hash(password)
        self.password_changed_at = datetime.utcnow()

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return pwd_context.verify(password, self.hashed_password)

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Admin has all permissions
        if self.role == UserRole.ADMIN:
            return True

        # Check specific permissions
        return permission in self.permissions

    def can_manage_campaigns(self) -> bool:
        """Check if user can manage campaigns."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER] or self.has_permission("manage_campaigns")

    def can_manage_kols(self) -> bool:
        """Check if user can manage KOLs."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.COORDINATOR] or self.has_permission("manage_kols")

    def can_view_analytics(self) -> bool:
        """Check if user can view analytics."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST] or self.has_permission("view_analytics")

    def can_verify_content(self) -> bool:
        """Check if user can verify content."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.COORDINATOR] or self.has_permission("verify_content")

    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER] or self.has_permission("manage_users")

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN or self.is_superuser

    def set_password(self, password: str) -> None:
        """Set user password (hashed)."""
        self.hashed_password = pwd_context.hash(password)

    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip()

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    def generate_reset_token(self) -> str:
        """Generate password reset token."""
        import secrets
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        return token

    def clear_reset_token(self) -> None:
        """Clear password reset token."""
        self.reset_token = None
        self.reset_token_expires_at = None

    def is_reset_token_valid(self, token: str) -> bool:
        """Check if reset token is valid."""
        return (
            self.reset_token == token and
            self.reset_token_expires_at and
            self.reset_token_expires_at > datetime.utcnow()
        )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class UserSession(Base):
    """
    User session model for tracking active sessions.
    """
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Session identification
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_info: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Session timing
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    terminated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    termination_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user = relationship("User")

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return self.expires_at < datetime.utcnow()

    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration."""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity_at = datetime.utcnow()

    def terminate(self, reason: str = "manual") -> None:
        """Terminate the session."""
        self.is_active = False
        self.terminated_at = datetime.utcnow()
        self.termination_reason = reason

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class AuditLog(Base):
    """
    Audit log model for tracking all user actions.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # Action information
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Action details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    old_values: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    new_values: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Additional context
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"


# Indexes for performance optimization
Index("idx_user_email_status", User.email, User.status)
Index("idx_user_role_status", User.role, User.status)
Index("idx_user_created_role", User.created_at, User.role)

Index("idx_session_user_active", UserSession.user_id, UserSession.is_active)
Index("idx_session_token_active", UserSession.session_token, UserSession.is_active)
Index("idx_session_expires_active", UserSession.expires_at, UserSession.is_active)

Index("idx_audit_user_action", AuditLog.user_id, AuditLog.action)
Index("idx_audit_resource_created", AuditLog.resource_type, AuditLog.resource_id, AuditLog.created_at)
Index("idx_audit_action_created", AuditLog.action, AuditLog.created_at)