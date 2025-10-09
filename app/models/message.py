from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.message_template import MessageType
import enum


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


class Message(Base):
    """
    Message model for tracking all communications with KOLs.
    Supports multiple communication channels (email, SMS, Line, Discord, etc.)
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    
    # Message content
    subject = Column(String(500))  # For email messages
    content = Column(Text, nullable=False)
    
    # Message metadata
    message_type = Column(Enum(MessageType), nullable=False, index=True)
    status = Column(Enum(MessageStatus), default=MessageStatus.DRAFT, index=True)
    priority = Column(Enum(MessagePriority), default=MessagePriority.NORMAL)
    
    # Recipients and sender
    recipient_email = Column(String(255))
    recipient_phone = Column(String(50))
    recipient_line_id = Column(String(255))
    recipient_discord_id = Column(String(255))
    sender_email = Column(String(255))
    sender_name = Column(String(255))
    
    # Relationships
    kol_id = Column(Integer, ForeignKey("kols.id"), nullable=True)  # Optional - can send to non-KOLs
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)  # Optional
    brief_id = Column(Integer, ForeignKey("briefs.id"), nullable=True)  # Optional
    template_id = Column(Integer, ForeignKey("message_templates.id"), nullable=True)
    
    # Message tracking
    sent_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # External service tracking
    external_id = Column(String(255))  # ID from email service, SMS provider, etc.
    external_status = Column(String(100))  # Status from external service
    
    # JSON field for additional message data
    # Example: {
    #   "attachments": [{"name": "brief.pdf", "url": "..."}],
    #   "tracking_data": {"opens": 1, "clicks": 2},
    #   "delivery_info": {"provider": "sendgrid", "message_id": "..."}
    # }
    message_data = Column(JSON, default=dict)
    
    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    kol = relationship("KOL", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")
    brief = relationship("Brief", back_populates="messages")
    template = relationship("MessageTemplate", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

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