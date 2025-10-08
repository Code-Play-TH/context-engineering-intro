"""RefreshToken model for JWT token rotation."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(SQLModel, table=True):
    """RefreshToken model for managing JWT refresh tokens with rotation."""
    
    __tablename__ = "refresh_tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(max_length=255, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = Field(default=False)
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="refresh_tokens")
