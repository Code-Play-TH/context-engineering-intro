"""Message service for managing communications with KOLs."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.message import Message, MessageStatus, MessagePriority
from app.models.message_template import MessageTemplate, MessageType
from app.models.campaign import Campaign
from app.models.kol import KOL
from app.models.brief import Brief
from app.models.user import User
from app.schemas.message import (
    MessageCreate, MessageUpdate, MessageStatusUpdate, MessageFilters,
    MessageTemplateCreate, MessageTemplateUpdate, GenerateMessageFromTemplate,
    BulkMessageCreate, SendMessageRequest
)
from app.services.email_service import EmailService


class MessageService:
    """Service for managing messages and message templates."""

    def __init__(self):
        self.email_service = EmailService()

    @staticmethod
    def create_message(db: Session, message_data: MessageCreate, sent_by: int) -> Message:
        """Create a new message."""
        # Validate relationships
        if message_data.kol_id:
            kol = db.query(KOL).filter(KOL.id == message_data.kol_id).first()
            if not kol:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="KOL not found"
                )

        if message_data.campaign_id:
            campaign = db.query(Campaign).filter(Campaign.id == message_data.campaign_id).first()
            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign not found"
                )

        if message_data.brief_id:
            brief = db.query(Brief).filter(Brief.id == message_data.brief_id).first()
            if not brief:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Brief not found"
                )

        if message_data.template_id:
            template = db.query(MessageTemplate).filter(
                MessageTemplate.id == message_data.template_id,
                MessageTemplate.is_active == True
            ).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message template not found or inactive"
                )

        # Validate recipient information
        if message_data.message_type == MessageType.EMAIL and not message_data.recipient_email:
            # Try to get email from KOL
            if message_data.kol_id:
                kol = db.query(KOL).filter(KOL.id == message_data.kol_id).first()
                if kol and kol.email:
                    message_data.recipient_email = kol.email
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Recipient email is required for email messages"
                    )

        # Create message
        message = Message(
            subject=message_data.subject,
            content=message_data.content,
            message_type=message_data.message_type,
            priority=message_data.priority,
            recipient_email=message_data.recipient_email,
            recipient_phone=message_data.recipient_phone,
            recipient_line_id=message_data.recipient_line_id,
            recipient_discord_id=message_data.recipient_discord_id,
            sender_email=message_data.sender_email,
            sender_name=message_data.sender_name,
            kol_id=message_data.kol_id,
            campaign_id=message_data.campaign_id,
            brief_id=message_data.brief_id,
            template_id=message_data.template_id,
            sent_by=sent_by,
            message_data=message_data.message_data,
            scheduled_at=message_data.scheduled_at,
            status=MessageStatus.DRAFT
        )

        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_message(db: Session, message_id: int) -> Optional[Message]:
        """Get message by ID with related data."""
        return db.query(Message).options(
            joinedload(Message.kol),
            joinedload(Message.campaign),
            joinedload(Message.brief),
            joinedload(Message.template),
            joinedload(Message.sender)
        ).filter(Message.id == message_id).first()

    @staticmethod
    def update_message(db: Session, message_id: int, message_data: MessageUpdate, user_id: int) -> Message:
        """Update a message."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Check if message can be edited
        if message.status not in [MessageStatus.DRAFT, MessageStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message with status '{message.status}' cannot be edited"
            )

        # Update fields
        update_data = message_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(message, field, value)

        message.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def update_message_status(
        db: Session, 
        message_id: int, 
        status_data: MessageStatusUpdate
    ) -> Message:
        """Update message status and tracking information."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Update status and tracking fields
        message.status = status_data.status
        message.updated_at = datetime.utcnow()

        if status_data.external_id:
            message.external_id = status_data.external_id
        
        if status_data.external_status:
            message.external_status = status_data.external_status
        
        if status_data.error_message:
            message.error_message = status_data.error_message
        
        if status_data.delivered_at:
            message.delivered_at = status_data.delivered_at
        
        if status_data.read_at:
            message.read_at = status_data.read_at

        # Set sent_at if status is sent and not already set
        if status_data.status == MessageStatus.SENT and not message.sent_at:
            message.sent_at = datetime.utcnow()

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def delete_message(db: Session, message_id: int, user_id: int) -> bool:
        """Delete a message (only if in draft status)."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        if message.status != MessageStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft messages can be deleted"
            )

        db.delete(message)
        db.commit()
        return True

    @staticmethod
    def list_messages(
        db: Session, 
        filters: MessageFilters, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Message], int]:
        """List messages with filtering and pagination."""
        query = db.query(Message).options(
            joinedload(Message.kol),
            joinedload(Message.campaign),
            joinedload(Message.brief),
            joinedload(Message.template),
            joinedload(Message.sender)
        )

        # Apply filters
        if filters.kol_id:
            query = query.filter(Message.kol_id == filters.kol_id)
        
        if filters.campaign_id:
            query = query.filter(Message.campaign_id == filters.campaign_id)
        
        if filters.brief_id:
            query = query.filter(Message.brief_id == filters.brief_id)
        
        if filters.template_id:
            query = query.filter(Message.template_id == filters.template_id)
        
        if filters.message_type:
            query = query.filter(Message.message_type == filters.message_type)
        
        if filters.status:
            query = query.filter(Message.status == filters.status)
        
        if filters.priority:
            query = query.filter(Message.priority == filters.priority)
        
        if filters.sent_by:
            query = query.filter(Message.sent_by == filters.sent_by)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Message.subject.ilike(search_term),
                    Message.content.ilike(search_term)
                )
            )
        
        if filters.date_from:
            query = query.filter(Message.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Message.created_at <= filters.date_to)
        
        if filters.scheduled_from:
            query = query.filter(Message.scheduled_at >= filters.scheduled_from)
        
        if filters.scheduled_to:
            query = query.filter(Message.scheduled_at <= filters.scheduled_to)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        messages = query.order_by(desc(Message.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return messages, total

    def send_message(self, db: Session, message_id: int, force_send: bool = False) -> Message:
        """Send a message immediately."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Check if message can be sent
        if not force_send and message.status not in [MessageStatus.DRAFT, MessageStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message with status '{message.status}' cannot be sent"
            )

        # Update status to queued
        message.status = MessageStatus.QUEUED
        message.updated_at = datetime.utcnow()
        db.commit()

        # Send based on message type
        try:
            if message.message_type == MessageType.EMAIL:
                result = self._send_email_message(message)
            else:
                # For other message types, mark as sent for now
                # TODO: Implement SMS, Line, Discord, etc.
                result = {"success": True, "message": f"{message.message_type} sending not implemented yet"}

            if result["success"]:
                message.status = MessageStatus.SENT
                message.sent_at = datetime.utcnow()
                if "external_id" in result:
                    message.external_id = result["external_id"]
            else:
                message.status = MessageStatus.FAILED
                message.error_message = result.get("error", "Unknown error")
                message.retry_count += 1

        except Exception as e:
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            message.retry_count += 1

        message.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
        return message

    def _send_email_message(self, message: Message) -> Dict[str, Any]:
        """Send an email message using the email service."""
        if not message.recipient_email:
            return {"success": False, "error": "No recipient email"}

        return self.email_service.send_email(
            to_email=message.recipient_email,
            subject=message.subject or "No Subject",
            content=message.content,
            sender_email=message.sender_email,
            sender_name=message.sender_name,
            is_html=True
        )

    @staticmethod
    def generate_message_from_template(
        db: Session, 
        generation_data: GenerateMessageFromTemplate, 
        sent_by: int
    ) -> Message:
        """Generate a message from a template."""
        # Get template
        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == generation_data.template_id,
            MessageTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or inactive"
            )

        # Get related data for context
        kol = None
        campaign = None
        brief = None
        
        if generation_data.kol_id:
            kol = db.query(KOL).filter(KOL.id == generation_data.kol_id).first()
        
        if generation_data.campaign_id:
            campaign = db.query(Campaign).filter(Campaign.id == generation_data.campaign_id).first()
        
        if generation_data.brief_id:
            brief = db.query(Brief).filter(Brief.id == generation_data.brief_id).first()

        # Prepare variables
        variables = {**template.variables, **generation_data.variable_values}
        
        # Add default variables
        default_vars = {}
        if kol:
            default_vars.update({
                "kol_name": kol.name,
                "kol_email": kol.email or "",
                "kol_phone": kol.phone or "",
            })
        
        if campaign:
            default_vars.update({
                "campaign_name": campaign.name,
                "campaign_objectives": campaign.objectives or "",
                "campaign_start_date": campaign.start_date.isoformat() if campaign.start_date else "",
                "campaign_end_date": campaign.end_date.isoformat() if campaign.end_date else "",
            })
        
        if brief:
            default_vars.update({
                "brief_title": brief.title,
                "brief_content": brief.content,
            })

        variables.update(default_vars)

        # Replace placeholders in content and subject
        content = template.content
        subject = template.subject or ""
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))

        # Determine recipient
        recipient_email = generation_data.recipient_email
        if not recipient_email and kol and kol.email:
            recipient_email = kol.email

        # Create message
        message_data = MessageCreate(
            subject=subject,
            content=content,
            message_type=template.message_type,
            recipient_email=recipient_email,
            recipient_phone=generation_data.recipient_phone,
            recipient_line_id=generation_data.recipient_line_id,
            recipient_discord_id=generation_data.recipient_discord_id,
            kol_id=generation_data.kol_id,
            campaign_id=generation_data.campaign_id,
            brief_id=generation_data.brief_id,
            template_id=generation_data.template_id,
            message_data=variables,
            scheduled_at=generation_data.scheduled_at
        )

        return MessageService.create_message(db, message_data, sent_by)

    @staticmethod
    def create_bulk_messages(
        db: Session, 
        bulk_data: BulkMessageCreate, 
        sent_by: int
    ) -> List[Message]:
        """Create messages in bulk."""
        messages = []
        errors = []

        # Handle KOL recipients
        if bulk_data.kol_ids:
            for kol_id in bulk_data.kol_ids:
                try:
                    kol = db.query(KOL).filter(KOL.id == kol_id).first()
                    if not kol:
                        errors.append(f"KOL {kol_id}: Not found")
                        continue

                    # Determine recipient based on message type
                    recipient_email = None
                    recipient_phone = None
                    
                    if bulk_data.message_type == MessageType.EMAIL:
                        recipient_email = kol.email
                        if not recipient_email:
                            errors.append(f"KOL {kol_id}: No email address")
                            continue
                    elif bulk_data.message_type == MessageType.SMS:
                        recipient_phone = kol.phone
                        if not recipient_phone:
                            errors.append(f"KOL {kol_id}: No phone number")
                            continue

                    message_data = MessageCreate(
                        subject=bulk_data.subject,
                        content=bulk_data.content,
                        message_type=bulk_data.message_type,
                        priority=bulk_data.priority,
                        recipient_email=recipient_email,
                        recipient_phone=recipient_phone,
                        sender_email=bulk_data.sender_email,
                        sender_name=bulk_data.sender_name,
                        kol_id=kol_id,
                        campaign_id=bulk_data.campaign_id,
                        brief_id=bulk_data.brief_id,
                        template_id=bulk_data.template_id,
                        message_data=bulk_data.message_data,
                        scheduled_at=bulk_data.scheduled_at
                    )
                    
                    message = MessageService.create_message(db, message_data, sent_by)
                    messages.append(message)
                    
                except Exception as e:
                    errors.append(f"KOL {kol_id}: {str(e)}")

        # Handle custom recipients
        if bulk_data.custom_recipients:
            for recipient in bulk_data.custom_recipients:
                try:
                    message_data = MessageCreate(
                        subject=bulk_data.subject,
                        content=bulk_data.content,
                        message_type=bulk_data.message_type,
                        priority=bulk_data.priority,
                        recipient_email=recipient.get("email"),
                        recipient_phone=recipient.get("phone"),
                        recipient_line_id=recipient.get("line_id"),
                        recipient_discord_id=recipient.get("discord_id"),
                        sender_email=bulk_data.sender_email,
                        sender_name=bulk_data.sender_name,
                        campaign_id=bulk_data.campaign_id,
                        brief_id=bulk_data.brief_id,
                        template_id=bulk_data.template_id,
                        message_data=bulk_data.message_data,
                        scheduled_at=bulk_data.scheduled_at
                    )
                    
                    message = MessageService.create_message(db, message_data, sent_by)
                    messages.append(message)
                    
                except Exception as e:
                    errors.append(f"Recipient {recipient.get('email', 'unknown')}: {str(e)}")

        if errors and not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create any messages: {'; '.join(errors)}"
            )

        return messages

    # Message Template Methods
    @staticmethod
    def create_message_template(
        db: Session, 
        template_data: MessageTemplateCreate, 
        created_by: int
    ) -> MessageTemplate:
        """Create a new message template."""
        template = MessageTemplate(
            **template_data.dict(),
            created_by=created_by
        )

        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_message_template(db: Session, template_id: int) -> Optional[MessageTemplate]:
        """Get message template by ID."""
        return db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()

    @staticmethod
    def update_message_template(
        db: Session, 
        template_id: int, 
        template_data: MessageTemplateUpdate
    ) -> MessageTemplate:
        """Update a message template."""
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message template not found"
            )

        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_message_template(db: Session, template_id: int) -> bool:
        """Delete a message template."""
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message template not found"
            )

        # Check if template is being used
        messages_using_template = db.query(Message).filter(Message.template_id == template_id).count()
        if messages_using_template > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete template that is being used by existing messages"
            )

        db.delete(template)
        db.commit()
        return True

    @staticmethod
    def list_message_templates(
        db: Session, 
        message_type: Optional[MessageType] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[MessageTemplate], int]:
        """List message templates with filtering and pagination."""
        query = db.query(MessageTemplate)

        if message_type:
            query = query.filter(MessageTemplate.message_type == message_type)
        
        if category:
            query = query.filter(MessageTemplate.category == category)
        
        if is_active is not None:
            query = query.filter(MessageTemplate.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        templates = query.order_by(desc(MessageTemplate.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return templates, total

    @staticmethod
    def get_message_stats(db: Session, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Get message statistics."""
        query = db.query(Message)
        
        if campaign_id:
            query = query.filter(Message.campaign_id == campaign_id)

        total_messages = query.count()

        # Count by status
        status_counts = db.query(
            Message.status, func.count(Message.id)
        ).group_by(Message.status)
        
        if campaign_id:
            status_counts = status_counts.filter(Message.campaign_id == campaign_id)
        
        by_status = {status: count for status, count in status_counts.all()}

        # Count by type
        type_counts = db.query(
            Message.message_type, func.count(Message.id)
        ).group_by(Message.message_type)
        
        if campaign_id:
            type_counts = type_counts.filter(Message.campaign_id == campaign_id)
        
        by_type = {msg_type: count for msg_type, count in type_counts.all()}

        # Count by priority
        priority_counts = db.query(
            Message.priority, func.count(Message.id)
        ).group_by(Message.priority)
        
        if campaign_id:
            priority_counts = priority_counts.filter(Message.campaign_id == campaign_id)
        
        by_priority = {priority: count for priority, count in priority_counts.all()}

        # Calculate delivery and open rates
        sent_count = by_status.get(MessageStatus.SENT, 0) + by_status.get(MessageStatus.DELIVERED, 0) + by_status.get(MessageStatus.READ, 0)
        delivered_count = by_status.get(MessageStatus.DELIVERED, 0) + by_status.get(MessageStatus.READ, 0)
        read_count = by_status.get(MessageStatus.READ, 0)

        delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
        open_rate = (read_count / delivered_count * 100) if delivered_count > 0 else 0

        # Recent activity (last 10 messages)
        recent_messages = query.order_by(desc(Message.updated_at)).limit(10).all()
        recent_activity = [
            {
                "id": message.id,
                "subject": message.subject,
                "status": message.status,
                "message_type": message.message_type,
                "updated_at": message.updated_at
            }
            for message in recent_messages
        ]

        return {
            "total_messages": total_messages,
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            "delivery_rate": round(delivery_rate, 2),
            "open_rate": round(open_rate, 2),
            "recent_activity": recent_activity
        }