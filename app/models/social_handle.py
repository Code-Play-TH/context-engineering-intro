"""Social media handle model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.kol import KOL


class SocialHandle(SQLModel, table=True):
    """Social media handle model for KOL profiles."""
    
    __tablename__ = "social_handles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kols.id", index=True)
    platform: str = Field(max_length=50, index=True)  # instagram, tiktok, youtube, twitter, facebook
    handle: str = Field(max_length=255)
    url: Optional[str] = Field(default=None, max_length=500)
    follower_count: Optional[int] = Field(default=None)
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    last_enriched_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    kol: Optional["KOL"] = Relationship(back_populates="social_handles")
