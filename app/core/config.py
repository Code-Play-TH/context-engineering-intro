"""
Core configuration settings for KOL Influencer Management System.
Using pydantic-settings for environment variable management.
"""

from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable validation."""

    # Application settings
    APP_NAME: str = "KOL Influencer Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(False, description="Debug mode")
    ENVIRONMENT: str = Field("development", description="Environment (development, staging, production)")

    # Server settings
    HOST: str = Field("0.0.0.0", description="Server host")
    PORT: int = Field(8000, description="Server port")

    # Database settings
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_ECHO: bool = Field(False, description="SQLAlchemy echo mode")
    DATABASE_POOL_SIZE: int = Field(10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(20, description="Database max overflow connections")

    # Redis settings
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis URL for caching")
    REDIS_CELERY_BROKER_URL: str = Field("redis://localhost:6379/1", description="Redis URL for Celery broker")
    REDIS_CELERY_BACKEND_URL: str = Field("redis://localhost:6379/2", description="Redis URL for Celery backend")

    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ALGORITHM: str = Field("HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Access token expiration in minutes")

    # Social Media API Keys
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = Field(None, description="Instagram Graph API access token")
    YOUTUBE_API_KEY: Optional[str] = Field(None, description="YouTube Data API v3 key")
    TWITTER_BEARER_TOKEN: Optional[str] = Field(None, description="Twitter API v2 bearer token")
    TIKTOK_ACCESS_TOKEN: Optional[str] = Field(None, description="TikTok API access token")
    FACEBOOK_ACCESS_TOKEN: Optional[str] = Field(None, description="Facebook Graph API access token")

    # Communication API Keys
    SENDGRID_API_KEY: Optional[str] = Field(None, description="SendGrid API key")
    AWS_SES_ACCESS_KEY_ID: Optional[str] = Field(None, description="AWS SES access key")
    AWS_SES_SECRET_ACCESS_KEY: Optional[str] = Field(None, description="AWS SES secret key")
    AWS_SES_REGION: str = Field("us-east-1", description="AWS SES region")
    DISCORD_BOT_TOKEN: Optional[str] = Field(None, description="Discord bot token")
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = Field(None, description="Line Messaging API access token")
    LINE_CHANNEL_SECRET: Optional[str] = Field(None, description="Line Messaging API channel secret")

    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(60, description="API rate limit per minute")
    SOCIAL_MEDIA_RATE_LIMITS: Dict[str, int] = Field(
        default_factory=lambda: {
            "instagram": 200,  # requests per hour
            "youtube": 10000,  # units per day
            "twitter": 300,    # requests per 15 minutes
            "tiktok": 100,     # requests per hour
            "facebook": 200    # requests per hour
        },
        description="Rate limits for social media APIs"
    )

    # Celery Configuration
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/2", description="Celery result backend URL")
    CELERY_TASK_SERIALIZER: str = Field("json", description="Celery task serializer")
    CELERY_RESULT_SERIALIZER: str = Field("json", description="Celery result serializer")
    CELERY_ACCEPT_CONTENT: list = Field(["json"], description="Celery accepted content types")
    CELERY_TIMEZONE: str = Field("UTC", description="Celery timezone")
    CELERY_ENABLE_UTC: bool = Field(True, description="Celery UTC mode")

    # Content Monitoring
    AI_CONTENT_ANALYSIS_API_KEY: Optional[str] = Field(None, description="AI service API key for content analysis")
    CONTENT_DETECTION_CONFIDENCE_THRESHOLD: float = Field(0.6, description="Minimum confidence for content detection")

    # File Storage
    UPLOAD_DIR: str = Field("uploads", description="Directory for file uploads")
    MAX_UPLOAD_SIZE: int = Field(10 * 1024 * 1024, description="Maximum file upload size (10MB)")

    # Monitoring and Logging
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    SENTRY_DSN: Optional[str] = Field(None, description="Sentry DSN for error tracking")
    PROMETHEUS_METRICS_ENABLED: bool = Field(True, description="Enable Prometheus metrics")

    # GDPR Compliance
    DATA_RETENTION_DAYS: int = Field(365, description="Data retention period in days")
    GDPR_COMPLIANCE_ENABLED: bool = Field(True, description="Enable GDPR compliance features")

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL")
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Validate secret key length."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_environments}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the database URL with proper async driver."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_celery_config() -> Dict[str, Any]:
    """Get Celery configuration."""
    return {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_serializer": settings.CELERY_TASK_SERIALIZER,
        "result_serializer": settings.CELERY_RESULT_SERIALIZER,
        "accept_content": settings.CELERY_ACCEPT_CONTENT,
        "timezone": settings.CELERY_TIMEZONE,
        "enable_utc": settings.CELERY_ENABLE_UTC,
        "task_routes": {
            "app.tasks.social_media_tasks.*": {"queue": "social_media"},
            "app.tasks.communication_tasks.*": {"queue": "communication"},
            "app.tasks.content_monitoring_tasks.*": {"queue": "content_monitoring"},
            "app.tasks.reporting_tasks.*": {"queue": "reporting"},
        },
        "task_annotations": {
            "*": {"rate_limit": "10/s"},
            "app.tasks.social_media_tasks.collect_performance_data": {"rate_limit": "5/m"},
            "app.tasks.communication_tasks.send_follow_up": {"rate_limit": "20/m"},
        },
        # Error handling and retries
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        "task_default_retry_delay": 60,
        "task_max_retries": 3,
    }


def get_cors_origins() -> list:
    """Get CORS origins based on environment."""
    if settings.ENVIRONMENT == "development":
        return ["http://localhost:3000", "http://localhost:8080"]
    elif settings.ENVIRONMENT == "staging":
        return ["https://staging.kolsystem.com"]
    else:  # production
        return ["https://kolsystem.com", "https://app.kolsystem.com"]


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.ENVIRONMENT == "development"