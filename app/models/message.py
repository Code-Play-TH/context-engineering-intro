from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
import enum


class MessageType(str, enum.Enum):
    """Message type enumeration"""
    EMAIL = "email"
    SMS = "sms"
    LINE = "line"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


class MessageStatus(str, enum.Enum):
    """Message status enumeration"""
    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"


class MessagePriority(str, enum.Enum):
    """Message priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Message(SQLModel, table=True):
    """
    Message model for tracking all communications with KOLs.
    Supports multiple communication channels (email, SMS, Line, Discord, etc.)
    """
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Message content
    subject: Optional[str] = Field(default=None, max_length=500)  # For email messages
    content: str
    
    # Message metadata
    message_type: MessageType = Field(index=True)
    status: MessageStatus = Field(default=MessageStatus.DRAFT, index=True)
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    
    # Recipients and sender
    recipient_email: Optional[str] = Field(default=None, max_length=255)
    recipient_phone: Optional[str] = Field(default=None, max_length=50)
    recipient_line_id: Optional[str] = Field(default=None, max_length=255)
    recipient_discord_id: Optional[str] = Field(default=None, max_length=255)
    sender_email: Optional[str] = Field(default=None, max_length=255)
    sender_name: Optional[str] = Field(default=None, max_length=255)
    
    # Relationships
    kol_id: Optional[int] = Field(default=None, foreign_key="kols.id")  # Optional - can send to non-KOLs
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id")  # Optional
    brief_id: Optional[int] = Field(default=None, foreign_key="briefs.id")  # Optional
    template_id: Optional[int] = Field(default=None, foreign_key="message_templates.id")
    
    # Message tracking
    sent_by: int = Field(foreign_key="users.id")
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # External service tracking
    external_id: Optional[str] = Field(default=None, max_length=255)  # ID from email service, SMS provider, etc.
    external_status: Optional[str] = Field(default=None, max_length=100)  # Status from external service
    
    # JSON field for additional message data
    # Example: {
    #   "attachments": [{"name": "brief.pdf", "url": "..."}],
    #   "tracking_data": {"opens": 1, "clicks": 2},
    #   "delivery_info": {"provider": "sendgrid", "message_id": "..."}
    # }
    message_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    # Scheduling
    scheduled_at: Optional[datetime] = None
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    kol: Optional["KOL"] = Relationship(back_populates="messages")
    campaign: Optional["Campaign"] = Relationship(back_populates="messages")
    brief: Optional["Brief"] = Relationship(back_populates="messages")
    # template: Optional["MessageTemplate"] = Relationship(back_populates="messages")
    # sender: Optional["User"] = Relationship(back_populates="sent_messages")

    def __repr__(self):
        return f"<Message(id={self.id}, type='{self.message_type}', status='{self.status}')>"

    @property
    def is_sent(self) -> bool:
        """Check if message has been sent"""
        return self.status in [MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.READ]

    @property
    def can_retry(self) -> bool:
        """Check if message can be retried"""
        return (
            self.status == MessageStatus.FAILED and 
            self.retry_count < self.max_retries
        )

    @property
    def recipient_display(self) -> str:
        """Get display name for recipient"""
        if self.kol:
            return self.kol.name
        elif self.recipient_email:
            return self.recipient_email
        elif self.recipient_phone:
            return self.recipient_phone
        else:
            return "Unknown Recipient"