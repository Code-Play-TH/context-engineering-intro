from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class MessageType(str, enum.Enum):
    """Message type enumeration"""
    EMAIL = "email"
    SMS = "sms"
    LINE = "line"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"


class MessageTemplate(Base):
    """
    Message template model for reusable message structures.
    Templates can be used for different communication channels.
    """
    __tablename__ = "message_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Template content
    subject = Column(String(500))  # For email templates
    content = Column(Text, nullable=False)
    
    # Template metadata
    message_type = Column(Enum(MessageType), nullable=False, index=True)
    category = Column(String(100))  # e.g., "brief_notification", "follow_up", "reminder"
    
    # JSON field for template variables and their default values
    # Example: {"kol_name": "", "campaign_name": "", "deadline": "", "brief_url": ""}
    variables = Column(JSON, default=dict)
    
    # Template settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="message_templates")
    messages = relationship("Message", back_populates="template")

    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, name='{self.name}', type='{self.message_type}')>"