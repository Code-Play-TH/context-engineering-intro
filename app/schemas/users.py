"""
User Management Pydantic Schemas

Provides validation schemas for user-related API operations including:
- User profile creation and updates
- User role and permission management
- User status management
- Search and filtering parameters
- Analytics and reporting
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum

from app.models.user import UserRole, UserStatus


class UserSearchFilters(BaseModel):
    """Schema for user search and filtering parameters."""
    search: Optional[str] = Field(None, description="Search term for name, email, or username")
    status: Optional[List[UserStatus]] = Field(None, description="Filter by status")
    role: Optional[List[UserRole]] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date (after)")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date (before)")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# Core User Schemas
class UserBase(BaseModel):
    """Base schema for user profiles."""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)


class UserCreate(UserBase):
    """Schema for creating user profiles."""
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = Field(UserRole.VIEWER)
    status: Optional[UserStatus] = Field(UserStatus.ACTIVE)
    is_active: Optional[bool] = Field(True)
    is_verified: Optional[bool] = Field(False)
    permissions: Optional[List[str]] = Field(default_factory=list)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserUpdate(BaseModel):
    """Schema for updating user profiles."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    permissions: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user profile responses."""
    id: int
    role: UserRole
    status: UserStatus
    is_active: bool
    is_verified: bool
    is_superuser: bool = False
    avatar_url: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    two_factor_enabled: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Session Management Schemas
class UserSessionResponse(BaseModel):
    """Schema for user session responses."""
    id: int
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Dict[str, Any] = Field(default_factory=dict)
    location: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_active: bool
    terminated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Audit Log Schemas
class UserAuditLogResponse(BaseModel):
    """Schema for user audit log responses."""
    id: int
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Detailed User Response
class UserDetailedResponse(UserResponse):
    """Schema for detailed user responses with additional data."""
    recent_sessions: List[UserSessionResponse] = Field(default_factory=list)
    recent_audit_logs: List[UserAuditLogResponse] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# List Response Schema
class UserListResponse(BaseModel):
    """Schema for paginated user list responses."""
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    pages: int


# Status and Role Management Schemas
class UserStatusUpdate(BaseModel):
    """Schema for updating user status."""
    status: UserStatus
    is_active: bool
    reason: Optional[str] = Field(None, max_length=500)
    suspension_expires_at: Optional[datetime] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role."""
    role: UserRole
    permissions: Optional[List[str]] = None
    reason: Optional[str] = Field(None, max_length=500)


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    preferences: Dict[str, Any]


# Bulk Operations Schemas
class UserBulkAction(BaseModel):
    """Schema for bulk user actions."""
    user_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(activate|deactivate|suspend|verify|unverify)$")
    reason: Optional[str] = Field(None, max_length=500)


class UserBulkActionResponse(BaseModel):
    """Schema for bulk action response."""
    success_count: int
    failed_count: int
    failed_users: List[Dict[str, Any]] = Field(default_factory=list)
    updated_users: List[int] = Field(default_factory=list)


# Analytics Schemas
class UserAnalytics(BaseModel):
    """Schema for user analytics response."""
    total_users: int
    active_users: int
    verified_users: int
    status_distribution: Dict[str, int]
    role_distribution: Dict[str, int]
    recent_registrations: int
    generated_at: datetime


class UserRegistrationTrend(BaseModel):
    """Schema for user registration trend data."""
    date: datetime
    new_users: int
    total_users: int


class UserActivityStats(BaseModel):
    """Schema for user activity statistics."""
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    average_session_duration: float
    total_sessions: int


class UserEngagementMetrics(BaseModel):
    """Schema for user engagement metrics."""
    login_frequency: Dict[str, int]
    feature_usage: Dict[str, int]
    session_patterns: Dict[str, Any]
    retention_rate: float


class UserDetailedAnalytics(BaseModel):
    """Schema for detailed user analytics."""
    period_start: datetime
    period_end: datetime
    registration_trends: List[UserRegistrationTrend]
    activity_stats: UserActivityStats
    engagement_metrics: UserEngagementMetrics
    user_segments: Dict[str, int]
    churn_analysis: Dict[str, Any]


# Permission and Role Schemas
class PermissionResponse(BaseModel):
    """Schema for permission responses."""
    name: str
    description: str
    category: str


class RoleResponse(BaseModel):
    """Schema for role responses."""
    name: str
    description: str
    permissions: List[PermissionResponse]
    is_system_role: bool = False


class UserPermissionCheck(BaseModel):
    """Schema for checking user permissions."""
    user_id: int
    permission: str


class UserPermissionResponse(BaseModel):
    """Schema for permission check response."""
    has_permission: bool
    granted_by: Optional[str] = None  # role or direct permission


# Password Management Schemas
class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8)


# Import/Export Schemas
class UserImportData(BaseModel):
    """Schema for user data import."""
    users: List[UserCreate] = Field(..., min_length=1)
    skip_duplicates: bool = True
    send_welcome_emails: bool = False


class UserImportResponse(BaseModel):
    """Schema for user import response."""
    imported_count: int
    skipped_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class UserExportFilters(BaseModel):
    """Schema for user export filtering."""
    status: Optional[List[UserStatus]] = None
    role: Optional[List[UserRole]] = None
    date_range: Optional[Dict[str, datetime]] = None
    include_sessions: bool = False
    include_audit_logs: bool = False


# Notification and Communication Schemas
class UserNotificationPreferences(BaseModel):
    """Schema for user notification preferences."""
    email_notifications: bool = True
    browser_notifications: bool = True
    sms_notifications: bool = False
    campaign_updates: bool = True
    content_alerts: bool = True
    performance_reports: bool = True
    security_alerts: bool = True


class UserCommunicationLog(BaseModel):
    """Schema for user communication log."""
    id: int
    user_id: int
    type: str  # email, sms, push, etc.
    channel: str
    subject: Optional[str] = None
    content: str
    status: str  # sent, delivered, failed, read
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)