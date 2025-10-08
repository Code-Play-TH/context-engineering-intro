"""Deliverable model."""
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class Deliverable(SQLModel, table=True):
    """Deliverable model for campaign deliverables."""
    
    __tablename__ = "deliverables"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    deliverable_type: str = Field(max_length=100)  # post, story, video, etc.
    quantity: int
    deadline: Optional[date] = None
    status: str = Field(default="pending", max_length=50)  # pending, in_progress, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    campaign: Optional["Campaign"] = Relationship(back_populates="deliverables")
