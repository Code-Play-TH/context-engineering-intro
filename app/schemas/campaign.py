"""
Campaign and Brief Pydantic V2 schemas for validation and serialization.
Comprehensive schemas for campaign lifecycle management.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from app.models.campaign import CampaignStatus, ApprovalStatus


class CampaignBase(BaseModel):
    """Base campaign schema with common fields."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str = Field(..., min_length=2, max_length=255, description="Campaign name")
    description: str = Field(..., min_length=10, description="Campaign description")
    brand_name: str = Field(..., min_length=2, max_length=255, description="Brand name")
    start_date: datetime = Field(..., description="Campaign start date")
    end_date: datetime = Field(..., description="Campaign end date")
    budget: Optional[Decimal] = Field(None, ge=0, description="Campaign budget")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime, info) -> datetime:
        """Validate that end date is after start date."""
        if hasattr(info, 'data') and 'start_date' in info.data:
            start_date = info.data['start_date']
            if v <= start_date:
                raise ValueError("End date must be after start date")

            # Check for reasonable campaign duration
            duration = v - start_date
            if duration > timedelta(days=365):
                raise ValueError("Campaign duration cannot exceed 365 days")
            if duration < timedelta(days=1):
                raise ValueError("Campaign duration must be at least 1 day")

        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        valid_currencies = {
            "USD", "EUR", "GBP", "JPY", "CNY", "KRW", "THB", "SGD",
            "HKD", "AUD", "CAD", "CHF", "SEK", "NOK", "DKK"
        }
        if v.upper() not in valid_currencies:
            raise ValueError(f"Unsupported currency: {v}")
        return v.upper()


class CampaignTargetKPIs(BaseModel):
    """Schema for campaign target KPIs."""
    total_reach: Optional[int] = Field(None, ge=1, description="Target total reach")
    total_engagement: Optional[int] = Field(None, ge=1, description="Target total engagement")
    average_engagement_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Target avg engagement rate %")
    posts_delivered: Optional[int] = Field(None, ge=1, description="Target number of posts")
    video_views: Optional[int] = Field(None, ge=1, description="Target video views")
    story_completion_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Target story completion rate %")
    brand_mention_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Target brand mention rate %")
    roi_percentage: Optional[float] = Field(None, description="Target ROI percentage")

    @field_validator("*")
    @classmethod
    def validate_positive_values(cls, v: Optional[Union[int, float]]) -> Optional[Union[int, float]]:
        """Validate that all numeric values are positive."""
        if v is not None and v < 0:
            raise ValueError("KPI values must be positive")
        return v


class ContentGuidelines(BaseModel):
    """Schema for content guidelines."""
    content_type_requirements: Optional[Dict[str, int]] = Field(
        None,
        description="Required content types (posts, stories, reels, etc.)"
    )
    posting_schedule: Optional[Dict[str, Any]] = Field(None, description="Posting schedule guidelines")
    tone_and_style: Optional[str] = Field(None, description="Tone and style guidelines")
    dos_and_donts: Optional[List[str]] = Field(None, description="List of dos and don'ts")
    approval_required: bool = Field(True, description="Whether content approval is required")
    revision_deadline: Optional[int] = Field(None, ge=1, le=30, description="Revision deadline in days")


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    target_kpis: Optional[CampaignTargetKPIs] = Field(None, description="Target KPIs")
    required_hashtags: List[str] = Field(default_factory=list, description="Required hashtags")
    optional_hashtags: List[str] = Field(default_factory=list, description="Optional hashtags")
    required_keywords: List[str] = Field(default_factory=list, description="Required keywords")
    optional_keywords: List[str] = Field(default_factory=list, description="Optional keywords")
    brand_mentions: List[str] = Field(default_factory=list, description="Required brand mentions")
    content_guidelines: Optional[ContentGuidelines] = Field(None, description="Content guidelines")

    # Feature toggles
    auto_approval_enabled: bool = Field(False, description="Enable automatic brief approval")
    follow_up_enabled: bool = Field(True, description="Enable automated follow-ups")
    content_monitoring_enabled: bool = Field(True, description="Enable content monitoring")

    @field_validator("required_hashtags", "optional_hashtags")
    @classmethod
    def validate_hashtags(cls, v: List[str]) -> List[str]:
        """Validate hashtag format."""
        validated_hashtags = []
        for hashtag in v:
            # Remove # if present and add it back
            clean_hashtag = hashtag.lstrip("#")
            if not clean_hashtag:
                continue

            # Validate hashtag format (alphanumeric and underscore only)
            if not clean_hashtag.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid hashtag format: {hashtag}")

            validated_hashtags.append(f"#{clean_hashtag}")

        return validated_hashtags

    @field_validator("required_keywords", "optional_keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate keywords."""
        return [keyword.strip() for keyword in v if keyword.strip()]

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        # Convert target_kpis to dict if present
        if self.target_kpis:
            data["target_kpis"] = self.target_kpis.model_dump(exclude_none=True)

        # Convert content_guidelines to dict if present
        if self.content_guidelines:
            data["content_guidelines"] = self.content_guidelines.model_dump(exclude_none=True)

        return data


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    brand_name: Optional[str] = Field(None, min_length=2, max_length=255)
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    budget: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    status: Optional[CampaignStatus] = Field(None)
    target_kpis: Optional[CampaignTargetKPIs] = Field(None)
    required_hashtags: Optional[List[str]] = Field(None)
    optional_hashtags: Optional[List[str]] = Field(None)
    required_keywords: Optional[List[str]] = Field(None)
    optional_keywords: Optional[List[str]] = Field(None)
    brand_mentions: Optional[List[str]] = Field(None)
    content_guidelines: Optional[ContentGuidelines] = Field(None)


class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: int
    status: CampaignStatus
    target_kpis: Dict[str, Any] = Field(default_factory=dict)
    actual_kpis: Dict[str, Any] = Field(default_factory=dict)
    required_hashtags: List[str] = Field(default_factory=list)
    optional_hashtags: List[str] = Field(default_factory=list)
    required_keywords: List[str] = Field(default_factory=list)
    optional_keywords: List[str] = Field(default_factory=list)
    brand_mentions: List[str] = Field(default_factory=list)
    content_guidelines: Dict[str, Any] = Field(default_factory=dict)
    baseline_engagement_rates: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    spent_amount: Decimal = Field(default=0)
    auto_approval_enabled: bool = False
    follow_up_enabled: bool = True
    content_monitoring_enabled: bool = True
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    @computed_field
    @property
    def budget_utilization(self) -> float:
        """Calculate budget utilization percentage."""
        if not self.budget or self.budget == 0:
            return 0.0
        return float((self.spent_amount / self.budget) * 100)

    @computed_field
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in campaign."""
        if self.end_date < datetime.utcnow():
            return 0
        return (self.end_date - datetime.utcnow()).days

    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        now = datetime.utcnow()
        return (
            self.status == CampaignStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )

    @computed_field
    @property
    def kpi_achievement_summary(self) -> Dict[str, float]:
        """Calculate KPI achievement percentages."""
        achievements = {}
        for kpi_name, target_value in self.target_kpis.items():
            actual_value = self.actual_kpis.get(kpi_name, 0)
            if target_value > 0:
                achievements[kpi_name] = (actual_value / target_value) * 100
            else:
                achievements[kpi_name] = 0.0
        return achievements


# Brief Schemas
class BriefDeliverables(BaseModel):
    """Schema for brief deliverables."""
    posts_count: int = Field(1, ge=1, le=50, description="Number of posts required")
    stories_count: int = Field(0, ge=0, le=20, description="Number of stories required")
    reels_count: int = Field(0, ge=0, le=10, description="Number of reels required")
    video_length: Optional[int] = Field(None, ge=15, le=600, description="Video length in seconds")
    platforms: List[str] = Field(..., min_length=1, description="Target platforms")
    posting_dates: Optional[List[datetime]] = Field(None, description="Specific posting dates")

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, v: List[str]) -> List[str]:
        """Validate platform names."""
        valid_platforms = {"instagram", "youtube", "tiktok", "twitter", "facebook", "linkedin", "twitch"}
        validated_platforms = []

        for platform in v:
            if platform.lower() not in valid_platforms:
                raise ValueError(f"Unsupported platform: {platform}")
            validated_platforms.append(platform.lower())

        return list(set(validated_platforms))  # Remove duplicates


class BriefRequirements(BaseModel):
    """Schema for brief requirements."""
    content_format: Optional[str] = Field(None, description="Required content format")
    style_guide: Optional[str] = Field(None, description="Style guide requirements")
    call_to_action: Optional[str] = Field(None, description="Required call to action")
    disclosure_requirements: Optional[str] = Field(None, description="Disclosure requirements")
    brand_guidelines: Optional[str] = Field(None, description="Brand guideline requirements")
    technical_specs: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")


class BriefBase(BaseModel):
    """Base brief schema."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    title: str = Field(..., min_length=5, max_length=255, description="Brief title")
    content: str = Field(..., min_length=50, description="Brief content")


class BriefCreate(BriefBase):
    """Schema for creating a new brief."""
    campaign_id: int = Field(..., description="Campaign ID")
    kol_id: int = Field(..., description="KOL ID")
    requirements: Optional[BriefRequirements] = Field(None, description="Specific requirements")
    deliverables: BriefDeliverables = Field(..., description="Expected deliverables")
    deadlines: Dict[str, datetime] = Field(..., description="Various deadlines")
    template_id: Optional[int] = Field(None, description="Template ID if using template")

    @field_validator("deadlines")
    @classmethod
    def validate_deadlines(cls, v: Dict[str, datetime]) -> Dict[str, datetime]:
        """Validate deadline structure and ordering."""
        required_deadlines = {"final_submission"}
        optional_deadlines = {"first_draft", "revision_deadline", "approval_deadline", "posting_date"}

        # Check for required deadlines
        for required in required_deadlines:
            if required not in v:
                raise ValueError(f"Missing required deadline: {required}")

        # Validate deadline names
        for deadline_name in v.keys():
            if deadline_name not in required_deadlines and deadline_name not in optional_deadlines:
                raise ValueError(f"Invalid deadline type: {deadline_name}")

        # Validate deadline ordering
        now = datetime.utcnow()
        sorted_deadlines = sorted(v.items(), key=lambda x: x[1])

        for i, (name, date) in enumerate(sorted_deadlines):
            if date < now:
                raise ValueError(f"Deadline {name} cannot be in the past")

            # Check logical order
            if i > 0:
                prev_name, prev_date = sorted_deadlines[i-1]
                if date <= prev_date:
                    raise ValueError(f"Deadline {name} must be after {prev_name}")

        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        if self.requirements:
            data["requirements"] = self.requirements.model_dump(exclude_none=True)

        if self.deliverables:
            data["deliverables"] = self.deliverables.model_dump(exclude_none=True)

        return data


class BriefUpdate(BaseModel):
    """Schema for updating a brief."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    title: Optional[str] = Field(None, min_length=5, max_length=255)
    content: Optional[str] = Field(None, min_length=50)
    requirements: Optional[BriefRequirements] = Field(None)
    deliverables: Optional[BriefDeliverables] = Field(None)
    deadlines: Optional[Dict[str, datetime]] = Field(None)
    approval_status: Optional[ApprovalStatus] = Field(None)
    feedback: Optional[str] = Field(None)
    revision_notes: Optional[str] = Field(None)


class BriefResponse(BriefBase):
    """Schema for brief response."""
    id: int
    campaign_id: int
    kol_id: int
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    deadlines: Dict[str, datetime] = Field(default_factory=dict)
    approval_status: ApprovalStatus
    version: int
    template_id: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    feedback: Optional[str] = None
    revision_notes: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if any deadline is overdue."""
        now = datetime.utcnow()
        for deadline_name, deadline_date in self.deadlines.items():
            if isinstance(deadline_date, str):
                deadline_date = datetime.fromisoformat(deadline_date)
            if deadline_date < now and self.approval_status != ApprovalStatus.APPROVED:
                return True
        return False

    @computed_field
    @property
    def next_deadline(self) -> Optional[datetime]:
        """Get the next upcoming deadline."""
        now = datetime.utcnow()
        upcoming_deadlines = []

        for deadline_name, deadline_date in self.deadlines.items():
            if isinstance(deadline_date, str):
                deadline_date = datetime.fromisoformat(deadline_date)
            if deadline_date > now:
                upcoming_deadlines.append(deadline_date)

        return min(upcoming_deadlines) if upcoming_deadlines else None


# Brief Template Schemas
class BriefTemplateCreate(BaseModel):
    """Schema for creating a brief template."""
    name: str = Field(..., min_length=2, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    content_template: str = Field(..., min_length=50, description="Template content with variables")
    default_requirements: Optional[BriefRequirements] = Field(None, description="Default requirements")
    default_deliverables: Optional[BriefDeliverables] = Field(None, description="Default deliverables")
    category: Optional[str] = Field(None, max_length=100, description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        if self.default_requirements:
            data["default_requirements"] = self.default_requirements.model_dump(exclude_none=True)

        if self.default_deliverables:
            data["default_deliverables"] = self.default_deliverables.model_dump(exclude_none=True)

        return data


class BriefTemplateResponse(BaseModel):
    """Schema for brief template response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    content_template: str
    default_requirements: Dict[str, Any] = Field(default_factory=dict)
    default_deliverables: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None