"""Client Brief request/response schemas."""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from app.models.client_brief import ClientBriefStatus


class ClientBriefBase(BaseModel):
    """Base client brief schema."""
    client_name: str = Field(..., min_length=1, max_length=255)
    campaign_objective: str = Field(..., min_length=1)
    target_audience: Optional[dict] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    brand_guidelines: Optional[str] = None
    content_requirements: Optional[str] = None
    campaign_start_date: Optional[datetime] = None
    campaign_end_date: Optional[datetime] = None
    content_deadline: Optional[datetime] = None
    platform_requirements: Optional[dict] = None
    kol_requirements: Optional[dict] = None
    deliverable_requirements: Optional[dict] = None
    
    @validator('client_name')
    def validate_client_name(cls, v):
        if not v.strip():
            raise ValueError('Client name cannot be empty')
        return v.strip()
    
    @validator('campaign_objective')
    def validate_campaign_objective(cls, v):
        if not v.strip():
            raise ValueError('Campaign objective cannot be empty')
        return v.strip()
    
    @validator('campaign_end_date')
    def validate_end_date(cls, v, values):
        if v and 'campaign_start_date' in values and values['campaign_start_date']:
            if v <= values['campaign_start_date']:
                raise ValueError('Campaign end date must be after start date')
        return v
    
    @validator('content_deadline')
    def validate_content_deadline(cls, v, values):
        if v and 'campaign_start_date' in values and values['campaign_start_date']:
            if v >= values['campaign_start_date']:
                raise ValueError('Content deadline must be before campaign start date')
        return v


class ClientBriefCreate(ClientBriefBase):
    """Client brief creation schema."""
    pass


class ClientBriefUpdate(BaseModel):
    """Client brief update schema."""
    client_name: Optional[str] = None
    campaign_objective: Optional[str] = None
    target_audience: Optional[dict] = None
    budget: Optional[Decimal] = None
    currency: Optional[str] = None
    brand_guidelines: Optional[str] = None
    content_requirements: Optional[str] = None
    campaign_start_date: Optional[datetime] = None
    campaign_end_date: Optional[datetime] = None
    content_deadline: Optional[datetime] = None
    platform_requirements: Optional[dict] = None
    kol_requirements: Optional[dict] = None
    deliverable_requirements: Optional[dict] = None
    status: Optional[ClientBriefStatus] = None


class ClientBriefResponse(ClientBriefBase):
    """Client brief response schema."""
    id: int
    status: ClientBriefStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClientBriefListResponse(BaseModel):
    """Client brief list response schema."""
    briefs: List[ClientBriefResponse]
    total: int
    page: int
    page_size: int


class ClientBriefApproval(BaseModel):
    """Client brief approval schema."""
    approved: bool
    rejection_reason: Optional[str] = None
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v, values):
        if not values.get('approved') and not v:
            raise ValueError('Rejection reason is required when rejecting a brief')
        return v