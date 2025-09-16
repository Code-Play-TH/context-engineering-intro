"""
Campaign and Brief database models.
Handles campaign lifecycle management, briefs, and KOL assignments.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum
from decimal import Decimal

from app.core.database import Base


class CampaignStatus(PyEnum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApprovalStatus(PyEnum):
    """Brief approval status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class Campaign(Base):
    """
    Campaign model for managing KOL campaigns with comprehensive tracking.
    """
    __tablename__ = "campaigns"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Campaign timeline
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Financial information
    budget: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    spent_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, default=0)

    # Campaign objectives and KPIs
    # Format: {"total_reach": 100000, "total_engagement": 5000, "posts_delivered": 10}
    target_kpis: Mapped[Dict[str, float]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Target KPIs for the campaign"
    )

    # Campaign requirements and guidelines
    # Format: ["#brand", "#summer2024"], ["summer collection", "new arrivals"]
    required_hashtags: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Required hashtags for content"
    )

    optional_hashtags: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Optional hashtags for content"
    )

    required_keywords: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Required keywords in content"
    )

    optional_keywords: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Optional keywords in content"
    )

    # Content guidelines
    content_guidelines: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Content guidelines and requirements"
    )

    # Brand information
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand_mentions: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Required brand mentions"
    )

    # Campaign status and metadata
    status: Mapped[CampaignStatus] = mapped_column(String(50), nullable=False, default=CampaignStatus.DRAFT, index=True)

    # Performance tracking
    baseline_engagement_rates: Mapped[Dict[str, Dict[str, float]]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Baseline engagement rates by KOL and platform"
    )

    actual_kpis: Mapped[Dict[str, float]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Actual achieved KPIs"
    )

    # Campaign settings
    auto_approval_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    content_monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

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
    kols = relationship(
        "KOL",
        secondary="campaign_kols",
        back_populates="campaigns",
        lazy="selectin"
    )

    briefs = relationship(
        "Brief",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    content_posts = relationship(
        "ContentPost",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    messages = relationship(
        "Message",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    follow_up_schedules = relationship(
        "FollowUpSchedule",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    creator = relationship("User", foreign_keys=[created_by])

    def calculate_budget_utilization(self) -> float:
        """Calculate budget utilization percentage."""
        if not self.budget or self.budget == 0:
            return 0.0
        return float((self.spent_amount / self.budget) * 100)

    def calculate_kpi_achievement(self, kpi_name: str) -> float:
        """Calculate achievement percentage for a specific KPI."""
        target = self.target_kpis.get(kpi_name, 0)
        actual = self.actual_kpis.get(kpi_name, 0)
        if target == 0:
            return 0.0
        return (actual / target) * 100

    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        now = datetime.utcnow()
        return (
            self.status == CampaignStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )

    def days_remaining(self) -> int:
        """Calculate days remaining in campaign."""
        if self.end_date < datetime.utcnow():
            return 0
        return (self.end_date - datetime.utcnow()).days

    def add_kol(self, kol_id: int, compensation: Decimal = None, notes: str = None) -> None:
        """Add a KOL to the campaign."""
        from app.models.kol import CampaignKOL

        campaign_kol = CampaignKOL(
            campaign_id=self.id,
            kol_id=kol_id,
            compensation=compensation,
            notes=notes
        )
        # This would be added to the session in the calling code

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"


class Brief(Base):
    """
    Brief model for individual KOL campaign briefs with versioning.
    """
    __tablename__ = "briefs"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)

    # Brief content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Rich text brief content")

    # Requirements and specifications
    requirements: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Specific requirements for this brief"
    )

    # Deadlines and timeline
    # Format: {"first_draft": "2024-01-15", "final_submission": "2024-01-20", "posting_date": "2024-01-25"}
    deadlines: Mapped[Dict[str, datetime]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Various deadlines for the brief"
    )

    # Deliverables specification
    # Format: {"posts_count": 3, "stories_count": 5, "video_length": 60, "platforms": ["instagram", "tiktok"]}
    deliverables: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Expected deliverables specification"
    )

    # Approval workflow
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        String(50),
        nullable=False,
        default=ApprovalStatus.DRAFT,
        index=True
    )

    # Versioning
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brief_templates.id"), nullable=True)

    # Approval and feedback
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="briefs")
    kol = relationship("KOL")
    template = relationship("BriefTemplate", foreign_keys=[template_id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])

    def is_overdue(self) -> bool:
        """Check if any deadline is overdue."""
        now = datetime.utcnow()
        for deadline_name, deadline_date in self.deadlines.items():
            if isinstance(deadline_date, str):
                deadline_date = datetime.fromisoformat(deadline_date)
            if deadline_date < now:
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

    def create_new_version(self, content: str, requirements: Dict[str, Any] = None) -> "Brief":
        """Create a new version of this brief."""
        new_brief = Brief(
            campaign_id=self.campaign_id,
            kol_id=self.kol_id,
            title=self.title,
            content=content,
            requirements=requirements or self.requirements,
            deadlines=self.deadlines,
            deliverables=self.deliverables,
            version=self.version + 1,
            template_id=self.template_id
        )
        return new_brief

    def __repr__(self) -> str:
        return f"<Brief(id={self.id}, campaign_id={self.campaign_id}, kol_id={self.kol_id}, version={self.version})>"


class BriefTemplate(Base):
    """
    Template model for reusable brief templates.
    """
    __tablename__ = "brief_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template content with variable placeholders
    content_template: Mapped[str] = mapped_column(Text, nullable=False)

    # Default requirements and settings
    default_requirements: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    default_deliverables: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    # Template metadata
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    # Template status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    briefs = relationship("Brief", back_populates="template")
    creator = relationship("User", foreign_keys=[created_by])

    def render_content(self, variables: Dict[str, Any]) -> str:
        """Render template content with provided variables."""
        from jinja2 import Template

        template = Template(self.content_template)
        return template.render(**variables)

    def __repr__(self) -> str:
        return f"<BriefTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"


# Indexes for performance optimization
Index("idx_campaign_dates", Campaign.start_date, Campaign.end_date)
Index("idx_campaign_brand_status", Campaign.brand_name, Campaign.status)
Index("idx_campaign_created_status", Campaign.created_at, Campaign.status)

Index("idx_brief_campaign_kol", Brief.campaign_id, Brief.kol_id)
Index("idx_brief_status_version", Brief.approval_status, Brief.version)
Index("idx_brief_deadlines_gin", Brief.deadlines, postgresql_using="gin")

Index("idx_brief_template_category", BriefTemplate.category, BriefTemplate.is_active)