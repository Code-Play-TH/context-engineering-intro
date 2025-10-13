"""Campaign request/response schemas."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from app.models.campaign import CampaignStatus


class CampaignBase(BaseModel):
    """Base campaign schema."""
    name: str = Field(..., min_length=1, max_length=255)
    objectives: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    target_audience: Optional[dict] = None
    brief_deadline: Optional[date] = None
    content_deadline: Optional[date] = None
    posting_start_date: Optional[date] = None
    posting_end_date: Optional[date] = None
    report_due_date: Optional[date] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Campaign name cannot be empty')
        return v.strip()
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('Campaign end date must be after start date')
        return v
    
    @validator('brief_deadline')
    def validate_brief_deadline(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v >= values['start_date']:
                raise ValueError('Brief deadline must be before campaign start date')
        return v
    
    @validator('content_deadline')
    def validate_content_deadline(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v >= values['start_date']:
                raise ValueError('Content deadline must be before campaign start date')
        return v
    
    @validator('posting_end_date')
    def validate_posting_end_date(cls, v, values):
        if v and 'posting_start_date' in values and values['posting_start_date']:
            if v <= values['posting_start_date']:
                raise ValueError('Posting end date must be after posting start date')
        return v


class CampaignCreate(CampaignBase):
    """Campaign creation schema."""
    pass


class CampaignUpdate(BaseModel):
    """Campaign update schema."""
    name: Optional[str] = None
    objectives: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[Decimal] = None
    currency: Optional[str] = None
    target_audience: Optional[dict] = None
    brief_deadline: Optional[date] = None
    content_deadline: Optional[date] = None
    posting_start_date: Optional[date] = None
    posting_end_date: Optional[date] = None
    report_due_date: Optional[date] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(CampaignBase):
    """Campaign response schema."""
    id: int
    status: CampaignStatus
    total_reach: Optional[int] = None
    total_engagement: Optional[int] = None
    average_engagement_rate: Optional[float] = None
    kol_count: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Campaign list response schema."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int


class CampaignStatusChange(BaseModel):
    """Campaign status change schema."""
    status: CampaignStatus


class CampaignSummaryResponse(BaseModel):
    """Campaign summary response schema."""
    campaign: CampaignResponse
    kol_stats: dict
    deliverable_stats: dict
    kpi_stats: dict