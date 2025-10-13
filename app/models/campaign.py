"""Campaign model."""
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from enum import Enum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.client_brief import ClientBrief
    from app.models.campaign_kpi import CampaignKPI
    from app.models.deliverable import Deliverable
    from app.models.campaign_kol import CampaignKOL
    from app.models.brief import Brief
    from app.models.message import Message


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(SQLModel, table=True):
    """Campaign model for managing influencer campaigns."""
    
    __tablename__ = "campaigns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, index=True)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    total_budget: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    objectives: Optional[str] = Field(default=None)
    target_audience: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Metadata
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Campaign timeline
    brief_deadline: Optional[date] = Field(default=None)
    content_deadline: Optional[date] = Field(default=None)
    posting_start_date: Optional[date] = Field(default=None)
    posting_end_date: Optional[date] = Field(default=None)
    report_due_date: Optional[date] = Field(default=None)
    
    # Campaign metrics (calculated fields)
    total_reach: Optional[int] = Field(default=None)
    total_engagement: Optional[int] = Field(default=None)
    average_engagement_rate: Optional[float] = Field(default=None)
    kol_count: int = Field(default=0)
    
    # Relationships
    creator: "User" = Relationship(back_populates="campaigns")
    client_briefs: List["ClientBrief"] = Relationship(back_populates="campaign")
    kpis: List["CampaignKPI"] = Relationship(back_populates="campaign")
    deliverables: List["Deliverable"] = Relationship(back_populates="campaign")
    campaign_kols: List["CampaignKOL"] = Relationship(back_populates="campaign")
    briefs: List["Brief"] = Relationship(back_populates="campaign")
    messages: List["Message"] = Relationship(back_populates="campaign")