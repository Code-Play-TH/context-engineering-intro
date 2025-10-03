"""
Campaign content database models.
Handles campaign briefs, content submissions, and related entities.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum
from decimal import Decimal

from app.core.database import Base


class ContentStatus(PyEnum):
    """Content status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentType(PyEnum):
    """Content type enumeration."""
    POST = "post"
    STORY = "story"
    VIDEO = "video"
    REEL = "reel"
    LIVE = "live"
    ARTICLE = "article"
    REVIEW = "review"


class BriefStatus(PyEnum):
    """Brief status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CampaignBrief(Base):
    """
    Campaign brief model for managing campaign instructions and requirements.
    """
    __tablename__ = "campaign_briefs"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    kol_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kols.id"), nullable=True, index=True)

    # Brief content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Requirements and guidelines
    requirements: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Specific requirements and guidelines"
    )

    deliverables: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Expected deliverables specification"
    )

    # Timeline and deadlines
    deadlines: Mapped[Dict[str, datetime]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Various deadlines and milestones"
    )

    # Template and customization
    template_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customization: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Brief customization parameters"
    )

    # Status and workflow
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True
    )

    # Communication tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Feedback and revisions
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="briefs")
    kol = relationship("KOL")
    creator = relationship("User", foreign_keys=[created_by])

    def is_overdue(self) -> bool:
        """Check if any deadline is overdue."""
        now = datetime.utcnow()
        for deadline_name, deadline_date in self.deadlines.items():
            if isinstance(deadline_date, str):
                deadline_date = datetime.fromisoformat(deadline_date)
            if deadline_date < now and self.status not in [BriefStatus.COMPLETED]:
                return True
        return False

    def get_next_deadline(self) -> Optional[datetime]:
        """Get the next upcoming deadline."""
        now = datetime.utcnow()
        upcoming_deadlines = []

        for deadline_name, deadline_date in self.deadlines.items():
            if isinstance(deadline_date, str):
                deadline_date = datetime.fromisoformat(deadline_date)
            if deadline_date > now:
                upcoming_deadlines.append(deadline_date)

        return min(upcoming_deadlines) if upcoming_deadlines else None

    def __repr__(self) -> str:
        return f"<CampaignBrief(id={self.id}, campaign_id={self.campaign_id}, status='{self.status}')>"


class CampaignContent(Base):
    """
    Campaign content model for managing content submissions and performance.
    """
    __tablename__ = "campaign_content"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)
    brief_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaign_briefs.id"), nullable=True)

    # Content details
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Content URLs and media
    content_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    media_urls: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="URLs to media files (images, videos, etc.)"
    )

    # Social media metadata
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

    # Scheduling and publishing
    scheduled_publish_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_publish_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Performance metrics
    engagement_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Performance metadata
    performance_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Detailed performance metrics and analytics"
    )

    # Status and approval workflow
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True
    )

    # Approval and feedback
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Compliance and guidelines
    compliance_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    guideline_violations: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Any guideline violations detected"
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="content_posts")
    kol = relationship("KOL", back_populates="content_posts")
    brief = relationship("CampaignBrief")
    approver = relationship("User", foreign_keys=[approved_by])

    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate based on metrics."""
        if not self.reach or self.reach == 0:
            return 0.0

        total_engagement = (self.likes or 0) + (self.comments or 0) + (self.shares or 0) + (self.saves or 0)
        return (total_engagement / self.reach) * 100

    def is_published(self) -> bool:
        """Check if content is published."""
        return self.status == ContentStatus.PUBLISHED and self.actual_publish_date is not None

    def is_overdue(self) -> bool:
        """Check if content publication is overdue."""
        if not self.scheduled_publish_date:
            return False

        return (
            self.scheduled_publish_date < datetime.utcnow() and
            self.status not in [ContentStatus.PUBLISHED, ContentStatus.ARCHIVED]
        )

    def __repr__(self) -> str:
        return f"<CampaignContent(id={self.id}, campaign_id={self.campaign_id}, kol_id={self.kol_id}, status='{self.status}')>"


# Indexes for performance optimization
Index("idx_brief_campaign_kol", CampaignBrief.campaign_id, CampaignBrief.kol_id)
Index("idx_brief_status_created", CampaignBrief.status, CampaignBrief.created_at)

Index("idx_content_campaign_kol", CampaignContent.campaign_id, CampaignContent.kol_id)
Index("idx_content_platform_status", CampaignContent.platform, CampaignContent.status)
Index("idx_content_published_date", CampaignContent.actual_publish_date)
Index("idx_content_scheduled_date", CampaignContent.scheduled_publish_date)