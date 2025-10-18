"""Campaign KPI model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import DECIMAL
from enum import Enum

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class KPIType(str, Enum):
    """KPI type enumeration."""
    REACH = "reach"
    IMPRESSIONS = "impressions"
    ENGAGEMENT = "engagement"
    ENGAGEMENT_RATE = "engagement_rate"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    CONVERSION_RATE = "conversion_rate"
    COST_PER_ENGAGEMENT = "cost_per_engagement"
    COST_PER_CLICK = "cost_per_click"
    COST_PER_CONVERSION = "cost_per_conversion"
    BRAND_AWARENESS = "brand_awareness"
    SENTIMENT_SCORE = "sentiment_score"


class KPIUnit(str, Enum):
    """KPI unit enumeration."""
    COUNT = "count"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    SCORE = "score"
    RATE = "rate"


class CampaignKPI(SQLModel, table=True):
    """Campaign KPI model for tracking performance metrics."""
    
    __tablename__ = "campaign_kpis"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    kpi_type: KPIType = Field(index=True)
    target_value: Decimal = Field(sa_column=Column(DECIMAL(15, 2)))
    actual_value: Optional[Decimal] = Field(default=None, sa_column=Column(DECIMAL(15, 2)))
    unit: KPIUnit = Field()
    
    # Progress tracking
    achievement_percentage: Optional[float] = Field(default=None)
    is_achieved: bool = Field(default=False)
    
    # Metadata
    description: Optional[str] = Field(default=None, max_length=500)
    priority: str = Field(default="medium", max_length=20)  # low, medium, high, critical
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    campaign: "Campaign" = Relationship(back_populates="kpis")
    
    def calculate_achievement_percentage(self) -> Optional[float]:
        """Calculate achievement percentage."""
        if self.actual_value is None or self.target_value == 0:
            return None
        
        percentage = float(self.actual_value / self.target_value * 100)
        return min(percentage, 100.0)  # Cap at 100%
    
    def update_achievement(self) -> None:
        """Update achievement status and percentage."""
        self.achievement_percentage = self.calculate_achievement_percentage()
        if self.achievement_percentage is not None:
            self.is_achieved = self.achievement_percentage >= 100.0
        self.updated_at = datetime.utcnow()