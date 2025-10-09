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
    
    # Brief relationships (will be added when brief models are imported)
    # brief_templates: List["BriefTemplate"] = Relationship(back_populates="creator")
    # created_briefs: List["Brief"] = Relationship(back_populates="creator", foreign_keys="Brief.created_by")
    # approved_briefs: List["Brief"] = Relationship(back_populates="approver", foreign_keys="Brief.approved_by")
    
    # Message relationships (will be added when message models are imported)
    # message_templates: List["MessageTemplate"] = Relationship(back_populates="creator")
    # sent_messages: List["Message"] = Relationship(back_populates="sender")
