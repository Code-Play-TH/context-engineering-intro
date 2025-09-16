"""
Communication and messaging database models.
Handles messages, follow-up scheduling, and communication tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum as PyEnum

from app.core.database import Base


class CommunicationChannel(PyEnum):
    """Communication channel enumeration."""
    EMAIL = "email"
    LINE = "line"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    PHONE = "phone"


class MessageStatus(PyEnum):
    """Message status enumeration."""
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    SPAM = "spam"


class ScheduleStatus(PyEnum):
    """Follow-up schedule status enumeration."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Message(Base):
    """
    Message model for tracking all communications with KOLs.
    """
    __tablename__ = "messages"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"), nullable=True, index=True)

    # Message content and metadata
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[CommunicationChannel] = mapped_column(String(50), nullable=False, index=True)

    # Template information
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("message_templates.id"), nullable=True)
    template_variables: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Variables used for template rendering"
    )

    # Delivery information
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status tracking
    status: Mapped[MessageStatus] = mapped_column(String(50), nullable=False, default=MessageStatus.DRAFT, index=True)

    # Timing information
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # Response tracking
    response_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    response_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # External provider information
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_response: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Response data from email/messaging provider"
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Message metadata
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1=highest, 10=lowest
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    # Attachments and rich content
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="File attachments metadata"
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    kol = relationship("KOL", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")
    template = relationship("MessageTemplate", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by])

    def is_overdue(self) -> bool:
        """Check if scheduled message is overdue."""
        if not self.scheduled_for or self.status != MessageStatus.QUEUED:
            return False
        return self.scheduled_for < datetime.utcnow()

    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return (
            self.status == MessageStatus.FAILED and
            self.retry_count < self.max_retries
        )

    def mark_as_sent(self, provider_message_id: str = None, provider_name: str = None) -> None:
        """Mark message as sent."""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.utcnow()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        if provider_name:
            self.provider_name = provider_name

    def mark_as_delivered(self, delivered_at: datetime = None) -> None:
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = delivered_at or datetime.utcnow()

    def mark_as_read(self, read_at: datetime = None) -> None:
        """Mark message as read."""
        self.status = MessageStatus.READ
        self.read_at = read_at or datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, kol_id={self.kol_id}, channel='{self.channel}', status='{self.status}')>"


class FollowUpSchedule(Base):
    """
    Follow-up schedule model for automated follow-up communications.
    """
    __tablename__ = "follow_up_schedules"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"), nullable=False, index=True)

    # Trigger information
    trigger_event: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Event that triggers this follow-up (brief_sent, no_response_1_day, etc.)"
    )

    trigger_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("messages.id"), nullable=True)

    # Scheduling information
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Follow-up configuration
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    delay_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Message template and content
    message_template_id: Mapped[int] = mapped_column(ForeignKey("message_templates.id"), nullable=False)
    custom_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Channel preferences
    preferred_channel: Mapped[CommunicationChannel] = mapped_column(String(50), nullable=False)
    fallback_channels: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Fallback communication channels if preferred fails"
    )

    # Status and execution
    status: Mapped[ScheduleStatus] = mapped_column(String(50), nullable=False, default=ScheduleStatus.PENDING, index=True)

    # Execution results
    executed_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("messages.id"), nullable=True)
    execution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Follow-up rules
    stop_on_response: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="follow_up_schedules")
    kol = relationship("KOL", back_populates="follow_up_schedules")
    message_template = relationship("MessageTemplate", foreign_keys=[message_template_id])
    trigger_message = relationship("Message", foreign_keys=[trigger_message_id])
    executed_message = relationship("Message", foreign_keys=[executed_message_id])
    creator = relationship("User", foreign_keys=[created_by])

    def is_due(self) -> bool:
        """Check if follow-up is due for execution."""
        return (
            self.status == ScheduleStatus.SCHEDULED and
            self.scheduled_for <= datetime.utcnow()
        )

    def is_overdue(self) -> bool:
        """Check if follow-up is overdue."""
        return (
            self.status == ScheduleStatus.SCHEDULED and
            self.scheduled_for < datetime.utcnow() - timedelta(hours=1)
        )

    def can_execute(self) -> bool:
        """Check if follow-up can be executed."""
        return (
            self.status in [ScheduleStatus.PENDING, ScheduleStatus.SCHEDULED] and
            self.attempt_count < self.max_attempts
        )

    def schedule(self, base_datetime: datetime = None) -> None:
        """Schedule the follow-up based on delay configuration."""
        base_time = base_datetime or datetime.utcnow()
        self.scheduled_for = base_time + timedelta(days=self.delay_days, hours=self.delay_hours)
        self.status = ScheduleStatus.SCHEDULED

    def execute(self, message_id: int) -> None:
        """Mark follow-up as executed."""
        self.status = ScheduleStatus.EXECUTED
        self.executed_at = datetime.utcnow()
        self.executed_message_id = message_id
        self.attempt_count += 1

    def cancel(self, reason: str = None) -> None:
        """Cancel the follow-up."""
        self.status = ScheduleStatus.CANCELLED
        if reason:
            self.execution_notes = reason

    def __repr__(self) -> str:
        return f"<FollowUpSchedule(id={self.id}, campaign_id={self.campaign_id}, kol_id={self.kol_id}, trigger='{self.trigger_event}')>"


class MessageTemplate(Base):
    """
    Message template model for reusable communication templates.
    """
    __tablename__ = "message_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template content
    subject_template: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_template: Mapped[str] = mapped_column(Text, nullable=False)

    # Template configuration
    channel: Mapped[CommunicationChannel] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Template variables and validation
    required_variables: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Required template variables"
    )

    optional_variables: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Optional template variables"
    )

    default_values: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Default values for template variables"
    )

    # Template metadata
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    # Template status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="template")
    follow_up_schedules = relationship("FollowUpSchedule", back_populates="message_template")
    creator = relationship("User", foreign_keys=[created_by])

    def render_subject(self, variables: Dict[str, Any]) -> str:
        """Render template subject with provided variables."""
        if not self.subject_template:
            return ""

        from jinja2 import Template
        template = Template(self.subject_template)
        return template.render(**variables)

    def render_content(self, variables: Dict[str, Any]) -> str:
        """Render template content with provided variables."""
        from jinja2 import Template
        template = Template(self.content_template)
        return template.render(**variables)

    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are provided."""
        missing_variables = []
        for required_var in self.required_variables:
            if required_var not in variables:
                missing_variables.append(required_var)
        return missing_variables

    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<MessageTemplate(id={self.id}, name='{self.name}', channel='{self.channel}')>"


# Indexes for performance optimization
Index("idx_message_kol_campaign", Message.kol_id, Message.campaign_id)
Index("idx_message_status_sent", Message.status, Message.sent_at)
Index("idx_message_channel_status", Message.channel, Message.status)
Index("idx_message_scheduled", Message.scheduled_for, Message.status)

Index("idx_followup_schedule_due", FollowUpSchedule.scheduled_for, FollowUpSchedule.status)
Index("idx_followup_trigger_status", FollowUpSchedule.trigger_event, FollowUpSchedule.status)
Index("idx_followup_campaign_kol", FollowUpSchedule.campaign_id, FollowUpSchedule.kol_id)

Index("idx_template_channel_active", MessageTemplate.channel, MessageTemplate.is_active)
Index("idx_template_category_active", MessageTemplate.category, MessageTemplate.is_active)