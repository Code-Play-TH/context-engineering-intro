"""
Authentication and Authorization Pydantic Schemas

Provides validation schemas for authentication and security operations including:
- User registration and authentication
- JWT token management
- Role-based access control
- API key management
- Session management
- OAuth2 integration
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict, validator
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    KOL = "kol"
    CLIENT = "client"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class TokenType(str, Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"


class SessionStatus(str, Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALID = "invalid"


# Base Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=200, description="Full name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=1000, description="User bio")
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", description="Preferred language")


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    phone_number: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    timezone: Optional[str] = None
    language: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    uuid: str
    status: UserStatus
    is_active: bool
    is_verified: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    two_factor_enabled: bool
    primary_role: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    """Schema for detailed user profile."""
    id: int
    uuid: str
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str
    language: str
    status: UserStatus
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Authentication Schemas
class LoginRequest(BaseModel):
    """Schema for login requests."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Remember login session")
    two_factor_code: Optional[str] = Field(None, description="Two-factor authentication code")


class LoginResponse(BaseModel):
    """Schema for login responses."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until token expires
    user: UserResponse
    session_id: str
    requires_two_factor: bool = False


class TokenResponse(BaseModel):
    """Schema for token responses."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token requests."""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests."""
    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseModel):
    """Schema for email verification requests."""
    email: EmailStr = Field(..., description="Email to verify")


class EmailVerificationConfirm(BaseModel):
    """Schema for email verification confirmation."""
    token: str = Field(..., description="Verification token")


class TwoFactorSetupResponse(BaseModel):
    """Schema for two-factor authentication setup."""
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class TwoFactorConfirmRequest(BaseModel):
    """Schema for two-factor authentication confirmation."""
    code: str = Field(..., description="Two-factor authentication code")


# Role and Permission Schemas
class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., description="Permission name")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Permission description")
    resource: Optional[str] = Field(None, description="Resource type")
    action: Optional[str] = Field(None, description="Action type")
    scope: Optional[str] = Field(None, description="Permission scope")


class PermissionCreate(PermissionBase):
    """Schema for permission creation."""
    is_system_permission: bool = Field(False, description="System permission flag")


class PermissionResponse(PermissionBase):
    """Schema for permission responses."""
    id: int
    is_active: bool
    is_system_permission: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., description="Role name")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Role description")
    level: int = Field(0, description="Role hierarchy level")


class RoleCreate(RoleBase):
    """Schema for role creation."""
    parent_role_id: Optional[int] = Field(None, description="Parent role ID")
    permission_ids: List[int] = Field(default_factory=list, description="Permission IDs")
    is_system_role: bool = Field(False, description="System role flag")


class RoleUpdate(BaseModel):
    """Schema for role updates."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None
    parent_role_id: Optional[int] = None
    permission_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    """Schema for role responses."""
    id: int
    is_active: bool
    is_system_role: bool
    parent_role_id: Optional[int] = None
    permissions: List[PermissionResponse] = Field(default_factory=list)
    user_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleAssignment(BaseModel):
    """Schema for user role assignment."""
    user_id: int
    role_ids: List[int]
    expires_at: Optional[datetime] = None


# Session Management Schemas
class SessionResponse(BaseModel):
    """Schema for session responses."""
    id: int
    session_id: str
    status: SessionStatus
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Dict[str, Any] = Field(default_factory=dict)
    location: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False

    model_config = ConfigDict(from_attributes=True)


class SessionTerminateRequest(BaseModel):
    """Schema for session termination."""
    session_id: Optional[str] = Field(None, description="Specific session to terminate")
    terminate_all: bool = Field(False, description="Terminate all sessions")


# API Key Management Schemas
class APIKeyCreate(BaseModel):
    """Schema for API key creation."""
    name: str = Field(..., min_length=1, max_length=200, description="API key name")
    description: Optional[str] = Field(None, max_length=1000, description="API key description")
    scopes: List[str] = Field(default_factory=list, description="API key scopes")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    rate_limit: int = Field(1000, ge=1, le=10000, description="Rate limit per hour")


class APIKeyResponse(BaseModel):
    """Schema for API key responses."""
    id: int
    key_id: str
    name: str
    description: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    is_active: bool
    is_revoked: bool
    rate_limit: int
    usage_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(APIKeyResponse):
    """Schema for API key creation response (includes the actual key)."""
    api_key: str  # Only returned once during creation


# Security Audit Schemas
class SecurityAuditLogResponse(BaseModel):
    """Schema for security audit log responses."""
    id: int
    user_id: Optional[int] = None
    event_type: str
    event_category: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    risk_level: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityAuditLogFilters(BaseModel):
    """Schema for security audit log filters."""
    user_id: Optional[int] = None
    event_type: Optional[str] = None
    event_category: Optional[str] = None
    risk_level: Optional[str] = None
    success: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    ip_address: Optional[str] = None


# OAuth2 Schemas
class OAuth2ClientCreate(BaseModel):
    """Schema for OAuth2 client creation."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    redirect_uris: List[str] = Field(..., min_items=1)
    allowed_scopes: List[str] = Field(default_factory=list)
    grant_types: List[str] = Field(default=["authorization_code"])
    is_trusted: bool = Field(False)


class OAuth2ClientResponse(BaseModel):
    """Schema for OAuth2 client responses."""
    id: int
    client_id: str
    name: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    redirect_uris: List[str]
    allowed_scopes: List[str]
    grant_types: List[str]
    is_active: bool
    is_trusted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OAuth2AuthorizeRequest(BaseModel):
    """Schema for OAuth2 authorization requests."""
    response_type: str = Field("code", description="Response type")
    client_id: str = Field(..., description="Client ID")
    redirect_uri: str = Field(..., description="Redirect URI")
    scope: Optional[str] = Field(None, description="Requested scopes")
    state: Optional[str] = Field(None, description="State parameter")
    code_challenge: Optional[str] = Field(None, description="PKCE code challenge")
    code_challenge_method: Optional[str] = Field(None, description="PKCE challenge method")


class OAuth2TokenRequest(BaseModel):
    """Schema for OAuth2 token requests."""
    grant_type: str = Field(..., description="Grant type")
    client_id: str = Field(..., description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret")
    code: Optional[str] = Field(None, description="Authorization code")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier")


class OAuth2TokenResponse(BaseModel):
    """Schema for OAuth2 token responses."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


# User Management Schemas
class UserListFilters(BaseModel):
    """Schema for user list filters."""
    status: Optional[UserStatus] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search in name, email, username")
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None


class UserStatusUpdate(BaseModel):
    """Schema for user status updates."""
    status: UserStatus
    reason: Optional[str] = Field(None, description="Reason for status change")


class BulkUserAction(BaseModel):
    """Schema for bulk user actions."""
    user_ids: List[int] = Field(..., min_items=1)
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)


# Security Configuration Schemas
class SecuritySettings(BaseModel):
    """Schema for security settings."""
    password_min_length: int = Field(8, ge=6, le=128)
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = False
    password_max_age_days: int = Field(90, ge=0, le=365)
    session_timeout_minutes: int = Field(480, ge=5, le=1440)  # 8 hours default
    max_failed_login_attempts: int = Field(5, ge=1, le=20)
    lockout_duration_minutes: int = Field(30, ge=1, le=1440)
    require_two_factor: bool = False
    allow_multiple_sessions: bool = True
    api_key_default_expiry_days: int = Field(365, ge=1, le=3650)


class SecurityStatsResponse(BaseModel):
    """Schema for security statistics."""
    total_users: int
    active_users: int
    locked_users: int
    failed_logins_24h: int
    successful_logins_24h: int
    active_sessions: int
    active_api_keys: int
    security_events_24h: int
    high_risk_events_24h: int
    generated_at: datetime