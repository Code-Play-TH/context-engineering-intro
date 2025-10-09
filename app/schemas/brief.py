"""Brief schemas for API requests and responses."""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.brief import BriefStatus


# Brief Template Schemas
class BriefTemplateBase(BaseModel):
    """Base brief template schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    variables: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_default: bool = False


class BriefTemplateCreate(BriefTemplateBase):
    """Schema for creating a brief template."""
    pass


class BriefTemplateUpdate(BaseModel):
    """Schema for updating a brief template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[Dict[str, Any]] = None
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class BriefTemplateResponse(BriefTemplateBase):
    """Schema for brief template responses."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Brief Schemas
class BriefBase(BaseModel):
    """Base brief schema."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    brief_data: Dict[str, Any] = Field(default_factory=dict)
    internal_notes: Optional[str] = None


class BriefCreate(BriefBase):
    """Schema for creating a brief."""
    campaign_id: int
    kol_id: int
    template_id: Optional[int] = None


class BriefUpdate(BaseModel):
    """Schema for updating a brief."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    brief_data: Optional[Dict[str, Any]] = None
    internal_notes: Optional[str] = None
    kol_feedback: Optional[str] = None


class BriefStatusUpdate(BaseModel):
    """Schema for updating brief status."""
    status: BriefStatus
    notes: Optional[str] = None


class BriefResponse(BriefBase):
    """Schema for brief responses."""
    id: int
    status: BriefStatus
    campaign_id: int
    kol_id: int
    template_id: Optional[int] = None
    created_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    kol_feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BriefWithRelations(BriefResponse):
    """Brief response with related data."""
    campaign_name: Optional[str] = None
    kol_name: Optional[str] = None
    template_name: Optional[str] = None
    creator_name: Optional[str] = None
    approver_name: Optional[str] = None


# Brief Generation Schemas
class GenerateBriefFromTemplate(BaseModel):
    """Schema for generating brief from template."""
    template_id: int
    campaign_id: int
    kol_id: int
    variable_values: Dict[str, Any] = Field(default_factory=dict)
    custom_content: Optional[str] = None


class BulkBriefCreate(BaseModel):
    """Schema for creating briefs in bulk."""
    campaign_id: int
    kol_ids: List[int] = Field(..., min_items=1)
    template_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    brief_data: Dict[str, Any] = Field(default_factory=dict)


# Filter and List Schemas
class BriefFilters(BaseModel):
    """Schema for brief filtering."""
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    status: Optional[BriefStatus] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    template_id: Optional[int] = None
    search: Optional[str] = None  # Search in title and content
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class BriefListResponse(BaseModel):
    """Schema for paginated brief list response."""
    briefs: List[BriefWithRelations]
    total: int
    page: int
    page_size: int
    total_pages: int


class BriefTemplateListResponse(BaseModel):
    """Schema for paginated brief template list response."""
    templates: List[BriefTemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Statistics Schemas
class BriefStats(BaseModel):
    """Brief statistics schema."""
    total_briefs: int
    by_status: Dict[str, int]
    by_campaign: Dict[str, int]
    recent_activity: List[Dict[str, Any]]