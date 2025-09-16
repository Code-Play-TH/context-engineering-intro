"""
Content Pydantic V2 schemas for validation and serialization.
Handles content posts, statistics, and alerts with custom validators.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import re
from urllib.parse import urlparse

from app.models.content import VerificationStatus, ContentType


class ContentPostBase(BaseModel):
    """Base content post schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    kol_id: int = Field(..., gt=0, description="KOL ID")
    campaign_id: int = Field(..., gt=0, description="Campaign ID")
    platform: str = Field(..., min_length=1, max_length=50, description="Social media platform")
    platform_post_id: str = Field(..., min_length=1, max_length=255, description="Platform post ID")
    url: str = Field(..., description="Content URL")
    content: str = Field(..., min_length=1, max_length=10000, description="Content text")
    content_type: ContentType = Field(ContentType.POST, description="Content type")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used")
    mentions: List[str] = Field(default_factory=list, description="User mentions")
    media_urls: List[str] = Field(default_factory=list, description="Media URLs")
    posted_at: datetime = Field(..., description="When content was posted")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate social media platform."""
        valid_platforms = {"instagram", "youtube", "tiktok", "twitter", "facebook", "linkedin", "twitch"}
        if v.lower() not in valid_platforms:
            raise ValueError(f"Unsupported platform: {v}")
        return v.lower()

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate content URL format."""
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")

            if parsed.scheme not in ["http", "https"]:
                raise ValueError("URL must use http or https scheme")

            return v
        except Exception:
            raise ValueError("Invalid URL format")

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, v: List[str]) -> List[str]:
        """Validate hashtags format."""
        validated_hashtags = []

        for hashtag in v:
            # Remove # if present
            if hashtag.startswith("#"):
                hashtag = hashtag[1:]

            # Validate hashtag format
            if not re.match(r'^[a-zA-Z0-9_]+$', hashtag):
                raise ValueError(f"Invalid hashtag format: {hashtag}")

            if len(hashtag) > 100:
                raise ValueError(f"Hashtag too long: {hashtag}")

            validated_hashtags.append(hashtag.lower())

        # Remove duplicates while preserving order
        return list(dict.fromkeys(validated_hashtags))

    @field_validator("mentions")
    @classmethod
    def validate_mentions(cls, v: List[str]) -> List[str]:
        """Validate user mentions format."""
        validated_mentions = []

        for mention in v:
            # Remove @ if present
            if mention.startswith("@"):
                mention = mention[1:]

            # Validate mention format
            if not re.match(r'^[a-zA-Z0-9._-]+$', mention):
                raise ValueError(f"Invalid mention format: {mention}")

            if len(mention) > 100:
                raise ValueError(f"Mention too long: {mention}")

            validated_mentions.append(mention.lower())

        # Remove duplicates while preserving order
        return list(dict.fromkeys(validated_mentions))

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, v: List[str]) -> List[str]:
        """Validate media URLs."""
        if len(v) > 10:
            raise ValueError("Maximum 10 media URLs allowed")

        validated_urls = []
        for url in v:
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError(f"Invalid media URL format: {url}")
                validated_urls.append(url)
            except Exception:
                raise ValueError(f"Invalid media URL format: {url}")

        return validated_urls

    @field_validator("posted_at")
    @classmethod
    def validate_posted_at(cls, v: datetime) -> datetime:
        """Validate posted timestamp."""
        if v > datetime.utcnow():
            raise ValueError("Posted time cannot be in the future")

        # Content shouldn't be older than 5 years
        five_years_ago = datetime.utcnow() - timedelta(days=5*365)
        if v < five_years_ago:
            raise ValueError("Posted time is too old (more than 5 years)")

        return v

    @computed_field
    @property
    def media_count(self) -> int:
        """Calculate media count."""
        return len(self.media_urls)


class AIAnalysisData(BaseModel):
    """Schema for AI analysis data."""
    sentiment: Optional[str] = Field(None, description="Content sentiment (positive/negative/neutral)")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Sentiment score (-1 to 1)")
    topics: List[str] = Field(default_factory=list, description="Detected topics")
    brand_mentions: List[str] = Field(default_factory=list, description="Brand mentions detected")
    language: Optional[str] = Field(None, description="Detected language")
    adult_content: bool = Field(False, description="Adult content detected")
    toxicity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Toxicity score")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    categories: List[str] = Field(default_factory=list, description="Content categories")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, v: Optional[str]) -> Optional[str]:
        """Validate sentiment value."""
        if v is None:
            return v

        valid_sentiments = {"positive", "negative", "neutral"}
        if v.lower() not in valid_sentiments:
            raise ValueError(f"Invalid sentiment: {v}")

        return v.lower()


class ContentPostCreate(ContentPostBase):
    """Schema for creating a new content post."""
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Detection confidence score")
    match_criteria: List[str] = Field(default_factory=list, description="Detection match criteria")
    ai_analysis: Optional[AIAnalysisData] = Field(None, description="AI analysis results")
    content_quality_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Content quality score")
    brand_alignment_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Brand alignment score")
    compliant_with_guidelines: bool = Field(True, description="Compliant with guidelines")
    compliance_issues: List[str] = Field(default_factory=list, description="Compliance issues")

    @field_validator("match_criteria")
    @classmethod
    def validate_match_criteria(cls, v: List[str]) -> List[str]:
        """Validate match criteria."""
        valid_criteria = {
            "hashtag_match", "keyword_match", "mention_match", "ai_analysis",
            "manual_detection", "brand_mention", "campaign_hashtag", "location_tag"
        }

        for criteria in v:
            if criteria not in valid_criteria:
                raise ValueError(f"Invalid match criteria: {criteria}")

        return v

    @field_validator("compliance_issues")
    @classmethod
    def validate_compliance_issues(cls, v: List[str]) -> List[str]:
        """Validate compliance issues."""
        valid_issues = {
            "missing_disclosure", "inappropriate_content", "brand_mismatch",
            "copyright_violation", "adult_content", "toxicity", "spam",
            "misleading_claims", "unlabeled_ad", "terms_violation"
        }

        for issue in v:
            if issue not in valid_issues:
                raise ValueError(f"Invalid compliance issue: {issue}")

        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        # Convert AI analysis to dict if present
        if self.ai_analysis:
            data["ai_analysis"] = self.ai_analysis.model_dump()

        return data


class ContentPostUpdate(BaseModel):
    """Schema for updating a content post."""
    model_config = ConfigDict(from_attributes=True)

    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    hashtags: Optional[List[str]] = Field(None)
    mentions: Optional[List[str]] = Field(None)
    verification_status: Optional[VerificationStatus] = Field(None)
    verification_notes: Optional[str] = Field(None, max_length=2000)
    content_quality_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    brand_alignment_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    compliant_with_guidelines: Optional[bool] = Field(None)
    compliance_issues: Optional[List[str]] = Field(None)


class ContentPostResponse(ContentPostBase):
    """Schema for content post response."""
    id: int
    verification_status: VerificationStatus
    confidence_score: float = 0.0
    match_criteria: List[str] = Field(default_factory=list)
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    content_quality_score: Optional[float] = None
    brand_alignment_score: Optional[float] = None
    compliant_with_guidelines: bool = True
    compliance_issues: List[str] = Field(default_factory=list)
    detected_at: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_verified(self) -> bool:
        """Check if content is verified."""
        return self.verification_status in [VerificationStatus.VERIFIED, VerificationStatus.AUTO_VERIFIED]

    @computed_field
    @property
    def needs_review(self) -> bool:
        """Check if content needs manual review."""
        return self.verification_status in [VerificationStatus.MANUAL_REVIEW, VerificationStatus.DUPLICATE_REVIEW]

    @computed_field
    @property
    def age_hours(self) -> float:
        """Calculate content age in hours."""
        return (datetime.utcnow() - self.posted_at).total_seconds() / 3600


class ContentStatsBase(BaseModel):
    """Base content statistics schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    content_post_id: int = Field(..., gt=0, description="Content post ID")
    collection_interval: str = Field(..., description="Collection interval")
    likes: int = Field(0, ge=0, description="Number of likes")
    comments: int = Field(0, ge=0, description="Number of comments")
    shares: int = Field(0, ge=0, description="Number of shares")
    saves: Optional[int] = Field(None, ge=0, description="Number of saves")
    views: Optional[int] = Field(None, ge=0, description="Number of views")
    reach: Optional[int] = Field(None, ge=0, description="Reach count")
    impressions: Optional[int] = Field(None, ge=0, description="Impression count")
    collection_method: str = Field("api", description="Collection method")

    @field_validator("collection_interval")
    @classmethod
    def validate_collection_interval(cls, v: str) -> str:
        """Validate collection interval."""
        valid_intervals = {"1hr", "6hr", "12hr", "24hr", "3day", "5day", "7day", "14day", "30day"}
        if v not in valid_intervals:
            raise ValueError(f"Invalid collection interval: {v}")
        return v

    @field_validator("collection_method")
    @classmethod
    def validate_collection_method(cls, v: str) -> str:
        """Validate collection method."""
        valid_methods = {"api", "scraping", "manual", "webhook"}
        if v not in valid_methods:
            raise ValueError(f"Invalid collection method: {v}")
        return v

    @computed_field
    @property
    def total_engagement(self) -> int:
        """Calculate total engagement."""
        return self.likes + self.comments + self.shares + (self.saves or 0)


class PlatformSpecificMetrics(BaseModel):
    """Schema for platform-specific metrics."""
    # Instagram specific
    story_completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    profile_visits: Optional[int] = Field(None, ge=0)
    website_clicks: Optional[int] = Field(None, ge=0)

    # YouTube specific
    watch_time_minutes: Optional[float] = Field(None, ge=0.0)
    average_view_duration: Optional[float] = Field(None, ge=0.0)
    subscriber_gains: Optional[int] = Field(None)

    # TikTok specific
    video_completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    music_plays: Optional[int] = Field(None, ge=0)
    duets: Optional[int] = Field(None, ge=0)

    # Twitter specific
    retweets: Optional[int] = Field(None, ge=0)
    quotes: Optional[int] = Field(None, ge=0)
    link_clicks: Optional[int] = Field(None, ge=0)


class AudienceDemographics(BaseModel):
    """Schema for audience demographics."""
    age_groups: Dict[str, float] = Field(default_factory=dict, description="Age group percentages")
    gender_split: Dict[str, float] = Field(default_factory=dict, description="Gender percentages")
    locations: Dict[str, float] = Field(default_factory=dict, description="Location percentages")
    languages: Dict[str, float] = Field(default_factory=dict, description="Language percentages")
    interests: List[str] = Field(default_factory=list, description="Top audience interests")

    @field_validator("age_groups")
    @classmethod
    def validate_age_groups(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate age group percentages."""
        valid_ranges = {"13-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"}
        for age_range in v.keys():
            if age_range not in valid_ranges:
                raise ValueError(f"Invalid age range: {age_range}")
        return v


class ContentStatsCreate(ContentStatsBase):
    """Schema for creating content statistics."""
    platform_specific_metrics: Optional[PlatformSpecificMetrics] = Field(None, description="Platform-specific metrics")
    audience_demographics: Optional[AudienceDemographics] = Field(None, description="Audience demographics")
    data_completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="Data completeness score")

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        # Convert nested models to dict
        if self.platform_specific_metrics:
            data["platform_specific_metrics"] = self.platform_specific_metrics.model_dump()

        if self.audience_demographics:
            data["audience_demographics"] = self.audience_demographics.model_dump()

        return data


class ContentStatsUpdate(BaseModel):
    """Schema for updating content statistics."""
    model_config = ConfigDict(from_attributes=True)

    likes: Optional[int] = Field(None, ge=0)
    comments: Optional[int] = Field(None, ge=0)
    shares: Optional[int] = Field(None, ge=0)
    saves: Optional[int] = Field(None, ge=0)
    views: Optional[int] = Field(None, ge=0)
    reach: Optional[int] = Field(None, ge=0)
    impressions: Optional[int] = Field(None, ge=0)


class ContentStatsResponse(ContentStatsBase):
    """Schema for content statistics response."""
    id: int
    collected_at: datetime
    engagement_rate: float = 0.0
    viral_coefficient: Optional[float] = None
    platform_specific_metrics: Dict[str, Any] = Field(default_factory=dict)
    audience_demographics: Dict[str, Any] = Field(default_factory=dict)
    likes_growth: Optional[int] = None
    comments_growth: Optional[int] = None
    shares_growth: Optional[int] = None
    views_growth: Optional[int] = None
    data_completeness_score: float = 0.0

    @computed_field
    @property
    def engagement_score(self) -> float:
        """Calculate normalized engagement score (0-100)."""
        if not self.reach or self.reach == 0:
            return 0.0

        total_engagement = self.total_engagement
        return min((total_engagement / self.reach) * 100, 100.0)

    @computed_field
    @property
    def virality_score(self) -> float:
        """Calculate virality score based on shares."""
        if not self.reach or self.reach == 0:
            return 0.0

        return min((self.shares / self.reach) * 100, 100.0)


class ContentAlertBase(BaseModel):
    """Base content alert schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    content_post_id: int = Field(..., gt=0, description="Content post ID")
    campaign_id: int = Field(..., gt=0, description="Campaign ID")
    alert_type: str = Field(..., min_length=1, max_length=100, description="Alert type")
    severity: str = Field("medium", description="Alert severity")
    title: str = Field(..., min_length=1, max_length=255, description="Alert title")
    description: str = Field(..., min_length=1, max_length=2000, description="Alert description")
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict, description="Trigger conditions")
    threshold_values: Dict[str, Any] = Field(default_factory=dict, description="Threshold values")
    actual_values: Dict[str, Any] = Field(default_factory=dict, description="Actual values")

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        """Validate alert type."""
        valid_types = {
            "underperforming", "viral", "compliance_issue", "negative_sentiment",
            "high_engagement", "spam_detected", "copyright_claim", "content_removed",
            "unusual_activity", "performance_drop", "quality_issue"
        }

        if v not in valid_types:
            raise ValueError(f"Invalid alert type: {v}")

        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate alert severity."""
        valid_severities = {"low", "medium", "high", "critical"}
        if v not in valid_severities:
            raise ValueError(f"Invalid severity: {v}")
        return v


class ContentAlertCreate(ContentAlertBase):
    """Schema for creating a content alert."""
    pass


class ContentAlertUpdate(BaseModel):
    """Schema for updating a content alert."""
    model_config = ConfigDict(from_attributes=True)

    status: Optional[str] = Field(None, description="Alert status")
    resolution_notes: Optional[str] = Field(None, max_length=2000, description="Resolution notes")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate alert status."""
        if v is None:
            return v

        valid_statuses = {"active", "acknowledged", "resolved", "dismissed"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}")

        return v


class ContentAlertResponse(ContentAlertBase):
    """Schema for content alert response."""
    id: int
    status: str = "active"
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    notifications_sent: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if alert is active."""
        return self.status == "active"

    @computed_field
    @property
    def age_hours(self) -> float:
        """Calculate alert age in hours."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600


class ContentSearchCriteria(BaseModel):
    """Schema for content search criteria."""
    kol_ids: Optional[List[int]] = Field(None, description="Filter by KOL IDs")
    campaign_ids: Optional[List[int]] = Field(None, description="Filter by campaign IDs")
    platforms: Optional[List[str]] = Field(None, description="Filter by platforms")
    content_types: Optional[List[ContentType]] = Field(None, description="Filter by content types")
    verification_statuses: Optional[List[VerificationStatus]] = Field(None, description="Filter by verification status")
    posted_after: Optional[datetime] = Field(None, description="Content posted after date")
    posted_before: Optional[datetime] = Field(None, description="Content posted before date")
    min_engagement: Optional[int] = Field(None, ge=0, description="Minimum engagement count")
    hashtags: Optional[List[str]] = Field(None, description="Filter by hashtags")
    mentions: Optional[List[str]] = Field(None, description="Filter by mentions")
    has_compliance_issues: Optional[bool] = Field(None, description="Filter by compliance issues")
    quality_score_min: Optional[float] = Field(None, ge=0.0, le=10.0, description="Minimum quality score")

    # Sorting and pagination
    sort_by: str = Field("posted_at", description="Sort field")
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


class ContentSearchResult(BaseModel):
    """Schema for content search results."""
    content_posts: List[ContentPostResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    search_criteria: ContentSearchCriteria

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_count + self.per_page - 1) // self.per_page


class ContentAnalyticsResponse(BaseModel):
    """Schema for content analytics response."""
    total_posts: int = 0
    verified_posts: int = 0
    pending_posts: int = 0
    rejected_posts: int = 0
    avg_engagement_rate: float = 0.0
    top_performing_posts: List[ContentPostResponse] = Field(default_factory=list)
    platform_breakdown: Dict[str, int] = Field(default_factory=dict)
    content_type_breakdown: Dict[str, int] = Field(default_factory=dict)
    compliance_score: float = 0.0
    quality_score: float = 0.0
    active_alerts: int = 0
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)