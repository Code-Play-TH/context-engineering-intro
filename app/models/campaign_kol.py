"""Campaign KOL relationship model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import DECIMAL
from enum import Enum

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.kol import KOL
    from app.models.user import User


class CampaignKOLStatus(str, Enum):
    """Campaign KOL status enumeration."""
    SHORTLISTED = "shortlisted"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    NEGOTIATING = "negotiating"
    CONTRACTED = "contracted"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignKOL(SQLModel, table=True):
    """Campaign KOL relationship model."""
    
    __tablename__ = "campaign_kols"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    kol_id: int = Field(foreign_key="kols.id", index=True)
    status: CampaignKOLStatus = Field(default=CampaignKOLStatus.SHORTLISTED, index=True)
    
    # Financial terms
    fee: Optional[Decimal] = Field(default=None, sa_column=Column(DECIMAL(10, 2)))
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = Field(default=None)
    
    # Assignment details
    notes: Optional[str] = Field(default=None)
    assigned_by: int = Field(foreign_key="users.id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Response tracking
    responded_at: Optional[datetime] = Field(default=None)
    response_notes: Optional[str] = Field(default=None)
    decline_reason: Optional[str] = Field(default=None)
    
    # Contract details
    contract_signed_at: Optional[datetime] = Field(default=None)
    contract_expires_at: Optional[datetime] = Field(default=None)
    
    # Performance tracking
    deliverables_completed: int = Field(default=0)
    total_deliverables: int = Field(default=0)
    performance_score: Optional[float] = Field(default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    campaign: "Campaign" = Relationship(back_populates="campaign_kols")
    kol: "KOL" = Relationship(back_populates="campaign_kols")
    assigner: "User" = Relationship(back_populates="assigned_campaign_kols")
    
    @property
    def completion_percentage(self) -> float:
        """Calculate deliverable completion percentage."""
        if self.total_deliverables == 0:
            return 0.0
        return (self.deliverables_completed / self.total_deliverables) * 100
    
    def update_status_based_on_progress(self) -> None:
        """Update status based on deliverable progress."""
        if self.status == CampaignKOLStatus.ACTIVE:
            if self.deliverables_completed >= self.total_deliverables:
                self.status = CampaignKOLStatus.COMPLETED
        
        self.updated_at = datetime.utcnow()