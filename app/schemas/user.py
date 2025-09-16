"""
User Pydantic V2 schemas for validation and serialization.
Handles user management, authentication, and audit logging with custom validators.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import re
from email_validator import validate_email, EmailNotValidError

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="Username")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    bio: Optional[str] = Field(None, max_length=1000, description="User biography")
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", description="User language")

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, v: str) -> str:
        """Validate email address format."""
        try:
            validate_email(v)
        except EmailNotValidError:
            raise ValueError("Invalid email address format")
        return v.lower()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format."""
        if v is None:
            return v

        # Username can only contain letters, numbers, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")

        # Cannot start or end with special characters
        if v.startswith(('_', '-')) or v.endswith(('_', '-')):
            raise ValueError("Username cannot start or end with underscores or hyphens")

        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v

        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone number must be between 10 and 15 digits")

        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone."""
        # Common timezones - in production, use pytz.all_timezones
        valid_timezones = {
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Bangkok", "Asia/Seoul",
            "Australia/Sydney", "America/New_York", "America/Los_Angeles"
        }

        if v not in valid_timezones:
            # Allow any valid timezone format for flexibility
            if not re.match(r'^[A-Za-z_/]+$', v):
                raise ValueError("Invalid timezone format")

        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        valid_languages = {
            "en", "th", "ja", "ko", "zh", "es", "fr", "de", "it", "pt", "ru",
            "ar", "hi", "bn", "ms", "id", "vi", "tl"
        }

        if v not in valid_languages:
            raise ValueError(f"Unsupported language: {v}")

        return v

    @computed_field
    @property
    def display_name(self) -> str:
        """Get display name."""
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip()


class NotificationSettings(BaseModel):
    """Schema for user notification settings."""
    email_notifications: bool = Field(True, description="Enable email notifications")
    browser_notifications: bool = Field(True, description="Enable browser notifications")
    sms_notifications: bool = Field(False, description="Enable SMS notifications")
    campaign_updates: bool = Field(True, description="Campaign update notifications")
    content_alerts: bool = Field(True, description="Content alert notifications")
    performance_reports: bool = Field(True, description="Performance report notifications")
    follow_up_reminders: bool = Field(True, description="Follow-up reminder notifications")
    weekly_summary: bool = Field(True, description="Weekly summary notifications")
    security_alerts: bool = Field(True, description="Security alert notifications")

    @field_validator("sms_notifications")
    @classmethod
    def validate_sms_notifications(cls, v: bool, info) -> bool:
        """Validate SMS notifications requirement."""
        # In real implementation, could check if phone number is provided
        return v


class UserPreferences(BaseModel):
    """Schema for user preferences."""
    dashboard_layout: str = Field("default", description="Dashboard layout preference")
    items_per_page: int = Field(20, ge=10, le=100, description="Items per page")
    date_format: str = Field("YYYY-MM-DD", description="Date format preference")
    time_format: str = Field("24h", description="Time format preference")
    theme: str = Field("light", description="UI theme preference")
    auto_refresh: bool = Field(True, description="Auto-refresh data")
    export_format: str = Field("xlsx", description="Default export format")

    @field_validator("dashboard_layout")
    @classmethod
    def validate_dashboard_layout(cls, v: str) -> str:
        """Validate dashboard layout."""
        valid_layouts = {"default", "compact", "detailed", "minimal"}
        if v not in valid_layouts:
            raise ValueError(f"Invalid dashboard layout: {v}")
        return v

    @field_validator("time_format")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format."""
        valid_formats = {"12h", "24h"}
        if v not in valid_formats:
            raise ValueError(f"Invalid time format: {v}")
        return v

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme."""
        valid_themes = {"light", "dark", "auto"}
        if v not in valid_themes:
            raise ValueError(f"Invalid theme: {v}")
        return v

    @field_validator("export_format")
    @classmethod
    def validate_export_format(cls, v: str) -> str:
        """Validate export format."""
        valid_formats = {"xlsx", "csv", "pdf", "json"}
        if v not in valid_formats:
            raise ValueError(f"Invalid export format: {v}")
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    role: UserRole = Field(UserRole.VIEWER, description="User role")
    permissions: List[str] = Field(default_factory=list, description="Specific permissions")
    notification_settings: NotificationSettings = Field(default_factory=NotificationSettings, description="Notification settings")
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")

        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")

        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")

        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: List[str]) -> List[str]:
        """Validate user permissions."""
        valid_permissions = {
            "manage_campaigns", "manage_kols", "manage_users", "view_analytics",
            "verify_content", "send_messages", "export_data", "manage_templates",
            "view_audit_logs", "manage_settings", "api_access", "bulk_operations"
        }

        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f"Invalid permission: {permission}")

        return v

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate avatar URL."""
        if v is None:
            return v

        # Basic URL validation
        if not re.match(r'^https?://', v):
            raise ValueError("Avatar URL must use http or https scheme")

        # Check file extension
        if not re.search(r'\.(jpg|jpeg|png|gif|webp)$', v.lower()):
            raise ValueError("Avatar must be an image file (jpg, jpeg, png, gif, webp)")

        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump(exclude={"password"})

        # Convert nested models to dict
        data["notification_settings"] = self.notification_settings.model_dump()
        data["preferences"] = self.preferences.model_dump()

        return data


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    model_config = ConfigDict(from_attributes=True)

    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None)
    language: Optional[str] = Field(None)
    role: Optional[UserRole] = Field(None)
    permissions: Optional[List[str]] = Field(None)
    status: Optional[UserStatus] = Field(None)
    notification_settings: Optional[NotificationSettings] = Field(None)
    preferences: Optional[UserPreferences] = Field(None)

    # Reuse validators from base class
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format."""
        if v is None:
            return v

        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")

        if v.startswith(('_', '-')) or v.endswith(('_', '-')):
            raise ValueError("Username cannot start or end with underscores or hyphens")

        return v.lower()


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: str, info) -> str:
        """Validate password confirmation matches."""
        if hasattr(info, "data") and "new_password" in info.data:
            if v != info.data["new_password"]:
                raise ValueError("Passwords do not match")
        return v


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: UserRole
    status: UserStatus
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    avatar_url: Optional[str] = None
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    two_factor_enabled: bool = False
    last_login_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    @computed_field
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    @computed_field
    @property
    def can_manage_campaigns(self) -> bool:
        """Check if user can manage campaigns."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER] or "manage_campaigns" in self.permissions

    @computed_field
    @property
    def can_manage_kols(self) -> bool:
        """Check if user can manage KOLs."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.COORDINATOR] or "manage_kols" in self.permissions

    @computed_field
    @property
    def can_view_analytics(self) -> bool:
        """Check if user can view analytics."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST] or "view_analytics" in self.permissions

    @computed_field
    @property
    def can_verify_content(self) -> bool:
        """Check if user can verify content."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.COORDINATOR] or "verify_content" in self.permissions

    @computed_field
    @property
    def days_since_last_login(self) -> Optional[int]:
        """Calculate days since last login."""
        if self.last_login_at:
            return (datetime.utcnow() - self.last_login_at).days
        return None

    @computed_field
    @property
    def account_age_days(self) -> int:
        """Calculate account age in days."""
        return (datetime.utcnow() - self.created_at).days


class UserSessionBase(BaseModel):
    """Base user session schema."""
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., gt=0, description="User ID")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=2000, description="User agent")

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP address format."""
        if v is None:
            return v

        # Basic IPv4/IPv6 validation
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Invalid IP address format")

        return v


class DeviceInfo(BaseModel):
    """Schema for device information."""
    device_type: Optional[str] = Field(None, description="Device type (desktop, mobile, tablet)")
    browser: Optional[str] = Field(None, description="Browser name")
    browser_version: Optional[str] = Field(None, description="Browser version")
    os: Optional[str] = Field(None, description="Operating system")
    os_version: Optional[str] = Field(None, description="OS version")
    screen_resolution: Optional[str] = Field(None, description="Screen resolution")


class UserSessionCreate(UserSessionBase):
    """Schema for creating a user session."""
    session_token: str = Field(..., min_length=32, description="Session token")
    refresh_token: Optional[str] = Field(None, min_length=32, description="Refresh token")
    device_info: Optional[DeviceInfo] = Field(None, description="Device information")
    expires_at: datetime = Field(..., description="Session expiration time")

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, v: datetime) -> datetime:
        """Validate session expiration."""
        if v <= datetime.utcnow():
            raise ValueError("Session expiration must be in the future")

        # Maximum session duration is 30 days
        max_expiration = datetime.utcnow() + timedelta(days=30)
        if v > max_expiration:
            raise ValueError("Session duration cannot exceed 30 days")

        return v


class UserSessionResponse(UserSessionBase):
    """Schema for user session response."""
    id: int
    session_token: str
    refresh_token: Optional[str] = None
    device_info: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_active: bool = True
    terminated_at: Optional[datetime] = None
    termination_reason: Optional[str] = None

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return self.expires_at < datetime.utcnow()

    @computed_field
    @property
    def time_until_expiry(self) -> Optional[timedelta]:
        """Calculate time until session expires."""
        if not self.is_expired:
            return self.expires_at - datetime.utcnow()
        return None


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    resource_type: str = Field(..., min_length=1, max_length=100, description="Resource type")
    resource_id: Optional[str] = Field(None, max_length=100, description="Resource ID")
    description: str = Field(..., min_length=1, max_length=2000, description="Action description")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=2000, description="User agent")
    request_id: Optional[str] = Field(None, max_length=100, description="Request ID")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action."""
        valid_actions = {
            "create", "read", "update", "delete", "login", "logout",
            "password_change", "role_change", "permission_grant", "permission_revoke",
            "verify", "reject", "approve", "cancel", "export", "import"
        }

        if v not in valid_actions:
            # Allow any action for flexibility, but warn
            pass

        return v.lower()

    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        """Validate resource type."""
        valid_types = {
            "user", "kol", "campaign", "brief", "message", "content_post",
            "template", "follow_up", "alert", "session", "settings"
        }

        if v not in valid_types:
            # Allow any resource type for flexibility
            pass

        return v.lower()


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log."""
    user_id: Optional[int] = Field(None, gt=0, description="User ID")
    old_values: Dict[str, Any] = Field(default_factory=dict, description="Old values")
    new_values: Dict[str, Any] = Field(default_factory=dict, description="New values")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    id: int
    user_id: Optional[int] = None
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @computed_field
    @property
    def age_hours(self) -> float:
        """Calculate log age in hours."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600


class UserSearchCriteria(BaseModel):
    """Schema for user search criteria."""
    roles: Optional[List[UserRole]] = Field(None, description="Filter by roles")
    statuses: Optional[List[UserStatus]] = Field(None, description="Filter by statuses")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")
    created_after: Optional[datetime] = Field(None, description="Users created after date")
    created_before: Optional[datetime] = Field(None, description="Users created before date")
    last_login_after: Optional[datetime] = Field(None, description="Last login after date")
    has_permissions: Optional[List[str]] = Field(None, description="Filter by permissions")

    # Sorting and pagination
    sort_by: str = Field("created_at", description="Sort field")
    sort_desc: bool = Field(True, description="Sort in descending order")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

    @computed_field
    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.per_page

    @computed_field
    @property
    def limit(self) -> int:
        """Get limit for pagination."""
        return self.per_page


class UserSearchResult(BaseModel):
    """Schema for user search results."""
    users: List[UserResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    search_criteria: UserSearchCriteria

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_count + self.per_page - 1) // self.per_page