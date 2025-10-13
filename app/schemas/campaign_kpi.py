"""Campaign KPI request/response schemas."""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from app.models.campaign_kpi import KPIType, KPIUnit


class CampaignKPIBase(BaseModel):
    """Base campaign KPI schema."""
    kpi_type: KPIType
    target_value: Decimal = Field(..., gt=0)
    unit: KPIUnit
    description: Optional[str] = Field(None, max_length=500)
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")


class CampaignKPICreate(CampaignKPIBase):
    """Campaign KPI creation schema."""
    pass


class CampaignKPIUpdate(BaseModel):
    """Campaign KPI update schema."""
    target_value: Optional[Decimal] = Field(None, gt=0)
    actual_value: Optional[Decimal] = Field(None, ge=0)
    unit: Optional[KPIUnit] = None
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[str] = Field(None, regex="^(low|medium|high|critical)$")


class CampaignKPIResponse(CampaignKPIBase):
    """Campaign KPI response schema."""
    id: int
    campaign_id: int
    actual_value: Optional[Decimal] = None
    achievement_percentage: Optional[float] = None
    is_achieved: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True