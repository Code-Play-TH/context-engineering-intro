"""Campaign request/response schemas."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class KPIBase(BaseModel):
    """Base KPI schema."""
    kpi_type: str
    target_value: float
    unit: str


class KPICreate(KPIBase):
    """KPI creation schema."""
    pass


class KPIResponse(KPIBase):
    """KPI response schema."""
    id: int
    campaign_id: int
    actual_value: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeliverableBase(BaseModel):
    """Base deliverable schema."""
    deliverable_type: str
    quantity: int
    deadline: Optional[date] = None


class DeliverableCreate(DeliverableBase):
    """Deliverable creation schema."""
    pass


class DeliverableResponse(DeliverableBase):
    """Deliverable response schema."""
    id: int
    campaign_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CampaignBase(BaseModel):
    """Base campaign schema."""
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[float] = None
    currency: str = "USD"
    objectives: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None


class CampaignCreate(CampaignBase):
    """Campaign creation schema."""
    kpis: List[KPICreate] = []
    deliverables: List[DeliverableCreate] = []


class CampaignUpdate(BaseModel):
    """Campaign update schema."""
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[float] = None
    currency: Optional[str] = None
    objectives: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class CampaignResponse(CampaignBase):
    """Campaign response schema."""
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    kpis: List[KPIResponse] = []
    deliverables: List[DeliverableResponse] = []
    
    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Campaign list response schema."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int


class ClientBriefBase(BaseModel):
    """Base client brief schema."""
    client_name: str
    campaign_objective: str
    target_audience: Optional[Dict[str, Any]] = None
    budget: Optional[float] = None
    brand_guidelines: Optional[str] = None
    content_requirements: Optional[str] = None


class ClientBriefCreate(ClientBriefBase):
    """Client brief creation schema."""
    pass


class ClientBriefResponse(ClientBriefBase):
    """Client brief response schema."""
    id: int
    status: str
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True
