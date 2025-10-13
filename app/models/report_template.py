"""
Report Template model for storing report template definitions.
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON, ARRAY, String
from enum import Enum


class TemplateType(str, Enum):
    """Template type enumeration."""
    POWERPOINT = "powerpoint"
    PDF = "pdf"


class ReportTemplate(SQLModel, table=True):
    """
    Report template model for storing template definitions.
    
    Templates define the structure and layout for generating
    PowerPoint and PDF reports with dynamic data population.
    """
    __tablename__ = "report_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    template_type: TemplateType = Field(index=True)
    is_shared: bool = Field(default=False, index=True)
    structure: dict = Field(sa_column=Column(JSON))  # Template layout definition
    variables: List[str] = Field(sa_column=Column(ARRAY(String)))  # {{campaign_name}}, etc.
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    usage_count: int = Field(default=0)
    
    class Config:
        """SQLModel configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }