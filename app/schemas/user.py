"""User request/response schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.enums import Role


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str
    role: Role


class UserCreate(UserBase):
    """User creation schema."""
    password: str


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
