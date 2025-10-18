"""Client Brief model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from sqlalchemy import DECIMAL
from enum import Enum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.campaign import Campaign


class ClientBriefStatus(str, Enum):
    """Client brief status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ClientBrief(SQLModel, table=True):
    """Client brief model for campaign requirements."""
    
    __tablename__ = "client_briefs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(max_length=255, index=True)
    campaign_objective: str = Field()
    target_audience: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    budget: Optional[Decimal] = Field(default=None, sa_column=Column(DECIMAL(12, 2)))
    currency: str = Field(default="USD", max_length=3)
    brand_guidelines: Optional[str] = Field(default=None)
    content_requirements: Optional[str] = Field(default=None)
    status: ClientBriefStatus = Field(default=ClientBriefStatus.DRAFT, index=True)
    
    # Timeline requirements
    campaign_start_date: Optional[datetime] = Field(default=None)
    campaign_end_date: Optional[datetime] = Field(default=None)
    content_deadline: Optional[datetime] = Field(default=None)
    
    # Additional requirements
    platform_requirements: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    kol_requirements: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    deliverable_requirements: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Approval workflow
    approved_by: Optional[int] = Field(default=None, foreign_key="users.id")
    approved_at: Optional[datetime] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)
    
    # Metadata
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    creator: "User" = Relationship(back_populates="client_briefs")
    approver: Optional["User"] = Relationship(
        back_populates="approved_client_briefs",
        sa_relationship_kwargs={"foreign_keys": "[ClientBrief.approved_by]"}
    )
    campaign: Optional["Campaign"] = Relationship(back_populates="client_briefs")