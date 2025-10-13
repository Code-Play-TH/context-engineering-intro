"""KOL (Key Opinion Leader) model."""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, ARRAY, String, Relationship

if TYPE_CHECKING:
    from app.models.social_handle import SocialHandle
    from app.models.brief import Brief
    from app.models.message import Message
    from app.models.scraping_schedule import ScrapingSchedule
    from app.models.kol_metrics import KOLMetrics
    from app.models.post import Post
    from app.models.performance_alert import PerformanceAlert
    from app.models.campaign_kol import CampaignKOL


class KOL(SQLModel, table=True):
    """KOL model for managing influencer profiles."""
    
    __tablename__ = "kols"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=255)
    niche: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    tier: Optional[str] = Field(default=None, max_length=50)  # nano, micro, mid, macro, mega
    tags: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    notes: Optional[str] = Field(default=None)
    status: str = Field(default="active", max_length=50)  # active, inactive, merged
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Performance tracking fields
    last_scraped_at: Optional[datetime] = Field(default=None)
    last_post_check_at: Optional[datetime] = Field(default=None)
    average_engagement_rate: Optional[float] = Field(default=None)
    
    # Relationships
    social_handles: List["SocialHandle"] = Relationship(back_populates="kol")
    briefs: List["Brief"] = Relationship(back_populates="kol")
    messages: List["Message"] = Relationship(back_populates="kol")
    scraping_schedule: Optional["ScrapingSchedule"] = Relationship(back_populates="kol")
    metrics: List["KOLMetrics"] = Relationship(back_populates="kol")
    posts: List["Post"] = Relationship(back_populates="kol")
    performance_alerts: List["PerformanceAlert"] = Relationship(back_populates="kol")
    campaign_kols: List["CampaignKOL"] = Relationship(back_populates="kol")
