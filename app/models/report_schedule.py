"""
Report Schedule model for automated report generation.
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, ARRAY, String
from enum import Enum


class ScheduleFrequency(str, Enum):
    """Schedule frequency enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CAMPAIGN_END = "campaign_end"


class ReportSchedule(SQLModel, table=True):
    """
    Report schedule model for automated report generation.
    
    Defines when and how often reports should be automatically
    generated and sent to specified recipients.
    """
    __tablename__ = "report_schedules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    template_id: int = Field(foreign_key="report_templates.id", index=True)
    frequency: ScheduleFrequency = Field(index=True)
    recipients: List[str] = Field(sa_column=Column(ARRAY(String)))  # Email addresses
    is_active: bool = Field(default=True, index=True)
    last_generated_at: Optional[datetime] = Field(default=None, index=True)
    next_generation_at: datetime = Field(index=True)
    created_by: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    
    @property
    def is_due(self) -> bool:
        """Check if the schedule is due for generation."""
        if not self.is_active:
            return False
        return datetime.utcnow() >= self.next_generation_at
    
    class Config:
        """SQLModel configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }