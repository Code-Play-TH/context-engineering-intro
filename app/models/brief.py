from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
import enum


class BriefStatus(str, enum.Enum):
    """Brief status enumeration"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Brief(SQLModel, table=True):
    """
    Brief model for KOL campaign briefs.
    Contains detailed instructions and requirements for KOLs.
    """
    __tablename__ = "briefs"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    
    # Brief content
    content: str
    
    # Brief metadata
    status: BriefStatus = Field(default=BriefStatus.DRAFT, index=True)
    
    # JSON field for structured brief data
    # Example: {
    #   "deliverables": ["1 Instagram post", "3 Stories"],
    #   "requirements": ["Must include product shot", "Use hashtag #brand"],
    #   "timeline": {"start_date": "2024-01-15", "end_date": "2024-01-30"},
    #   "compensation": {"amount": 5000, "currency": "THB", "type": "fixed"},
    #   "guidelines": ["Brand voice guidelines", "Visual style requirements"]
    # }
    brief_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    campaign_id: int = Field(foreign_key="campaigns.id")
    kol_id: int = Field(foreign_key="kols.id")
    template_id: Optional[int] = Field(default=None, foreign_key="brief_templates.id")
    
    # Approval workflow
    created_by: int = Field(foreign_key="users.id")
    approved_by: Optional[int] = Field(default=None, foreign_key="users.id")
    approved_at: Optional[datetime] = None
    
    # Communication tracking
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Notes and feedback
    internal_notes: Optional[str] = None  # Internal team notes
    kol_feedback: Optional[str] = None    # KOL feedback/questions
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    campaign: Optional["Campaign"] = Relationship(back_populates="briefs")
    kol: Optional["KOL"] = Relationship(back_populates="briefs")
    template: Optional["BriefTemplate"] = Relationship(back_populates="briefs")
    # User relationships (commented out to avoid circular import issues)
    # creator: Optional["User"] = Relationship(back_populates="created_briefs")
    # approver: Optional["User"] = Relationship(back_populates="approved_briefs")
    messages: List["Message"] = Relationship(back_populates="brief")

    def __repr__(self):
        return f"<Brief(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def is_editable(self) -> bool:
        """Check if brief can be edited"""
        return self.status in [BriefStatus.DRAFT, BriefStatus.PENDING_REVIEW, BriefStatus.REJECTED]

    @property
    def can_be_sent(self) -> bool:
        """Check if brief can be sent to KOL"""
        return self.status == BriefStatus.APPROVED

    @property
    def is_active(self) -> bool:
        """Check if brief is in active workflow"""
        return self.status in [
            BriefStatus.SENT, 
            BriefStatus.ACKNOWLEDGED, 
            BriefStatus.IN_PROGRESS
        ]