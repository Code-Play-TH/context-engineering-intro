"""
Configuration settings for the Factory ERP system.

Uses Pydantic Settings for environment variable management with validation.
"""

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    """
    
    # Application settings
    app_name: str = "Factory ERP System"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Database configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/factory_erp",
        description="PostgreSQL database URL"
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=50, ge=1, le=200)
    
    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        min_length=32,
        description="JWT secret key"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)
    
    # ERPNext integration settings
    erpnext_base_url: Optional[str] = Field(
        default=None,
        description="ERPNext instance base URL"
    )
    erpnext_api_key: Optional[str] = Field(
        default=None,
        description="ERPNext API key"
    )
    erpnext_api_secret: Optional[str] = Field(
        default=None,
        description="ERPNext API secret"
    )
    erpnext_timeout: int = Field(default=30, ge=1, le=300)
    
    # File upload settings
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    upload_dir: str = Field(default="uploads", description="Upload directory path")
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Validate that secret key is sufficiently secure."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith("postgresql"):
            raise ValueError("Database URL must use PostgreSQL")
        return v
    
    @validator("erpnext_base_url")
    def validate_erpnext_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate ERPNext URL format if provided."""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("ERPNext URL must start with http:// or https://")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings: Application configuration instance
    """
    return settings