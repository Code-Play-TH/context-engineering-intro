"""Message schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr
from app.models.message import MessageStatus, MessagePriority
from app.models.message_template import MessageType


# Message Template Schemas
class MessageTemplateBase(BaseModel):
    """Base message template schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    message_type: MessageType
    category: Optional[str] = Field(None, max_length=100)
    variables: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_default: bool = False


class MessageTemplateCreate(MessageTemplateBase):
    """Schema for creating a message template."""
    pass


class MessageTemplateUpdate(BaseModel):
    """Schema for updating a message template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    message_type: Optional[MessageType] = None
    category: Optional[str] = Field(None, max_length=100)
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class MessageTemplateResponse(MessageTemplateBase):
    """Schema for message template responses."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    """Base message schema."""
    subject: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = Field(None, max_length=50)
    recipient_line_id: Optional[str] = Field(None, max_length=255)
    recipient_discord_id: Optional[str] = Field(None, max_length=255)
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = Field(None, max_length=255)
    message_data: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    kol_id: Optional[int] = None
    campaign_id: Optional[int] = None
    brief_id: Optional[int] = None
    template_id: Optional[int] = None


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    subject: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[MessagePriority] = None
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = Field(None, max_length=50)
    recipient_line_id: Optional[str] = Field(None, max_length=255)
    recipient_discord_id: Optional[str] = Field(None, max_length=255)
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = Field(None, max_length=255)
    message_data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class MessageStatusUpdate(BaseModel):
    """Schema for updating message status."""
    status: MessageStatus
    external_id: Optional[str] = Field(None, max_length=255)
    external_status: Optional[str] = Field(None, max_length=100)
    error_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


class MessageResponse(MessageBase):
    """Schema for message responses."""
    id: int
    status: MessageStatus
    kol_id: Optional[int] = None
    campaign_id: Optional[int] = None
    brief_id: Optional[int] = None
    template_id: Optional[int] = None
    sent_by: int
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_status: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MessageWithRelations(MessageResponse):
    """Message response with related data."""
    kol_name: Optional[str] = None
    campaign_name: Optional[str] = None
    brief_title: Optional[str] = None
    template_name: Optional[str] = None
    sender_name: Optional[str] = None


# Message Generation Schemas
class GenerateMessageFromTemplate(BaseModel):
    """Schema for generating message from template."""
    template_id: int
    kol_id: Optional[int] = None
    campaign_id: Optional[int] = None
    brief_id: Optional[int] = None
    variable_values: Dict[str, Any] = Field(default_factory=dict)
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None
    recipient_line_id: Optional[str] = None
    recipient_discord_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class BulkMessageCreate(BaseModel):
    """Schema for creating messages in bulk."""
    kol_ids: Optional[List[int]] = None
    campaign_id: Optional[int] = None
    brief_id: Optional[int] = None
    template_id: Optional[int] = None
    subject: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    message_data: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    # For custom recipients (not KOLs)
    custom_recipients: Optional[List[Dict[str, Any]]] = None


class SendMessageRequest(BaseModel):
    """Schema for sending a message immediately."""
    message_id: int
    force_send: bool = False  # Send even if already sent


# Filter and List Schemas
class MessageFilters(BaseModel):
    """Schema for message filtering."""
    kol_id: Optional[int] = None
    campaign_id: Optional[int] = None
    brief_id: Optional[int] = None
    template_id: Optional[int] = None
    message_type: Optional[MessageType] = None
    status: Optional[MessageStatus] = None
    priority: Optional[MessagePriority] = None
    sent_by: Optional[int] = None
    search: Optional[str] = None  # Search in subject and content
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    scheduled_from: Optional[datetime] = None
    scheduled_to: Optional[datetime] = None


class MessageListResponse(BaseModel):
    """Schema for paginated message list response."""
    messages: List[MessageWithRelations]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageTemplateListResponse(BaseModel):
    """Schema for paginated message template list response."""
    templates: List[MessageTemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Statistics Schemas
class MessageStats(BaseModel):
    """Message statistics schema."""
    total_messages: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    delivery_rate: float
    open_rate: float


# Email Service Schemas
class EmailTestRequest(BaseModel):
    """Schema for testing email configuration."""
    test_email: EmailStr


class EmailSendRequest(BaseModel):
    """Schema for sending a single email."""
    to_email: EmailStr
    subject: str
    content: str
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    is_html: bool = True
    attachments: Optional[List[Dict[str, Any]]] = None


class BulkEmailRequest(BaseModel):
    """Schema for sending bulk emails."""
    recipients: List[Dict[str, Any]]  # List with 'email' and optional 'variables'
    subject: str
    content: str
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None
    is_html: bool = True


class EmailResponse(BaseModel):
    """Schema for email service responses."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    details: Optional[str] = None
    recipients: Optional[List[str]] = None


class BulkEmailResponse(BaseModel):
    """Schema for bulk email responses."""
    total: int
    success: int
    failed: int
    errors: List[Dict[str, str]]