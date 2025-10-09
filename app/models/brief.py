from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
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


class Brief(Base):
    """
    Brief model for KOL campaign briefs.
    Contains detailed instructions and requirements for KOLs.
    """
    __tablename__ = "briefs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    
    # Brief content
    content = Column(Text, nullable=False)
    
    # Brief metadata
    status = Column(Enum(BriefStatus), default=BriefStatus.DRAFT, index=True)
    
    # JSON field for structured brief data
    # Example: {
    #   "deliverables": ["1 Instagram post", "3 Stories"],
    #   "requirements": ["Must include product shot", "Use hashtag #brand"],
    #   "timeline": {"start_date": "2024-01-15", "end_date": "2024-01-30"},
    #   "compensation": {"amount": 5000, "currency": "THB", "type": "fixed"},
    #   "guidelines": ["Brand voice guidelines", "Visual style requirements"]
    # }
    brief_data = Column(JSON, default=dict)
    
    # Relationships
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    kol_id = Column(Integer, ForeignKey("kols.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("brief_templates.id"), nullable=True)
    
    # Approval workflow
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Communication tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes and feedback
    internal_notes = Column(Text)  # Internal team notes
    kol_feedback = Column(Text)    # KOL feedback/questions
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="briefs")
    kol = relationship("KOL", back_populates="briefs")
    template = relationship("BriefTemplate", back_populates="briefs")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_briefs")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="approved_briefs")
    messages = relationship("Message", back_populates="brief")

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