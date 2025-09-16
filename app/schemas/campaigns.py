"""
Campaign Management Pydantic Schemas

Provides validation schemas for campaign-related API operations including:
- Campaign creation and management
- Campaign brief generation and templates
- KOL collaboration management
- Content management and approval workflows
- Campaign analytics and reporting
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELETED = "deleted"


class CollaborationStatus(str, Enum):
    """Collaboration status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ContentStatus(str, Enum):
    """Content status enumeration."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class CompensationModel(str, Enum):
    """Compensation model enumeration."""
    FIXED_FEE = "fixed_fee"
    PER_POST = "per_post"
    PERFORMANCE_BASED = "performance_based"
    REVENUE_SHARE = "revenue_share"
    PRODUCT_GIFTING = "product_gifting"
    HYBRID = "hybrid"


class SocialPlatform(str, Enum):
    """Social media platform enumeration."""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITCH = "twitch"


class ContentType(str, Enum):
    """Content type enumeration."""
    POST = "post"
    STORY = "story"
    VIDEO = "video"
    REEL = "reel"
    LIVE = "live"
    ARTICLE = "article"
    PODCAST = "podcast"


# Core Campaign Schemas
class CampaignBase(BaseModel):
    """Base schema for campaigns."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    objectives: List[str] = Field(default_factory=list)
    target_audience: Optional[Dict[str, Any]] = Field(default_factory=dict)
    budget: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platforms: List[SocialPlatform] = Field(default_factory=list)


class CampaignCreate(CampaignBase):
    """Schema for creating campaigns."""
    content_requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    deliverables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    guidelines: Optional[Dict[str, Any]] = Field(default_factory=dict)
    target_reach: Optional[int] = Field(None, ge=0)
    target_engagement_rate: Optional[float] = Field(None, ge=0, le=100)
    compensation_model: Optional[CompensationModel] = None


class CampaignUpdate(BaseModel):
    """Schema for updating campaigns."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    objectives: Optional[List[str]] = None
    target_audience: Optional[Dict[str, Any]] = None
    budget: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platforms: Optional[List[SocialPlatform]] = None
    content_requirements: Optional[Dict[str, Any]] = None
    deliverables: Optional[Dict[str, Any]] = None
    guidelines: Optional[Dict[str, Any]] = None
    target_reach: Optional[int] = Field(None, ge=0)
    target_engagement_rate: Optional[float] = Field(None, ge=0, le=100)
    compensation_model: Optional[CompensationModel] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign responses."""
    id: int
    status: CampaignStatus
    content_requirements: Dict[str, Any]
    deliverables: Dict[str, Any]
    guidelines: Dict[str, Any]
    target_reach: Optional[int] = None
    target_engagement_rate: Optional[float] = None
    compensation_model: Optional[CompensationModel] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    total_reach: Optional[int] = None
    avg_engagement_rate: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Search and Filter Schemas
class CampaignSearchFilters(BaseModel):
    """Schema for campaign search and filtering."""
    search: Optional[str] = Field(None, description="Search term for name or description")
    status: Optional[List[CampaignStatus]] = Field(None, description="Filter by status")
    platforms: Optional[List[SocialPlatform]] = Field(None, description="Filter by platforms")
    budget_min: Optional[float] = Field(None, ge=0, description="Minimum budget")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    created_by: Optional[int] = Field(None, description="Filter by creator")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# List Response Schema
class CampaignListResponse(BaseModel):
    """Schema for paginated campaign list responses."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    limit: int
    pages: int


# Campaign Brief Schemas
class CampaignBriefBase(BaseModel):
    """Base schema for campaign briefs."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    timeline: Dict[str, Any] = Field(default_factory=dict)
    compensation: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CampaignBriefCreate(BaseModel):
    """Schema for campaign brief creation."""
    template_type: str = Field(..., description="Brief template type")
    target_kols: Optional[List[int]] = Field(None, description="Target KOL IDs")
    customization: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auto_send: bool = Field(False, description="Automatically send to KOLs")


class CampaignBriefUpdate(CampaignBriefBase):
    """Schema for updating campaign briefs."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None


class CampaignBriefResponse(CampaignBriefBase):
    """Schema for campaign brief responses."""
    id: int
    campaign_id: int
    kol_id: Optional[int] = None
    collaboration_id: Optional[int] = None
    status: str
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Collaboration Schemas
class CollaborationBase(BaseModel):
    """Base schema for collaborations."""
    compensation_amount: Optional[float] = Field(None, ge=0)
    compensation_type: Optional[str] = None
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    timeline: Dict[str, Any] = Field(default_factory=dict)


class CollaborationCreate(CollaborationBase):
    """Schema for creating collaborations."""
    kol_id: int = Field(..., description="KOL identifier")


class CollaborationUpdate(BaseModel):
    """Schema for updating collaborations."""
    compensation_amount: Optional[float] = Field(None, ge=0)
    compensation_type: Optional[str] = None
    deliverables: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    status: Optional[CollaborationStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    payment_status: Optional[str] = None


class CollaborationResponse(CollaborationBase):
    """Schema for collaboration responses."""
    id: int
    campaign_id: int
    kol_id: int
    status: CollaborationStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    payment_status: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_amount: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Content Management Schemas
class CampaignContentBase(BaseModel):
    """Base schema for campaign content."""
    platform: SocialPlatform
    content_type: ContentType
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    content_url: Optional[str] = Field(None, max_length=500)
    media_urls: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)


class CampaignContentCreate(CampaignContentBase):
    """Schema for creating campaign content."""
    kol_id: int = Field(..., description="KOL identifier")
    scheduled_publish_date: Optional[datetime] = None


class CampaignContentUpdate(BaseModel):
    """Schema for updating campaign content."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    content_url: Optional[str] = Field(None, max_length=500)
    media_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    scheduled_publish_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    status: Optional[ContentStatus] = None


class CampaignContentResponse(CampaignContentBase):
    """Schema for campaign content responses."""
    id: int
    campaign_id: int
    kol_id: int
    status: ContentStatus
    scheduled_publish_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    engagement_rate: Optional[float] = None
    reach: Optional[int] = None
    impressions: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    last_updated: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Analytics and Reporting Schemas
class CampaignAnalytics(BaseModel):
    """Schema for campaign analytics."""
    campaign_id: int
    total_collaborations: int = 0
    completed_collaborations: int = 0
    total_content: int = 0
    published_content: int = 0
    total_reach: int = 0
    avg_engagement_rate: float = 0.0
    budget_spent: float = 0.0
    roi: float = 0.0
    generated_at: datetime


class CampaignPerformanceMetrics(BaseModel):
    """Schema for detailed campaign performance metrics."""
    campaign_id: int
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Union[int, float]]
    platform_breakdown: Dict[str, Dict[str, Union[int, float]]]
    kol_performance: List[Dict[str, Any]]
    content_performance: List[Dict[str, Any]]
    trends: Dict[str, List[Dict[str, Any]]]


class CampaignROIAnalysis(BaseModel):
    """Schema for campaign ROI analysis."""
    campaign_id: int
    total_investment: float
    total_return: float
    roi_percentage: float
    cost_per_engagement: Optional[float] = None
    cost_per_reach: Optional[float] = None
    revenue_attribution: Optional[Dict[str, float]] = None
    analysis_date: datetime


# Workflow and Automation Schemas
class CampaignWorkflowAction(BaseModel):
    """Schema for campaign workflow actions."""
    action: str = Field(..., pattern="^(launch|pause|complete|approve|reject)$")
    reason: Optional[str] = Field(None, max_length=500)
    scheduled_at: Optional[datetime] = None


class CampaignAutomationRule(BaseModel):
    """Schema for campaign automation rules."""
    rule_name: str = Field(..., min_length=1, max_length=100)
    trigger_condition: Dict[str, Any]
    action: Dict[str, Any]
    is_active: bool = True
    priority: int = Field(default=1, ge=1, le=10)


class CampaignTemplate(BaseModel):
    """Schema for campaign templates."""
    template_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    template_data: Dict[str, Any]
    category: Optional[str] = None
    is_public: bool = False


# Bulk Operations Schemas
class CampaignBulkAction(BaseModel):
    """Schema for bulk campaign actions."""
    campaign_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(update_status|bulk_update|export|delete)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class CampaignBulkUpdateResponse(BaseModel):
    """Schema for bulk update response."""
    success_count: int
    failed_count: int
    failed_campaigns: List[Dict[str, Any]] = Field(default_factory=list)
    updated_campaigns: List[int] = Field(default_factory=list)


# Import/Export Schemas
class CampaignImportData(BaseModel):
    """Schema for campaign data import."""
    campaigns: List[CampaignCreate] = Field(..., min_length=1)
    skip_duplicates: bool = True
    update_existing: bool = False


class CampaignImportResponse(BaseModel):
    """Schema for campaign import response."""
    imported_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class CampaignExportFilters(BaseModel):
    """Schema for campaign export filtering."""
    status: Optional[List[CampaignStatus]] = None
    platforms: Optional[List[SocialPlatform]] = None
    date_range: Optional[Dict[str, datetime]] = None
    created_by: Optional[List[int]] = None
    include_collaborations: bool = True
    include_content: bool = True
    include_analytics: bool = False


# Collaboration Management Schemas
class CollaborationInvitation(BaseModel):
    """Schema for collaboration invitations."""
    campaign_id: int
    kol_ids: List[int] = Field(..., min_length=1)
    invitation_message: Optional[str] = Field(None, max_length=1000)
    compensation_offer: Optional[Dict[str, Any]] = None
    deadline: Optional[datetime] = None
    auto_approve: bool = False


class CollaborationInvitationResponse(BaseModel):
    """Schema for collaboration invitation response."""
    invitation_id: str
    campaign_id: int
    sent_count: int
    failed_count: int
    scheduled_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class CollaborationApproval(BaseModel):
    """Schema for collaboration approval."""
    collaboration_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, max_length=500)
    compensation_updates: Optional[Dict[int, Dict[str, Any]]] = None


# Content Approval Schemas
class ContentApprovalRequest(BaseModel):
    """Schema for content approval requests."""
    content_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(approve|reject|request_changes)$")
    feedback: Optional[str] = Field(None, max_length=1000)
    approval_notes: Optional[str] = Field(None, max_length=500)


class ContentApprovalResponse(BaseModel):
    """Schema for content approval response."""
    approved_count: int
    rejected_count: int
    pending_count: int
    processed_content: List[Dict[str, Any]] = Field(default_factory=list)
    notifications_sent: int


# Notification and Communication Schemas
class CampaignNotification(BaseModel):
    """Schema for campaign notifications."""
    notification_type: str
    recipients: List[int]  # User/KOL IDs
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    channels: List[str] = Field(default_factory=lambda: ["email"])
    scheduled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignNotificationResponse(BaseModel):
    """Schema for campaign notification response."""
    notification_id: str
    total_recipients: int
    sent_count: int
    failed_count: int
    scheduled_count: int
    delivery_status: Dict[str, int] = Field(default_factory=dict)