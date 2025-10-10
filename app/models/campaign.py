"""Campaign model."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, JSON, Relationship

if TYPE_CHECKING:
    from app.models.campaign_kpi import CampaignKPI
    from app.models.deliverable import Deliverable
    from app.models.brief import Brief
    from app.models.message import Message
    from app.models.post import Post
    from app.models.performance_alert import PerformanceAlert


class Campaign(SQLModel, table=True):
    """Campaign model for managing KOL campaigns."""
    
    __tablename__ = "campaigns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    status: str = Field(default="draft", max_length=50)  # draft, pending_approval, active, completed, cancelled
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[float] = None
    currency: str = Field(default="USD", max_length=10)
    objectives: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Performance tracking fields
    hashtags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    keywords: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Relationships
    kpis: List["CampaignKPI"] = Relationship(back_populates="campaign")
    deliverables: List["Deliverable"] = Relationship(back_populates="campaign")
    briefs: List["Brief"] = Relationship(back_populates="campaign")
    messages: List["Message"] = Relationship(back_populates="campaign")
    posts: List["Post"] = Relationship(back_populates="campaign")
    performance_alerts: List["PerformanceAlert"] = Relationship(back_populates="campaign")
