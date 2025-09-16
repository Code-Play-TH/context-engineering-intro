"""
Communication Pydantic V2 schemas for validation and serialization.
Handles messages, templates, and follow-up scheduling with custom validators.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import re
from email_validator import validate_email, EmailNotValidError

from app.models.communication import CommunicationChannel, MessageStatus, ScheduleStatus


class MessageBase(BaseModel):
    """Base message schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    kol_id: int = Field(..., gt=0, description="KOL ID")
    campaign_id: Optional[int] = Field(None, gt=0, description="Campaign ID")
    subject: Optional[str] = Field(None, max_length=255, description="Message subject")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    channel: CommunicationChannel = Field(..., description="Communication channel")
    recipient: str = Field(..., min_length=1, max_length=255, description="Recipient address")
    sender: Optional[str] = Field(None, max_length=255, description="Sender address")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled send time")
    priority: int = Field(5, ge=1, le=10, description="Message priority (1=highest, 10=lowest)")
    tags: List[str] = Field(default_factory=list, description="Message tags")

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, v: str, info) -> str:
        """Validate recipient based on communication channel."""
        channel = info.data.get("channel") if hasattr(info, "data") else None

        if channel == CommunicationChannel.EMAIL:
            try:
                validate_email(v)
            except EmailNotValidError:
                raise ValueError("Invalid email address format")
            return v.lower()

        elif channel == CommunicationChannel.PHONE:
            # Remove all non-digit characters for validation
            digits_only = re.sub(r'\D', '', v)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError("Phone number must be between 10 and 15 digits")
            return v

        elif channel in [CommunicationChannel.DISCORD, CommunicationChannel.TELEGRAM]:
            # Validate social handle format
            if v.startswith("@"):
                v = v[1:]
            if not re.match(r'^[a-zA-Z0-9._-]+$', v):
                raise ValueError("Handle can only contain letters, numbers, dots, underscores, and hyphens")
            return v

        return v

    @field_validator("sender")
    @classmethod
    def validate_sender(cls, v: Optional[str], info) -> Optional[str]:
        """Validate sender based on communication channel."""
        if v is None:
            return v

        channel = info.data.get("channel") if hasattr(info, "data") else None

        if channel == CommunicationChannel.EMAIL:
            try:
                validate_email(v)
            except EmailNotValidError:
                raise ValueError("Invalid sender email address format")
            return v.lower()

        return v

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate scheduled time is in the future."""
        if v is None:
            return v

        if v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate message tags."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")

        validated_tags = []
        for tag in v:
            if not tag or len(tag.strip()) == 0:
                continue
            if len(tag) > 50:
                raise ValueError("Tag cannot exceed 50 characters")
            if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                raise ValueError("Tags can only contain letters, numbers, underscores, and hyphens")
            validated_tags.append(tag.lower())

        return validated_tags


class AttachmentCreate(BaseModel):
    """Schema for message attachments."""
    filename: str = Field(..., min_length=1, max_length=255, description="File name")
    file_size: int = Field(..., gt=0, le=25*1024*1024, description="File size in bytes (max 25MB)")
    content_type: str = Field(..., description="MIME content type")
    file_url: Optional[str] = Field(None, description="File storage URL")
    file_data: Optional[str] = Field(None, description="Base64 encoded file data")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        allowed_types = {
            "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "text/plain", "text/csv", "application/json"
        }

        if v not in allowed_types:
            raise ValueError(f"Content type '{v}' is not allowed")

        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename."""
        # Check for dangerous characters
        if re.search(r'[<>:"/\\|?*]', v):
            raise ValueError("Filename contains invalid characters")

        # Must have extension
        if '.' not in v:
            raise ValueError("Filename must have an extension")

        return v


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    template_id: Optional[int] = Field(None, gt=0, description="Message template ID")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    attachments: List[AttachmentCreate] = Field(default_factory=list, description="Message attachments")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")

    @field_validator("attachments")
    @classmethod
    def validate_attachments(cls, v: List[AttachmentCreate]) -> List[AttachmentCreate]:
        """Validate attachments."""
        if len(v) > 5:
            raise ValueError("Maximum 5 attachments allowed")

        total_size = sum(attachment.file_size for attachment in v)
        if total_size > 50 * 1024 * 1024:  # 50MB total
            raise ValueError("Total attachment size cannot exceed 50MB")

        return v

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage."""
        data = self.model_dump()

        # Convert attachments to dict format
        if self.attachments:
            data["attachments"] = [attachment.model_dump() for attachment in self.attachments]

        return data


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    model_config = ConfigDict(from_attributes=True)

    subject: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    scheduled_for: Optional[datetime] = Field(None)
    priority: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = Field(None)
    status: Optional[MessageStatus] = Field(None)

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate scheduled time is in the future."""
        if v is None:
            return v

        if v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        return v


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    status: MessageStatus
    template_id: Optional[int] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)

    # Delivery tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    # Response tracking
    response_received: bool = False
    response_at: Optional[datetime] = None
    response_content: Optional[str] = None

    # Provider information
    provider_message_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_response: Dict[str, Any] = Field(default_factory=dict)

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Attachments
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    @computed_field
    @property
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.status == MessageStatus.FAILED and self.retry_count < self.max_retries

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if scheduled message is overdue."""
        if not self.scheduled_for or self.status != MessageStatus.QUEUED:
            return False
        return self.scheduled_for < datetime.utcnow()

    @computed_field
    @property
    def delivery_duration(self) -> Optional[timedelta]:
        """Calculate time between sent and delivered."""
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None


class MessageTemplateBase(BaseModel):
    """Base message template schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    subject_template: Optional[str] = Field(None, max_length=255, description="Subject template")
    content_template: str = Field(..., min_length=1, max_length=10000, description="Content template")
    channel: CommunicationChannel = Field(..., description="Communication channel")
    category: Optional[str] = Field(None, max_length=100, description="Template category")
    required_variables: List[str] = Field(default_factory=list, description="Required variables")
    optional_variables: List[str] = Field(default_factory=list, description="Optional variables")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default variable values")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    language: str = Field("en", description="Template language")

    @field_validator("content_template")
    @classmethod
    def validate_content_template(cls, v: str) -> str:
        """Validate Jinja2 template syntax."""
        try:
            from jinja2 import Template
            Template(v)
        except Exception as e:
            raise ValueError(f"Invalid template syntax: {str(e)}")
        return v

    @field_validator("subject_template")
    @classmethod
    def validate_subject_template(cls, v: Optional[str]) -> Optional[str]:
        """Validate subject template syntax."""
        if v is None:
            return v

        try:
            from jinja2 import Template
            Template(v)
        except Exception as e:
            raise ValueError(f"Invalid subject template syntax: {str(e)}")
        return v

    @field_validator("required_variables")
    @classmethod
    def validate_required_variables(cls, v: List[str]) -> List[str]:
        """Validate required variables list."""
        validated_vars = []
        for var in v:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                raise ValueError(f"Invalid variable name: {var}")
            validated_vars.append(var)
        return validated_vars

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        valid_languages = {"en", "th", "ja", "ko", "zh", "es", "fr", "de", "it", "pt", "ru"}
        if v not in valid_languages:
            raise ValueError(f"Unsupported language: {v}")
        return v


class MessageTemplateCreate(MessageTemplateBase):
    """Schema for creating a new message template."""
    is_system_template: bool = Field(False, description="Whether this is a system template")


class MessageTemplateUpdate(BaseModel):
    """Schema for updating a message template."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    subject_template: Optional[str] = Field(None, max_length=255)
    content_template: Optional[str] = Field(None, min_length=1, max_length=10000)
    category: Optional[str] = Field(None, max_length=100)
    required_variables: Optional[List[str]] = Field(None)
    optional_variables: Optional[List[str]] = Field(None)
    default_values: Optional[Dict[str, Any]] = Field(None)
    tags: Optional[List[str]] = Field(None)
    is_active: Optional[bool] = Field(None)


class MessageTemplateResponse(MessageTemplateBase):
    """Schema for message template response."""
    id: int
    is_active: bool = True
    is_system_template: bool = False
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    @computed_field
    @property
    def all_variables(self) -> List[str]:
        """Get all template variables (required + optional)."""
        return list(set(self.required_variables + self.optional_variables))


class FollowUpScheduleBase(BaseModel):
    """Base follow-up schedule schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    campaign_id: int = Field(..., gt=0, description="Campaign ID")
    kol_id: int = Field(..., gt=0, description="KOL ID")
    trigger_event: str = Field(..., min_length=1, max_length=100, description="Trigger event")
    trigger_message_id: Optional[int] = Field(None, gt=0, description="Trigger message ID")
    delay_days: int = Field(1, ge=0, le=365, description="Delay in days")
    delay_hours: int = Field(0, ge=0, le=23, description="Additional delay in hours")
    message_template_id: int = Field(..., gt=0, description="Message template ID")
    custom_message: Optional[str] = Field(None, max_length=2000, description="Custom message override")
    preferred_channel: CommunicationChannel = Field(..., description="Preferred communication channel")
    fallback_channels: List[str] = Field(default_factory=list, description="Fallback channels")
    stop_on_response: bool = Field(True, description="Stop if response received")
    max_attempts: int = Field(1, ge=1, le=5, description="Maximum attempts")

    @field_validator("trigger_event")
    @classmethod
    def validate_trigger_event(cls, v: str) -> str:
        """Validate trigger event."""
        valid_events = {
            "brief_sent", "no_response_1_day", "no_response_3_days", "no_response_7_days",
            "content_deadline_approaching", "content_overdue", "payment_reminder",
            "performance_review", "campaign_completed", "custom"
        }

        if v not in valid_events:
            raise ValueError(f"Invalid trigger event: {v}")

        return v

    @field_validator("fallback_channels")
    @classmethod
    def validate_fallback_channels(cls, v: List[str]) -> List[str]:
        """Validate fallback channels."""
        valid_channels = {ch.value for ch in CommunicationChannel}

        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f"Invalid fallback channel: {channel}")

        return v

    @computed_field
    @property
    def total_delay_hours(self) -> int:
        """Calculate total delay in hours."""
        return (self.delay_days * 24) + self.delay_hours


class FollowUpScheduleCreate(FollowUpScheduleBase):
    """Schema for creating a new follow-up schedule."""
    pass


class FollowUpScheduleUpdate(BaseModel):
    """Schema for updating a follow-up schedule."""
    model_config = ConfigDict(from_attributes=True)

    delay_days: Optional[int] = Field(None, ge=0, le=365)
    delay_hours: Optional[int] = Field(None, ge=0, le=23)
    custom_message: Optional[str] = Field(None, max_length=2000)
    preferred_channel: Optional[CommunicationChannel] = Field(None)
    fallback_channels: Optional[List[str]] = Field(None)
    stop_on_response: Optional[bool] = Field(None)
    max_attempts: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[ScheduleStatus] = Field(None)


class FollowUpScheduleResponse(FollowUpScheduleBase):
    """Schema for follow-up schedule response."""
    id: int
    scheduled_for: datetime
    executed_at: Optional[datetime] = None
    status: ScheduleStatus
    executed_message_id: Optional[int] = None
    execution_notes: Optional[str] = None
    attempt_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    @computed_field
    @property
    def is_due(self) -> bool:
        """Check if follow-up is due for execution."""
        return (
            self.status == ScheduleStatus.SCHEDULED and
            self.scheduled_for <= datetime.utcnow()
        )

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if follow-up is overdue."""
        return (
            self.status == ScheduleStatus.SCHEDULED and
            self.scheduled_for < datetime.utcnow() - timedelta(hours=1)
        )

    @computed_field
    @property
    def can_execute(self) -> bool:
        """Check if follow-up can be executed."""
        return (
            self.status in [ScheduleStatus.PENDING, ScheduleStatus.SCHEDULED] and
            self.attempt_count < self.max_attempts
        )


class CommunicationStatsResponse(BaseModel):
    """Schema for communication statistics."""
    total_messages: int = 0
    messages_by_status: Dict[str, int] = Field(default_factory=dict)
    messages_by_channel: Dict[str, int] = Field(default_factory=dict)
    response_rate: float = 0.0
    average_response_time: Optional[timedelta] = None
    pending_follow_ups: int = 0
    overdue_follow_ups: int = 0
    template_usage: Dict[str, int] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            timedelta: lambda v: v.total_seconds() if v else None
        }


class MessageSearchCriteria(BaseModel):
    """Schema for message search criteria."""
    kol_ids: Optional[List[int]] = Field(None, description="Filter by KOL IDs")
    campaign_ids: Optional[List[int]] = Field(None, description="Filter by campaign IDs")
    channels: Optional[List[CommunicationChannel]] = Field(None, description="Filter by channels")
    statuses: Optional[List[MessageStatus]] = Field(None, description="Filter by statuses")
    sent_after: Optional[datetime] = Field(None, description="Messages sent after date")
    sent_before: Optional[datetime] = Field(None, description="Messages sent before date")
    has_response: Optional[bool] = Field(None, description="Filter by response status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    priority_min: Optional[int] = Field(None, ge=1, le=10, description="Minimum priority")
    priority_max: Optional[int] = Field(None, ge=1, le=10, description="Maximum priority")

    # Sorting and pagination
    sort_by: str = Field("created_at", description="Sort field")
    sort_desc: bool = Field(True, description="Sort in descending order")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

    @computed_field
    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.per_page

    @computed_field
    @property
    def limit(self) -> int:
        """Get limit for pagination."""
        return self.per_page


class MessageSearchResult(BaseModel):
    """Schema for message search results."""
    messages: List[MessageResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    search_criteria: MessageSearchCriteria

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_count + self.per_page - 1) // self.per_page