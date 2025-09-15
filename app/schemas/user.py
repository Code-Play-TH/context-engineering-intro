"""
User-related Pydantic schemas for request/response validation.

Contains schemas for authentication, user management, and authorization.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Authentication schemas
class Token(BaseModel):
    """
    JWT token response schema.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenData(BaseModel):
    """
    Token payload data schema.
    """
    username: Optional[str] = None
    user_id: Optional[int] = None
    department: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """
    User login request schema.
    """
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """
    Login response schema with user info and token.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


# User schemas
class UserBase(BaseModel):
    """
    Base user schema with common fields.
    """
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    department_id: int = Field(gt=0)
    role_id: int = Field(gt=0)
    is_superuser: bool = False


class UserCreate(UserBase):
    """
    Schema for creating new users.
    """
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """
    Schema for updating user information.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, max_length=255)
    department_id: Optional[int] = Field(default=None, gt=0)
    role_id: Optional[int] = Field(default=None, gt=0)
    is_superuser: Optional[bool] = None
    is_active: Optional[bool] = None


class UserChangePassword(BaseModel):
    """
    Schema for changing user password.
    """
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=100)


class UserResponse(BaseModel):
    """
    User response schema (excludes sensitive data).
    """
    id: int
    username: str
    email: str
    full_name: str
    department_id: int
    role_id: int
    is_superuser: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    department: "DepartmentResponse"
    role: "RoleResponse"

    model_config = {"from_attributes": True}


# Department schemas
class DepartmentBase(BaseModel):
    """
    Base department schema.
    """
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=10)
    description: Optional[str] = Field(default=None, max_length=500)


class DepartmentCreate(DepartmentBase):
    """
    Schema for creating departments.
    """
    pass


class DepartmentUpdate(BaseModel):
    """
    Schema for updating departments.
    """
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    """
    Department response schema.
    """
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Role schemas
class RoleBase(BaseModel):
    """
    Base role schema.
    """
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    department_id: int = Field(gt=0)


class RoleCreate(RoleBase):
    """
    Schema for creating roles.
    """
    permissions: dict = Field(default_factory=dict, description="Role permissions")


class RoleUpdate(BaseModel):
    """
    Schema for updating roles.
    """
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    permissions: Optional[dict] = Field(default=None, description="Role permissions")
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    """
    Role response schema.
    """
    id: int
    name: str
    code: str
    description: Optional[str] = None
    department_id: int
    permissions: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    department: DepartmentResponse

    model_config = {"from_attributes": True}
    
    @property
    def permissions(self) -> dict:
        """Parse permissions from JSON string."""
        try:
            import json
            return json.loads(self.permissions_json) if hasattr(self, 'permissions_json') else {}
        except (json.JSONDecodeError, AttributeError):
            return {}


# Current user info schema
class CurrentUser(BaseModel):
    """
    Current authenticated user information.
    """
    id: int
    username: str
    email: str
    full_name: str
    department_code: str
    department_name: str
    role_code: str
    role_name: str
    is_superuser: bool
    permissions: dict
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Rebuild models to resolve forward references
LoginResponse.model_rebuild()
UserResponse.model_rebuild()
RoleResponse.model_rebuild()