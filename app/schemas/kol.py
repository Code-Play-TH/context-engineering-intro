"""
KOL Pydantic V2 schemas for validation and serialization.
Separate schemas for create, read, update operations with custom validators.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import re
from email_validator import validate_email, EmailNotValidError

from app.models.kol import KOLStatus


class KOLBase(BaseModel):
    """Base KOL schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=2, max_length=255, description="KOL full name")
    email: str = Field(..., description="KOL email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    bio: Optional[str] = Field(None, max_length=2000, description="Short biography")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    location: Optional[str] = Field(None, max_length=255, description="Primary location")
    timezone: str = Field("UTC", description="Timezone")
    niche: List[str] = Field(default_factory=list, description="Niche categories")
    communication_preferences: List[str] = Field(
        default_factory=lambda: ["email"],
        description="Preferred communication channels"
    )

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, v: str) -> str:
        """Validate email address format."""
        try:
            validate_email(v)
        except EmailNotValidError:
            raise ValueError("Invalid email address format")
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

    @field_validator("website")
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v is None:
            return v
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError("Invalid website URL format")
        return v

    @field_validator("niche")
    @classmethod
    def validate_niche_categories(cls, v: List[str]) -> List[str]:
        """Validate niche categories."""
        if not v:
            raise ValueError("At least one niche category is required")

        valid_niches = {
            "fashion", "beauty", "lifestyle", "fitness", "food", "travel",
            "technology", "gaming", "entertainment", "music", "art", "sports",
            "business", "finance", "health", "parenting", "education", "pets",
            "home", "automotive", "books", "photography", "comedy", "diy"
        }

        for niche in v:
            if niche.lower() not in valid_niches:
                raise ValueError(f"Invalid niche category: {niche}")

        return [niche.lower() for niche in v]

    @field_validator("communication_preferences")
    @classmethod
    def validate_communication_channels(cls, v: List[str]) -> List[str]:
        """Validate communication channels."""
        valid_channels = {"email", "line", "discord", "whatsapp", "telegram", "sms", "phone"}

        for channel in v:
            if channel.lower() not in valid_channels:
                raise ValueError(f"Invalid communication channel: {channel}")

        if "email" not in [ch.lower() for ch in v]:
            v.append("email")  # Email is always required

        return [channel.lower() for channel in v]


class SocialMediaAccountCreate(BaseModel):
    """Schema for creating social media account information."""
    platform: str = Field(..., description="Social media platform")
    handle: str = Field(..., min_length=1, max_length=100, description="Platform handle/username")
    platform_id: Optional[str] = Field(None, description="Platform-specific user ID")
    verified: bool = Field(False, description="Whether the account is verified")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate social media platform."""
        valid_platforms = {"instagram", "youtube", "tiktok", "twitter", "facebook", "linkedin", "twitch"}
        if v.lower() not in valid_platforms:
            raise ValueError(f"Unsupported platform: {v}")
        return v.lower()

    @field_validator("handle")
    @classmethod
    def validate_handle(cls, v: str) -> str:
        """Validate social media handle format."""
        # Remove @ symbol if present
        if v.startswith("@"):
            v = v[1:]

        # Basic handle validation (alphanumeric, underscore, dot, hyphen)
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Handle can only contain letters, numbers, dots, underscores, and hyphens")

        return v


class DemographicsCreate(BaseModel):
    """Schema for demographic information."""
    age: Optional[int] = Field(None, ge=13, le=100, description="Age")
    gender: Optional[str] = Field(None, description="Gender")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    city: Optional[str] = Field(None, max_length=100, description="City")
    language: List[str] = Field(default_factory=list, description="Languages spoken")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender value."""
        if v is None:
            return v
        valid_genders = {"male", "female", "non-binary", "other", "prefer-not-to-say"}
        if v.lower() not in valid_genders:
            raise ValueError(f"Invalid gender value: {v}")
        return v.lower()


class KOLCreate(KOLBase):
    """Schema for creating a new KOL."""
    social_media_accounts: Dict[str, SocialMediaAccountCreate] = Field(
        default_factory=dict,
        description="Social media accounts by platform"
    )
    demographics: Optional[DemographicsCreate] = Field(None, description="Demographic information")

    @field_validator("social_media_accounts")
    @classmethod
    def validate_social_media_accounts(cls, v: Dict[str, SocialMediaAccountCreate]) -> Dict[str, Any]:
        """Validate social media accounts."""
        if not v:
            raise ValueError("At least one social media account is required")

        # Convert Pydantic models to dict for database storage
        result = {}
        for platform, account in v.items():
            if platform != account.platform:
                raise ValueError(f"Platform mismatch: key '{platform}' != account platform '{account.platform}'")

            result[platform] = {
                "handle": account.handle,
                "id": account.platform_id,
                "verified": account.verified,
                "added_at": datetime.utcnow().isoformat()
            }

        return result

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        # Convert demographics to dict if present
        if self.demographics:
            data["demographics"] = self.demographics.model_dump()

        return data


class KOLUpdate(BaseModel):
    """Schema for updating a KOL."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=2000)
    website: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None)
    niche: Optional[List[str]] = Field(None)
    communication_preferences: Optional[List[str]] = Field(None)
    status: Optional[KOLStatus] = Field(None)

    # Reuse validators from base class
    @field_validator("email")
    @classmethod
    def validate_email_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate email address format."""
        if v is None:
            return v
        try:
            validate_email(v)
        except EmailNotValidError:
            raise ValueError("Invalid email address format")
        return v.lower()


class PerformanceDataResponse(BaseModel):
    """Schema for performance data response."""
    platform: str
    follower_count: int
    media_count: int = 0
    engagement_rate: float = 0.0
    last_updated: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KOLResponse(KOLBase):
    """Schema for KOL response with computed fields."""
    id: int
    status: KOLStatus
    social_media_accounts: Dict[str, Any] = Field(default_factory=dict)
    demographics: Dict[str, Any] = Field(default_factory=dict)
    follower_counts: Dict[str, int] = Field(default_factory=dict)
    engagement_rates: Dict[str, float] = Field(default_factory=dict)
    performance_history: List[Dict[str, Any]] = Field(default_factory=list)
    verified: bool = False
    verified_at: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    last_performance_update: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def total_followers(self) -> int:
        """Calculate total followers across all platforms."""
        return sum(self.follower_counts.values()) if self.follower_counts else 0

    @computed_field
    @property
    def average_engagement_rate(self) -> float:
        """Calculate average engagement rate across all platforms."""
        if not self.engagement_rates:
            return 0.0
        rates = list(self.engagement_rates.values())
        return sum(rates) / len(rates) if rates else 0.0

    @computed_field
    @property
    def primary_platform(self) -> Optional[str]:
        """Get the platform with the most followers."""
        if not self.follower_counts:
            return None
        return max(self.follower_counts.items(), key=lambda x: x[1])[0]

    @computed_field
    @property
    def social_media_handles(self) -> Dict[str, str]:
        """Get simplified handle mapping."""
        handles = {}
        for platform, account_data in self.social_media_accounts.items():
            if isinstance(account_data, dict) and "handle" in account_data:
                handles[platform] = account_data["handle"]
        return handles


class KOLSearchCriteria(BaseModel):
    """Schema for KOL search criteria."""
    # Basic filters
    niches: Optional[List[str]] = Field(None, description="Filter by niche categories")
    location: Optional[str] = Field(None, description="Filter by location")
    age_range: Optional[tuple[int, int]] = Field(None, description="Age range filter (min, max)")

    # Social media filters
    min_followers: Optional[Dict[str, int]] = Field(None, description="Minimum followers per platform")
    engagement_rate_range: Optional[tuple[float, float]] = Field(None, description="Engagement rate range")
    verified_only: bool = Field(False, description="Filter for verified accounts only")

    # Availability filters
    available_from: Optional[datetime] = Field(None, description="Available from date")
    available_to: Optional[datetime] = Field(None, description="Available to date")

    # Sorting and pagination
    sort_by: Optional[str] = Field("relevance", description="Sort field")
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

    def cache_key(self) -> str:
        """Generate cache key for search results."""
        import hashlib
        import json

        # Create a deterministic string from search criteria
        criteria_str = json.dumps(self.model_dump(), sort_keys=True, default=str)
        return hashlib.md5(criteria_str.encode()).hexdigest()

    @field_validator("min_followers")
    @classmethod
    def validate_min_followers(cls, v: Optional[Dict[str, int]]) -> Optional[Dict[str, int]]:
        """Validate minimum followers criteria."""
        if v is None:
            return v

        valid_platforms = {"instagram", "youtube", "tiktok", "twitter", "facebook", "linkedin"}
        for platform, min_count in v.items():
            if platform.lower() not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
            if min_count < 0:
                raise ValueError(f"Minimum followers must be non-negative for {platform}")

        return {k.lower(): v for k, v in v.items()}


class KOLSearchResult(BaseModel):
    """Schema for KOL search results."""
    kols: List[KOLResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    search_criteria: KOLSearchCriteria

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_count + self.per_page - 1) // self.per_page


class KOLWithScore(BaseModel):
    """Schema for KOL with relevance score."""
    kol: KOLResponse
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }