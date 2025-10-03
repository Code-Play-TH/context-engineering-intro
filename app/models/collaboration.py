"""
Collaboration database models.
Handles KOL-Campaign collaborations and related entities.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum
from decimal import Decimal

from app.core.database import Base


class CollaborationStatus(PyEnum):
    """Collaboration status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class CompensationType(PyEnum):
    """Compensation type enumeration."""
    FIXED = "fixed"
    PERFORMANCE = "performance"
    HYBRID = "hybrid"
    PRODUCT_ONLY = "product_only"
    REVENUE_SHARE = "revenue_share"


class Collaboration(Base):
    """
    Collaboration model for managing KOL-Campaign relationships.
    """
    __tablename__ = "collaborations"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)

    # Compensation details
    compensation_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    compensation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="fixed"
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Deliverables and timeline
    deliverables: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Expected deliverables and specifications"
    )

    timeline: Mapped[Dict[str, datetime]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Timeline milestones and deadlines"
    )

    # Contract and agreement details
    contract_terms: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Contract terms and conditions"
    )

    # Status and workflow
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True
    )

    # Important dates
    proposed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Performance tracking
    performance_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Performance metrics and KPIs achieved"
    )

    # Communication and notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="collaborations")
    kol = relationship("KOL", back_populates="collaborations")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def calculate_completion_rate(self) -> float:
        """Calculate completion rate based on deliverables."""
        if not self.deliverables:
            return 0.0

        total_deliverables = len(self.deliverables.get("items", []))
        completed_deliverables = sum(
            1 for item in self.deliverables.get("items", [])
            if item.get("status") == "completed"
        )

        if total_deliverables == 0:
            return 0.0

        return (completed_deliverables / total_deliverables) * 100

    def is_overdue(self) -> bool:
        """Check if collaboration has overdue deliverables."""
        now = datetime.utcnow()
        for milestone, deadline in self.timeline.items():
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            if deadline < now and self.status not in [CollaborationStatus.COMPLETED, CollaborationStatus.CANCELLED]:
                return True
        return False

    def get_next_deadline(self) -> Optional[datetime]:
        """Get the next upcoming deadline."""
        now = datetime.utcnow()
        upcoming_deadlines = []

        for milestone, deadline in self.timeline.items():
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            if deadline > now:
                upcoming_deadlines.append(deadline)

        return min(upcoming_deadlines) if upcoming_deadlines else None

    def __repr__(self) -> str:
        return f"<Collaboration(id={self.id}, campaign_id={self.campaign_id}, kol_id={self.kol_id}, status='{self.status}')>"


# Indexes for performance optimization
Index("idx_collaboration_campaign_kol", Collaboration.campaign_id, Collaboration.kol_id)
Index("idx_collaboration_status_created", Collaboration.status, Collaboration.created_at)
Index("idx_collaboration_kol_status", Collaboration.kol_id, Collaboration.status)