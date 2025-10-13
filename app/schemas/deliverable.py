"""Deliverable request/response schemas."""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.models.deliverable import DeliverableType, DeliverableStatus


class DeliverableBase(BaseModel):
    """Base deliverable schema."""
    deliverable_type: DeliverableType
    quantity: int = Field(..., gt=0)
    deadline: Optional[date] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    platform_specific_requirements: Optional[str] = None
    hashtags: Optional[str] = None
    mentions: Optional[str] = None
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")


class DeliverableCreate(DeliverableBase):
    """Deliverable creation schema."""
    pass


class DeliverableUpdate(BaseModel):
    """Deliverable update schema."""
    quantity: Optional[int] = Field(None, gt=0)
    deadline: Optional[date] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    platform_specific_requirements: Optional[str] = None
    hashtags: Optional[str] = None
    mentions: Optional[str] = None
    priority: Optional[str] = Field(None, regex="^(low|medium|high|critical)$")
    status: Optional[DeliverableStatus] = None
    submitted_count: Optional[int] = Field(None, ge=0)
    approved_count: Optional[int] = Field(None, ge=0)
    published_count: Optional[int] = Field(None, ge=0)
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class DeliverableResponse(DeliverableBase):
    """Deliverable response schema."""
    id: int
    campaign_id: int
    status: DeliverableStatus
    submitted_count: int
    approved_count: int
    published_count: int
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    completion_percentage: float
    is_overdue: bool
    
    class Config:
        from_attributes = True