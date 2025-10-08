"""Client brief model."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON


class ClientBrief(SQLModel, table=True):
    """Client brief model for campaign requirements."""
    
    __tablename__ = "client_briefs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(max_length=255)
    campaign_objective: str
    target_audience: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    budget: Optional[float] = None
    brand_guidelines: Optional[str] = None
    content_requirements: Optional[str] = None
    status: str = Field(default="draft", max_length=50)
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
