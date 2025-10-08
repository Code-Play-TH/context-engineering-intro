"""Campaign KPI model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class CampaignKPI(SQLModel, table=True):
    """Campaign KPI model for tracking campaign metrics."""
    
    __tablename__ = "campaign_kpis"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    kpi_type: str = Field(max_length=100)  # reach, engagement, conversions, etc.
    target_value: float
    actual_value: Optional[float] = None
    unit: str = Field(max_length=50)  # count, percentage, currency
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    campaign: Optional["Campaign"] = Relationship(back_populates="kpis")
