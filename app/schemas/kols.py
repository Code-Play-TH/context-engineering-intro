"""
KOL Management Pydantic Schemas

Provides validation schemas for KOL-related API operations including:
- KOL profile creation and updates
- Social media account management
- Performance metrics and analytics
- Search and filtering parameters
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum


class KOLStatus(str, Enum):
    """KOL status enumeration."""
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SocialPlatform(str, Enum):
    """Social media platform enumeration."""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITCH = "twitch"


class CollaborationStatus(str, Enum):
    """Collaboration status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Social Account Schemas
class KOLSocialAccountBase(BaseModel):
    """Base schema for KOL social media accounts."""
    platform: SocialPlatform
    username: str = Field(..., min_length=1, max_length=100)
    profile_url: Optional[str] = Field(None, max_length=500)
    follower_count: Optional[int] = Field(None, ge=0)
    is_verified: bool = False
    is_primary: bool = False


class KOLSocialAccountCreate(KOLSocialAccountBase):
    """Schema for creating KOL social media accounts."""
    pass


class KOLSocialAccountUpdate(BaseModel):
    """Schema for updating KOL social media accounts."""
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_url: Optional[str] = Field(None, max_length=500)
    follower_count: Optional[int] = Field(None, ge=0)
    is_verified: Optional[bool] = None
    is_primary: Optional[bool] = None


class KOLSocialAccountResponse(KOLSocialAccountBase):
    """Schema for KOL social media account responses."""
    id: int
    kol_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Core KOL Schemas
class KOLBase(BaseModel):
    """Base schema for KOL profiles."""
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    primary_platform: SocialPlatform
    bio: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    languages: Optional[List[str]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)


class KOLCreate(KOLBase):
    """Schema for creating KOL profiles."""
    follower_counts: Optional[Dict[str, int]] = Field(default_factory=dict)
    engagement_rates: Optional[Dict[str, float]] = Field(default_factory=dict)
    pricing: Optional[Dict[str, Any]] = Field(default_factory=dict)
    social_accounts: Optional[List[KOLSocialAccountCreate]] = Field(default_factory=list)


class KOLUpdate(BaseModel):
    """Schema for updating KOL profiles."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    primary_platform: Optional[SocialPlatform] = None
    bio: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    languages: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    follower_counts: Optional[Dict[str, int]] = None
    engagement_rates: Optional[Dict[str, float]] = None
    pricing: Optional[Dict[str, Any]] = None
    status: Optional[KOLStatus] = None


class KOLResponse(KOLBase):
    """Schema for KOL profile responses."""
    id: int
    status: KOLStatus
    follower_counts: Dict[str, int]
    engagement_rates: Dict[str, float]
    pricing: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    social_accounts: Optional[List[KOLSocialAccountResponse]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Search and Filter Schemas
class KOLSearchFilters(BaseModel):
    """Schema for KOL search and filtering parameters."""
    search: Optional[str] = Field(None, description="Search term for name, email, or bio")
    status: Optional[List[KOLStatus]] = Field(None, description="Filter by status")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    primary_platform: Optional[List[SocialPlatform]] = Field(None, description="Filter by platform")
    location: Optional[str] = Field(None, description="Filter by location")
    languages: Optional[List[str]] = Field(None, description="Filter by languages")
    min_followers: Optional[int] = Field(None, ge=0, description="Minimum follower count")
    max_followers: Optional[int] = Field(None, ge=0, description="Maximum follower count")
    min_engagement_rate: Optional[float] = Field(None, ge=0, le=100, description="Minimum engagement rate")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# List Response Schema
class KOLListResponse(BaseModel):
    """Schema for paginated KOL list responses."""
    kols: List[KOLResponse]
    total: int
    page: int
    limit: int
    pages: int


# Performance and Analytics Schemas
class KOLCollaborationHistory(BaseModel):
    """Schema for KOL collaboration history."""
    id: int
    campaign_id: int
    campaign_name: Optional[str] = None
    status: CollaborationStatus
    compensation_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KOLPerformanceMetrics(BaseModel):
    """Schema for KOL performance metrics."""
    avg_engagement_rate: float = Field(ge=0, le=100)
    avg_reach: int = Field(ge=0)
    total_campaigns: int = Field(ge=0)
    successful_campaigns: int = Field(ge=0)
    reliability_score: float = Field(ge=0, le=100)
    last_updated: Optional[datetime] = None


class KOLPerformanceResponse(KOLPerformanceMetrics):
    """Schema for KOL performance response."""
    kol_id: int
    collaboration_history: List[KOLCollaborationHistory] = Field(default_factory=list)


# Bulk Operations Schemas
class KOLBulkUpdate(BaseModel):
    """Schema for bulk KOL updates."""
    kol_ids: List[int] = Field(..., min_length=1)
    updates: KOLUpdate


class KOLBulkUpdateResponse(BaseModel):
    """Schema for bulk update response."""
    success_count: int
    failed_count: int
    failed_kols: List[Dict[str, Any]] = Field(default_factory=list)


# Import/Export Schemas
class KOLImportData(BaseModel):
    """Schema for KOL data import."""
    kols: List[KOLCreate] = Field(..., min_length=1)
    skip_duplicates: bool = True
    update_existing: bool = False


class KOLImportResponse(BaseModel):
    """Schema for KOL import response."""
    imported_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class KOLExportFilters(BaseModel):
    """Schema for KOL export filtering."""
    status: Optional[List[KOLStatus]] = None
    categories: Optional[List[str]] = None
    primary_platform: Optional[List[SocialPlatform]] = None
    date_range: Optional[Dict[str, datetime]] = None
    include_performance_data: bool = False
    include_social_accounts: bool = True


# Analytics and Reporting Schemas
class KOLAnalyticsRequest(BaseModel):
    """Schema for KOL analytics requests."""
    kol_ids: Optional[List[int]] = None
    date_range: Dict[str, datetime]
    metrics: List[str] = Field(default_factory=lambda: ["engagement", "reach", "growth"])
    group_by: Optional[str] = Field(None, pattern="^(platform|category|month|week)$")


class KOLAnalyticsResponse(BaseModel):
    """Schema for KOL analytics response."""
    kol_count: int
    date_range: Dict[str, datetime]
    metrics: Dict[str, Any]
    trends: Dict[str, Any]
    comparisons: Dict[str, Any]
    generated_at: datetime


class KOLEngagementTrend(BaseModel):
    """Schema for KOL engagement trend data."""
    date: datetime
    engagement_rate: float
    reach: int
    impressions: int
    platform: SocialPlatform


class KOLPlatformComparison(BaseModel):
    """Schema for KOL platform performance comparison."""
    platform: SocialPlatform
    follower_count: int
    engagement_rate: float
    avg_reach: int
    content_count: int
    performance_score: float


class KOLDetailedAnalytics(BaseModel):
    """Schema for detailed KOL analytics."""
    kol_id: int
    period_start: datetime
    period_end: datetime
    engagement_trends: List[KOLEngagementTrend]
    platform_comparison: List[KOLPlatformComparison]
    top_content: List[Dict[str, Any]]
    growth_metrics: Dict[str, float]
    recommendations: List[str]


# Validation and Verification Schemas
class KOLVerificationRequest(BaseModel):
    """Schema for KOL verification requests."""
    kol_id: int
    verification_type: str = Field(pattern="^(identity|social_accounts|performance)$")
    documents: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)


class KOLVerificationResponse(BaseModel):
    """Schema for KOL verification response."""
    verification_id: int
    status: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    notes: Optional[str] = None


# Communication and Outreach Schemas
class KOLContactInfo(BaseModel):
    """Schema for KOL contact information."""
    email: EmailStr
    phone: Optional[str] = None
    preferred_contact_method: str = Field(default="email")
    time_zone: Optional[str] = None
    available_hours: Optional[Dict[str, Any]] = None


class KOLOutreachTemplate(BaseModel):
    """Schema for KOL outreach templates."""
    template_name: str
    subject: str
    content: str
    variables: List[str] = Field(default_factory=list)
    channel: str = Field(pattern="^(email|discord|line|whatsapp)$")


class KOLOutreachRequest(BaseModel):
    """Schema for KOL outreach requests."""
    kol_ids: List[int] = Field(..., min_length=1)
    template_id: Optional[int] = None
    custom_message: Optional[str] = None
    channel: str = Field(pattern="^(email|discord|line|whatsapp)$")
    scheduled_at: Optional[datetime] = None
    personalization_data: Optional[Dict[str, Any]] = None


class KOLOutreachResponse(BaseModel):
    """Schema for KOL outreach response."""
    campaign_id: str
    total_kols: int
    messages_scheduled: int
    failed_messages: int
    scheduled_at: Optional[datetime] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)