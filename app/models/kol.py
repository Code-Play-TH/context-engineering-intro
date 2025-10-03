"""
KOL (Key Opinion Leader) database models.
Using SQLAlchemy 2.0 declarative syntax with proper relationships and indexing.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, DECIMAL, ForeignKey, Index
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum

from app.core.database import Base


class KOLStatus(PyEnum):
    """KOL status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"
    PENDING_VERIFICATION = "pending_verification"


class KOL(Base):
    """
    KOL (Key Opinion Leader) model with comprehensive profile information.
    Follows the PRP specification with JSONB fields for flexible social media data.
    """
    __tablename__ = "kols"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Social media accounts - flexible JSONB structure
    # Format: {"platform": {"handle": "username", "id": "platform_id", "verified": bool}}
    social_media_accounts: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Social media account information per platform"
    )

    # Demographics - flexible structure for various data points
    # Format: {"age": int, "gender": str, "location": str, "country": str, "language": [str]}
    demographics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Demographic information including age, location, etc."
    )

    # Niche categories - array of strings for multiple niches
    niche: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="List of niche categories (fashion, beauty, tech, etc.)"
    )

    # Performance metrics - updated by background tasks
    follower_counts: Mapped[Dict[str, int]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Follower counts per platform"
    )

    engagement_rates: Mapped[Dict[str, float]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Engagement rates per platform"
    )

    # Historical performance data
    performance_history: Mapped[List[Dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Historical performance snapshots"
    )

    # Communication preferences
    communication_preferences: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=["email"],
        comment="Preferred communication channels (email, discord, line, etc.)"
    )

    # Location and timezone
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")

    # Status and metadata
    status: Mapped[KOLStatus] = mapped_column(String(50), nullable=False, default=KOLStatus.ACTIVE, index=True)

    # Additional profile information
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Performance tracking
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_performance_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Verification status
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Campaign relationships
    campaigns = relationship(
        "Campaign",
        secondary="campaign_kols",
        back_populates="kols",
        lazy="selectin"
    )

    # Content posts
    content_posts = relationship(
        "ContentPost",
        back_populates="kol",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Messages and communications
    messages = relationship(
        "Message",
        back_populates="kol",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Follow-up schedules
    follow_up_schedules = relationship(
        "FollowUpSchedule",
        back_populates="kol",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Social accounts
    social_accounts = relationship(
        "KOLSocialAccounts",
        back_populates="kol",
        cascade="all, delete-orphan"
    )

    # Performance metrics
    performance_metrics = relationship(
        "KOLPerformanceMetrics",
        back_populates="kol",
        uselist=False
    )

    # Collaborations
    collaborations = relationship(
        "Collaboration",
        back_populates="kol",
        cascade="all, delete-orphan"
    )

    # Content posts
    content_posts = relationship(
        "CampaignContent",
        back_populates="kol",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def total_followers(self) -> int:
        """Calculate total followers across all platforms."""
        return sum(self.follower_counts.values()) if self.follower_counts else 0

    @hybrid_property
    def average_engagement_rate(self) -> float:
        """Calculate average engagement rate across all platforms."""
        if not self.engagement_rates:
            return 0.0
        rates = list(self.engagement_rates.values())
        return sum(rates) / len(rates) if rates else 0.0

    @hybrid_property
    def primary_platform(self) -> Optional[str]:
        """Get the platform with the most followers."""
        if not self.follower_counts:
            return None
        return max(self.follower_counts.items(), key=lambda x: x[1])[0]

    def get_platform_handle(self, platform: str) -> Optional[str]:
        """Get handle for a specific platform."""
        account = self.social_media_accounts.get(platform, {})
        return account.get("handle")

    def get_platform_follower_count(self, platform: str) -> int:
        """Get follower count for a specific platform."""
        return self.follower_counts.get(platform, 0)

    def get_platform_engagement_rate(self, platform: str) -> float:
        """Get engagement rate for a specific platform."""
        return self.engagement_rates.get(platform, 0.0)

    def is_available_for_campaign(self, start_date: datetime, end_date: datetime) -> bool:
        """Check if KOL is available for a campaign period."""
        # This would check against existing campaign commitments
        # Implementation would query active campaigns
        return self.status == KOLStatus.ACTIVE

    def update_performance_data(self, platform: str, followers: int, engagement_rate: float) -> None:
        """Update performance data for a platform."""
        # Update current metrics
        if not self.follower_counts:
            self.follower_counts = {}
        if not self.engagement_rates:
            self.engagement_rates = {}

        self.follower_counts[platform] = followers
        self.engagement_rates[platform] = engagement_rate

        # Add to performance history
        if not self.performance_history:
            self.performance_history = []

        self.performance_history.append({
            "platform": platform,
            "followers": followers,
            "engagement_rate": engagement_rate,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 100 historical records per platform
        platform_history = [h for h in self.performance_history if h.get("platform") == platform]
        if len(platform_history) > 100:
            # Remove oldest entries for this platform
            other_history = [h for h in self.performance_history if h.get("platform") != platform]
            self.performance_history = other_history + platform_history[-100:]

        self.last_performance_update = datetime.utcnow()

    def add_social_media_account(self, platform: str, handle: str, platform_id: str = None, verified: bool = False) -> None:
        """Add or update a social media account."""
        if not self.social_media_accounts:
            self.social_media_accounts = {}

        self.social_media_accounts[platform] = {
            "handle": handle,
            "id": platform_id,
            "verified": verified,
            "added_at": datetime.utcnow().isoformat()
        }

    def __repr__(self) -> str:
        return f"<KOL(id={self.id}, name='{self.name}', email='{self.email}', status='{self.status}')>"


# Indexes for performance optimization
Index("idx_kol_niche_gin", KOL.niche, postgresql_using="gin")
Index("idx_kol_follower_counts_gin", KOL.follower_counts, postgresql_using="gin")
Index("idx_kol_engagement_rates_gin", KOL.engagement_rates, postgresql_using="gin")
Index("idx_kol_social_media_gin", KOL.social_media_accounts, postgresql_using="gin")
Index("idx_kol_demographics_gin", KOL.demographics, postgresql_using="gin")
Index("idx_kol_location_status", KOL.location, KOL.status)
Index("idx_kol_created_status", KOL.created_at, KOL.status)


class KOLSocialAccounts(Base):
    """KOL social media accounts model."""
    __tablename__ = "kol_social_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    follower_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    kol = relationship("KOL", back_populates="social_accounts")

    def __repr__(self) -> str:
        return f"<KOLSocialAccounts(id={self.id}, kol_id={self.kol_id}, platform='{self.platform}')>"


class KOLPerformanceMetrics(Base):
    """KOL performance metrics model."""
    __tablename__ = "kol_performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)

    avg_engagement_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False, default=0)
    avg_reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_campaigns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_campaigns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reliability_score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False, default=0)

    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    kol = relationship("KOL", back_populates="performance_metrics")

    def __repr__(self) -> str:
        return f"<KOLPerformanceMetrics(id={self.id}, kol_id={self.kol_id})>"


# Association table for many-to-many relationship between KOLs and Campaigns
class CampaignKOL(Base):
    """Association table for KOL-Campaign relationships with additional metadata."""
    __tablename__ = "campaign_kols"

    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), primary_key=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), primary_key=True)

    # Additional relationship metadata
    compensation: Mapped[Optional[DECIMAL]] = mapped_column(DECIMAL(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    assignment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="assigned")

    # Performance tracking for this specific campaign
    deliverables_completed: Mapped[int] = mapped_column(Integer, default=0)
    deliverables_total: Mapped[int] = mapped_column(Integer, default=0)

    # Notes and comments
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CampaignKOL(campaign_id={self.campaign_id}, kol_id={self.kol_id}, status='{self.status}')>"