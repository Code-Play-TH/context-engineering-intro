from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON


class BriefTemplate(SQLModel, table=True):
    """
    Brief template model for reusable brief structures.
    Templates can be used to quickly generate briefs for campaigns.
    """
    __tablename__ = "brief_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    
    # Template content with placeholders
    content: str
    
    # JSON field for template variables and their default values
    # Example: {"campaign_name": "", "deliverables": [], "deadline": "", "budget": ""}
    variables: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Template metadata
    category: Optional[str] = Field(default=None, max_length=100)  # e.g., "fashion", "beauty", "tech"
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    
    # Audit fields
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    # creator: Optional["User"] = Relationship(back_populates="brief_templates")
    briefs: List["Brief"] = Relationship(back_populates="template")

    def __repr__(self):
        return f"<BriefTemplate(id={self.id}, name='{self.name}')>"