"""Message API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.message_template import MessageType
from app.services.message_service import MessageService
from app.services.email_service import EmailService
from app.schemas.message import (
    MessageCreate, MessageUpdate, MessageStatusUpdate, MessageResponse, MessageWithRelations,
    MessageListResponse, MessageFilters, MessageStats, GenerateMessageFromTemplate,
    BulkMessageCreate, SendMessageRequest, MessageTemplateCreate, MessageTemplateUpdate, 
    MessageTemplateResponse, MessageTemplateListResponse, EmailTestRequest, EmailSendRequest,
    BulkEmailRequest, EmailResponse, BulkEmailResponse
)

router = APIRouter(prefix="/messages", tags=["messages"])
message_service = MessageService()
email_service = EmailService()


# Message Endpoints
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new message."""
    message = MessageService.create_message(db, message_data, current_user.id)
    return message


@router.get("/", response_model=MessageListResponse)
def list_messages(
    kol_id: Optional[int] = Query(None),
    campaign_id: Optional[int] = Query(None),
    brief_id: Optional[int] = Query(None),
    template_id: Optional[int] = Query(None),
    message_type: Optional[MessageType] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    sent_by: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    scheduled_from: Optional[str] = Query(None),
    scheduled_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List messages with filtering and pagination."""
    filters = MessageFilters(
        kol_id=kol_id,
        campaign_id=campaign_id,
        brief_id=brief_id,
        template_id=template_id,
        message_type=message_type,
        status=status,
        priority=priority,
        sent_by=sent_by,
        search=search,
        date_from=date_from,
        date_to=date_to,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to
    )
    
    messages, total = MessageService.list_messages(db, filters, page, page_size)
    
    # Convert to response format with related data
    message_responses = []
    for message in messages:
        message_dict = {
            **message.__dict__,
            "kol_name": message.kol.name if message.kol else None,
            "campaign_name": message.campaign.name if message.campaign else None,
            "brief_title": message.brief.title if message.brief else None,
            "template_name": message.template.name if message.template else None,
            "sender_name": message.sender.full_name if message.sender else None,
        }
        message_responses.append(MessageWithRelations(**message_dict))
    
    total_pages = (total + page_size - 1) // page_size
    
    return MessageListResponse(
        messages=message_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{message_id}", response_model=MessageWithRelations)
def get_message(
    message_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific message by ID."""
    message = MessageService.get_message(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Convert to response format with related data
    message_dict = {
        **message.__dict__,
        "kol_name": message.kol.name if message.kol else None,
        "campaign_name": message.campaign.name if message.campaign else None,
        "brief_title": message.brief.title if message.brief else None,
        "template_name": message.template.name if message.template else None,
        "sender_name": message.sender.full_name if message.sender else None,
    }
    
    return MessageWithRelations(**message_dict)


@router.put("/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: int,
    message_data: MessageUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a message."""
    message = MessageService.update_message(db, message_id, message_data, current_user.id)
    return message


@router.patch("/{message_id}/status", response_model=MessageResponse)
def update_message_status(
    message_id: int,
    status_data: MessageStatusUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update message status."""
    message = MessageService.update_message_status(db, message_id, status_data)
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a message (only if in draft status)."""
    MessageService.delete_message(db, message_id, current_user.id)


@router.post("/{message_id}/send", response_model=MessageResponse)
def send_message(
    message_id: int,
    send_request: SendMessageRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Send a message immediately."""
    message = message_service.send_message(db, message_id, send_request.force_send)
    return message


@router.post("/generate-from-template", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def generate_message_from_template(
    generation_data: GenerateMessageFromTemplate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Generate a message from a template."""
    message = MessageService.generate_message_from_template(db, generation_data, current_user.id)
    return message


@router.post("/bulk", response_model=List[MessageResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_messages(
    bulk_data: BulkMessageCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create messages in bulk."""
    messages = MessageService.create_bulk_messages(db, bulk_data, current_user.id)
    return messages


@router.get("/stats/overview", response_model=MessageStats)
def get_message_stats(
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get message statistics."""
    stats = MessageService.get_message_stats(db, campaign_id)
    return MessageStats(**stats)


# Message Template Endpoints
@router.post("/templates", response_model=MessageTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_message_template(
    template_data: MessageTemplateCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new message template."""
    template = MessageService.create_message_template(db, template_data, current_user.id)
    return template


@router.get("/templates", response_model=MessageTemplateListResponse)
def list_message_templates(
    message_type: Optional[MessageType] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List message templates with filtering and pagination."""
    templates, total = MessageService.list_message_templates(
        db, message_type, category, is_active, page, page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return MessageTemplateListResponse(
        templates=templates,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/templates/{template_id}", response_model=MessageTemplateResponse)
def get_message_template(
    template_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific message template by ID."""
    template = MessageService.get_message_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message template not found"
        )
    return template


@router.put("/templates/{template_id}", response_model=MessageTemplateResponse)
def update_message_template(
    template_id: int,
    template_data: MessageTemplateUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a message template."""
    template = MessageService.update_message_template(db, template_id, template_data)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_template(
    template_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a message template."""
    MessageService.delete_message_template(db, template_id)


# Email Service Endpoints
@router.post("/email/test", response_model=EmailResponse)
def test_email_configuration(
    test_request: EmailTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Test email configuration by sending a test email."""
    result = email_service.send_email(
        to_email=test_request.test_email,
        subject="KOL Management System - Email Test",
        content="<h2>Email Configuration Test</h2><p>If you receive this email, your email configuration is working correctly!</p>",
        is_html=True
    )
    return EmailResponse(**result)


@router.post("/email/send", response_model=EmailResponse)
def send_single_email(
    email_request: EmailSendRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a single email directly."""
    result = email_service.send_email(
        to_email=email_request.to_email,
        subject=email_request.subject,
        content=email_request.content,
        sender_email=email_request.sender_email,
        sender_name=email_request.sender_name,
        is_html=email_request.is_html,
        attachments=email_request.attachments
    )
    return EmailResponse(**result)


@router.post("/email/bulk", response_model=BulkEmailResponse)
def send_bulk_emails(
    bulk_request: BulkEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send bulk emails directly."""
    result = email_service.send_bulk_emails(
        recipients=bulk_request.recipients,
        subject=bulk_request.subject,
        content=bulk_request.content,
        sender_email=bulk_request.sender_email,
        sender_name=bulk_request.sender_name,
        is_html=bulk_request.is_html
    )
    return BulkEmailResponse(**result)


@router.get("/email/test-connection", response_model=EmailResponse)
def test_email_connection(
    current_user: User = Depends(get_current_user)
):
    """Test SMTP connection without sending an email."""
    result = email_service.test_connection()
    return EmailResponse(**result)
