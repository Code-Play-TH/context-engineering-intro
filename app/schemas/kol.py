"""KOL request/response schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, Field
import re


class SocialHandleBase(BaseModel):
    """Base social handle schema."""
    platform: str = Field(..., pattern="^(instagram|tiktok|youtube|twitter|facebook)$")
    handle: str = Field(..., min_length=1, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    follower_count: Optional[int] = Field(None, ge=0)
    is_verified: bool = False
    
    @validator('handle')
    def validate_handle(cls, v):
        # Remove @ symbol if present
        if v.startswith('@'):
            v = v[1:]
        
        # Check for valid characters (alphanumeric, underscore, dot)
        if not re.match(r'^[a-zA-Z0-9._]+$', v):
            raise ValueError('Handle can only contain letters, numbers, underscore, and dot')
        
        return v
    
    @validator('url')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


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
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    niche: List[str] = Field(default=[], max_items=10)
    tags: List[str] = Field(default=[], max_items=20)
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Remove spaces and common separators
            phone = re.sub(r'[\s\-\(\)]', '', v)
            
            # Check if it's a valid phone format (starts with + and contains only digits)
            if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
                raise ValueError('Invalid phone number format. Use international format like +1234567890')
        
        return v
    
    @validator('niche', 'tags')
    def validate_string_lists(cls, v):
        if v:
            # Remove empty strings and strip whitespace
            cleaned = [item.strip() for item in v if item.strip()]
            return cleaned
        return v


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
