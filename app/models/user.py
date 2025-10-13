"""
User model for authentication and authorization
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import Enum as SQLAlchemyEnum
from app.models.enums import Role

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken
    from app.models.brief import Brief
    from app.models.message import Message
    from app.models.campaign import Campaign
    from app.models.client_brief import ClientBrief
    from app.models.campaign_kol import CampaignKOL


class User(SQLModel, table=True):
    """
    User model for authentication and role-based access control.
    
    Attributes:
        id: Primary key
        email: Unique email address for login
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role (admin, campaign_manager, account_executive, viewer)
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        last_login_at: Timestamp of last successful login
        failed_login_attempts: Counter for failed login attempts (for rate limiting)
        locked_until: Timestamp until which account is locked (after failed attempts)
    """
    __tablename__ = "user"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: str = Field(max_length=255)
    role: str = Field(
        default="viewer",
        sa_column=Column(
            SQLAlchemyEnum(
                'admin',
                'campaign_manager',
                'account_executive',
                'viewer',
                name='role',
                create_constraint=True,
                native_enum=True
            ),
            nullable=False
        )
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    
    # Relationships
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
    
    # Campaign relationships
    campaigns: List["Campaign"] = Relationship(back_populates="creator")
    client_briefs: List["ClientBrief"] = Relationship(back_populates="creator")
    approved_client_briefs: List["ClientBrief"] = Relationship(
        back_populates="approver",
        sa_relationship_kwargs={"foreign_keys": "[ClientBrief.approved_by]"}
    )
    assigned_campaign_kols: List["CampaignKOL"] = Relationship(back_populates="assigner")
    
    # Brief relationships (commented out to avoid circular import issues)
    # created_briefs: List["Brief"] = Relationship(back_populates="creator")
    # approved_briefs: List["Brief"] = Relationship(back_populates="approver")
    
    # Message relationships (commented out to avoid circular import issues)
    # sent_messages: List["Message"] = Relationship(back_populates="sender")
