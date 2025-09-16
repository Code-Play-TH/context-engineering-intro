"""
Content monitoring and analytics database models.
Handles content post detection, verification, and statistics tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, DECIMAL, ForeignKey, Index, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum
from decimal import Decimal

from app.core.database import Base


class VerificationStatus(PyEnum):
    """Content verification status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
    DUPLICATE_REVIEW = "duplicate_review"
    AUTO_VERIFIED = "auto_verified"


class ContentType(PyEnum):
    """Content type enumeration."""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    VIDEO = "video"
    LIVE = "live"
    CAROUSEL = "carousel"


class ContentPost(Base):
    """
    Content post model for tracking KOL content across platforms.
    """
    __tablename__ = "content_posts"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)

    # Platform information
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Content information
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(String(50), nullable=False, default=ContentType.POST)

    # Content metadata
    hashtags: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Hashtags used in the content"
    )

    mentions: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="User mentions in the content"
    )

    # Media information
    media_urls: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="URLs of images/videos in the post"
    )

    media_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing information
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Verification and matching
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(50),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True
    )

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_criteria: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Criteria that matched for detection (keywords, hashtags, ai_analysis, etc.)"
    )

    # AI analysis results
    ai_analysis: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="AI analysis results including sentiment, topics, etc."
    )

    # Manual verification
    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quality assessment
    content_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    brand_alignment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Compliance checking
    compliant_with_guidelines: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    compliance_issues: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="List of compliance issues if any"
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    kol = relationship("KOL", back_populates="content_posts")
    campaign = relationship("Campaign", back_populates="content_posts")
    verifier = relationship("User", foreign_keys=[verified_by])

    content_stats = relationship(
        "ContentStats",
        back_populates="content_post",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def get_latest_stats(self) -> Optional["ContentStats"]:
        """Get the most recent statistics for this content."""
        return self.content_stats.order_by(ContentStats.collected_at.desc()).first()

    def get_stats_by_interval(self, interval: str) -> Optional["ContentStats"]:
        """Get statistics for a specific collection interval."""
        return self.content_stats.filter_by(collection_interval=interval).order_by(
            ContentStats.collected_at.desc()
        ).first()

    def calculate_engagement_rate(self, stats: "ContentStats" = None) -> float:
        """Calculate engagement rate based on latest stats."""
        if not stats:
            stats = self.get_latest_stats()

        if not stats or not stats.reach:
            return 0.0

        total_engagement = (stats.likes or 0) + (stats.comments or 0) + (stats.shares or 0)
        return (total_engagement / stats.reach) * 100 if stats.reach > 0 else 0.0

    def is_high_performing(self, threshold: float = 5.0) -> bool:
        """Check if content is high-performing based on engagement rate."""
        latest_stats = self.get_latest_stats()
        if not latest_stats:
            return False

        engagement_rate = self.calculate_engagement_rate(latest_stats)
        return engagement_rate >= threshold

    def verify_content(self, user_id: int, notes: str = None) -> None:
        """Manually verify the content."""
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_by = user_id
        self.verified_at = datetime.utcnow()
        if notes:
            self.verification_notes = notes

    def reject_content(self, user_id: int, notes: str = None) -> None:
        """Manually reject the content."""
        self.verification_status = VerificationStatus.REJECTED
        self.verified_by = user_id
        self.verified_at = datetime.utcnow()
        if notes:
            self.verification_notes = notes

    def __repr__(self) -> str:
        return f"<ContentPost(id={self.id}, platform='{self.platform}', kol_id={self.kol_id}, status='{self.verification_status}')>"


class ContentStats(Base):
    """
    Content statistics model for tracking performance metrics over time.
    """
    __tablename__ = "content_stats"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_post_id: Mapped[int] = mapped_column(ForeignKey("content_posts.id"), nullable=False, index=True)

    # Collection metadata
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    collection_interval: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Collection interval (24hr, 3day, 5day, 7day, etc.)"
    )

    # Engagement metrics
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Reach and impression metrics
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Calculated metrics
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    viral_coefficient: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Platform-specific metrics
    platform_specific_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Platform-specific metrics (story_completion_rate, video_watch_time, etc.)"
    )

    # Audience demographics (if available)
    audience_demographics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Audience demographics data from platform insights"
    )

    # Growth metrics (compared to previous collection)
    likes_growth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments_growth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares_growth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    views_growth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Data quality indicators
    data_completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    collection_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="api",
        comment="How the data was collected (api, scraping, manual)"
    )

    # Relationships
    content_post = relationship("ContentPost", back_populates="content_stats")

    def calculate_growth_metrics(self, previous_stats: "ContentStats") -> None:
        """Calculate growth metrics compared to previous collection."""
        if previous_stats:
            self.likes_growth = self.likes - (previous_stats.likes or 0)
            self.comments_growth = self.comments - (previous_stats.comments or 0)
            self.shares_growth = self.shares - (previous_stats.shares or 0)
            self.views_growth = (self.views or 0) - (previous_stats.views or 0)

    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate for this collection."""
        if not self.reach or self.reach == 0:
            return 0.0

        total_engagement = self.likes + self.comments + self.shares
        self.engagement_rate = (total_engagement / self.reach) * 100
        return self.engagement_rate

    def calculate_viral_coefficient(self) -> float:
        """Calculate viral coefficient (shares/reach)."""
        if not self.reach or self.reach == 0:
            return 0.0

        self.viral_coefficient = (self.shares / self.reach) * 100
        return self.viral_coefficient

    def __repr__(self) -> str:
        return f"<ContentStats(id={self.id}, content_post_id={self.content_post_id}, interval='{self.collection_interval}')>"


class ContentAlert(Base):
    """
    Content alert model for tracking performance alerts and notifications.
    """
    __tablename__ = "content_alerts"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_post_id: Mapped[int] = mapped_column(ForeignKey("content_posts.id"), nullable=False, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)

    # Alert information
    alert_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of alert (underperforming, viral, compliance_issue, etc.)"
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        comment="Alert severity (low, medium, high, critical)"
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Alert conditions
    trigger_conditions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Conditions that triggered this alert"
    )

    threshold_values: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Threshold values used for comparison"
    )

    actual_values: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Actual values that triggered the alert"
    )

    # Status and resolution
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="Alert status (active, acknowledged, resolved, dismissed)"
    )

    acknowledged_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notification tracking
    notifications_sent: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Track notifications sent for this alert"
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    content_post = relationship("ContentPost")
    campaign = relationship("Campaign")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def acknowledge(self, user_id: int) -> None:
        """Acknowledge the alert."""
        self.status = "acknowledged"
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()

    def resolve(self, user_id: int, notes: str = None) -> None:
        """Resolve the alert."""
        self.status = "resolved"
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
        if notes:
            self.resolution_notes = notes

    def dismiss(self, user_id: int) -> None:
        """Dismiss the alert."""
        self.status = "dismissed"
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<ContentAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', status='{self.status}')>"


# Indexes for performance optimization
Index("idx_content_post_platform_campaign", ContentPost.platform, ContentPost.campaign_id)
Index("idx_content_post_kol_campaign", ContentPost.kol_id, ContentPost.campaign_id)
Index("idx_content_post_status_posted", ContentPost.verification_status, ContentPost.posted_at)
Index("idx_content_post_platform_posted", ContentPost.platform, ContentPost.posted_at)
Index("idx_content_post_hashtags_gin", ContentPost.hashtags, postgresql_using="gin")
Index("idx_content_post_confidence", ContentPost.confidence_score, ContentPost.verification_status)

Index("idx_content_stats_post_interval", ContentStats.content_post_id, ContentStats.collection_interval)
Index("idx_content_stats_collected_interval", ContentStats.collected_at, ContentStats.collection_interval)
Index("idx_content_stats_engagement", ContentStats.engagement_rate, ContentStats.collected_at)

Index("idx_content_alert_type_status", ContentAlert.alert_type, ContentAlert.status)
Index("idx_content_alert_severity_created", ContentAlert.severity, ContentAlert.created_at)
Index("idx_content_alert_campaign_status", ContentAlert.campaign_id, ContentAlert.status)