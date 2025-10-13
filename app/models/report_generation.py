"""
Report Generation model for tracking report generation jobs.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum


class ReportType(str, Enum):
    """Report type enumeration."""
    POWERPOINT = "powerpoint"
    PDF = "pdf"


class GenerationStatus(str, Enum):
    """Report generation status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportGeneration(SQLModel, table=True):
    """
    Report generation model for tracking report generation jobs.
    
    Tracks the status and metadata of report generation requests,
    including file paths and download URLs with expiration.
    """
    __tablename__ = "report_generations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    template_id: int = Field(foreign_key="report_templates.id", index=True)
    report_type: ReportType = Field(index=True)
    status: GenerationStatus = Field(default=GenerationStatus.PENDING, index=True)
    file_path: Optional[str] = Field(default=None, max_length=500)
    download_url: Optional[str] = Field(default=None, max_length=500)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    generated_by: int = Field(foreign_key="user.id", index=True)
    generated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)  # Download link expiry
    
    def __init__(self, **data):
        super().__init__(**data)
        # Set expiry to 24 hours from creation if not specified
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)
    
    @property
    def is_expired(self) -> bool:
        """Check if the download link has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    class Config:
        """SQLModel configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }