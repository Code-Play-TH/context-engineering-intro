"""KOL (Key Opinion Leader) model."""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, ARRAY, String, Relationship

if TYPE_CHECKING:
    from app.models.social_handle import SocialHandle


class KOL(SQLModel, table=True):
    """KOL model for managing influencer profiles."""
    
    __tablename__ = "kols"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=255)
    niche: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    tier: Optional[str] = Field(default=None, max_length=50)  # nano, micro, mid, macro, mega
    tags: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    notes: Optional[str] = Field(default=None)
    status: str = Field(default="active", max_length=50)  # active, inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    social_handles: List["SocialHandle"] = Relationship(back_populates="kol")
