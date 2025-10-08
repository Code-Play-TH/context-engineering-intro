"""Authentication request/response schemas."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: str
