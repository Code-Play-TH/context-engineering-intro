"""KOL request/response schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class SocialHandleBase(BaseModel):
    """Base social handle schema."""
    platform: str
    handle: str
    url: Optional[str] = None
    follower_count: Optional[int] = None
    is_verified: bool = False


class SocialHandleCreate(SocialHandleBase):
    """Social handle creation schema."""
    pass


class SocialHandleUpdate(BaseModel):
    """Social handle update schema."""
    platform: Optional[str] = None
    handle: Optional[str] = None
    url: Optional[str] = None
    follower_count: Optional[int] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class SocialHandleResponse(SocialHandleBase):
    """Social handle response schema."""
    id: int
    kol_id: int
    is_active: bool
    last_enriched_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class KOLBase(BaseModel):
    """Base KOL schema."""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    niche: List[str] = []
    tags: List[str] = []
    notes: Optional[str] = None


class KOLCreate(KOLBase):
    """KOL creation schema."""
    social_handles: List[SocialHandleCreate] = []


class KOLUpdate(BaseModel):
    """KOL update schema."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    niche: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class KOLResponse(KOLBase):
    """KOL response schema."""
    id: int
    tier: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    social_handles: List[SocialHandleResponse] = []
    
    class Config:
        from_attributes = True


class KOLListResponse(BaseModel):
    """KOL list response schema."""
    kols: List[KOLResponse]
    total: int
    page: int
    page_size: int
