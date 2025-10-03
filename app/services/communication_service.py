"""
Communication service for managing messages and notifications.

This module handles communication between team members and KOLs,
including messaging, notifications, and activity tracking.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.collaboration import Collaboration
from app.utils.datetime_utils import get_current_utc
import logging

logger = logging.getLogger(__name__)


class MessageType:
    """Message type constants."""
    DIRECT = "direct"
    BROADCAST = "broadcast"
    CAMPAIGN_INVITE = "campaign_invite"
    CONTENT_FEEDBACK = "content_feedback"
    REMINDER = "reminder"
    SYSTEM = "system"


class NotificationChannel:
    """Notification channel constants."""
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    PUSH = "push"


class Message:
    """Message model (simplified - would be a proper DB model)."""

    def __init__(
        self,
        sender_id: int,
        recipient_id: int,
        subject: str,
        body: str,
        message_type: str = MessageType.DIRECT,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = None  # Would be set by DB
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.subject = subject
        self.body = body
        self.message_type = message_type
        self.metadata = metadata or {}
        self.is_read = False
        self.created_at = get_current_utc()
        self.read_at = None


class CommunicationService:
    """
    Service for managing communications.

    Handles:
    - Direct messaging between users and KOLs
    - Broadcast messages
    - Campaign invitations
    - Notifications across channels
    - Message threading and history
    """

    def __init__(self, db: Session):
        """
        Initialize communication service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def send_message(
        self,
        sender_id: int,
        recipient_id: int,
        subject: str,
        body: str,
        message_type: str = MessageType.DIRECT,
        campaign_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message.

        Args:
            sender_id (int): Sender user ID.
            recipient_id (int): Recipient ID (user or KOL).
            subject (str): Message subject.
            body (str): Message body.
            message_type (str): Type of message.
            campaign_id (Optional[int]): Related campaign ID.
            metadata (Optional[Dict[str, Any]]): Additional metadata.

        Returns:
            Dict[str, Any]: Message send result.
        """
        # Create message
        message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            subject=subject,
            body=body,
            message_type=message_type,
            metadata=metadata or {}
        )

        if campaign_id:
            message.metadata["campaign_id"] = campaign_id

        # In a real implementation, this would save to database
        # For now, we'll just log and return success
        logger.info(
            f"Message sent: from user {sender_id} to {recipient_id}, "
            f"type={message_type}, subject='{subject}'"
        )

        return {
            "success": True,
            "message_id": "msg_" + str(get_current_utc().timestamp()),
            "sent_at": get_current_utc().isoformat(),
            "type": message_type
        }

    def send_broadcast_message(
        self,
        sender_id: int,
        recipient_ids: List[int],
        subject: str,
        body: str,
        campaign_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send broadcast message to multiple recipients.

        Args:
            sender_id (int): Sender user ID.
            recipient_ids (List[int]): List of recipient IDs.
            subject (str): Message subject.
            body (str): Message body.
            campaign_id (Optional[int]): Related campaign ID.

        Returns:
            Dict[str, Any]: Broadcast result summary.
        """
        sent_count = 0
        failed_count = 0
        message_ids = []

        for recipient_id in recipient_ids:
            try:
                result = self.send_message(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    subject=subject,
                    body=body,
                    message_type=MessageType.BROADCAST,
                    campaign_id=campaign_id
                )
                if result["success"]:
                    sent_count += 1
                    message_ids.append(result["message_id"])
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to {recipient_id}: {e}")
                failed_count += 1

        return {
            "success": True,
            "total_recipients": len(recipient_ids),
            "sent": sent_count,
            "failed": failed_count,
            "message_ids": message_ids,
            "sent_at": get_current_utc().isoformat()
        }

    def send_campaign_invitation(
        self,
        campaign_id: int,
        kol_id: int,
        sender_id: int,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send campaign invitation to KOL.

        Args:
            campaign_id (int): Campaign ID.
            kol_id (int): KOL ID.
            sender_id (int): User ID sending invitation.
            custom_message (Optional[str]): Custom message to include.

        Returns:
            Dict[str, Any]: Invitation send result.

        Raises:
            ValueError: If campaign or KOL not found.
        """
        # Get campaign
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Get KOL
        kol = self.db.query(KOL).filter(KOL.id == kol_id).first()
        if not kol:
            raise ValueError(f"KOL not found: {kol_id}")

        # Build invitation message
        subject = f"Invitation: {campaign.name} Campaign"
        body = self._build_invitation_body(campaign, kol, custom_message)

        # Send message
        result = self.send_message(
            sender_id=sender_id,
            recipient_id=kol_id,
            subject=subject,
            body=body,
            message_type=MessageType.CAMPAIGN_INVITE,
            campaign_id=campaign_id,
            metadata={
                "campaign_name": campaign.name,
                "kol_name": kol.name
            }
        )

        # Also send email notification
        self.send_notification(
            recipient_id=kol_id,
            title=subject,
            message=body,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            metadata={"campaign_id": campaign_id, "type": "campaign_invitation"}
        )

        return result

    def _build_invitation_body(
        self,
        campaign: Campaign,
        kol: KOL,
        custom_message: Optional[str]
    ) -> str:
        """Build invitation message body."""
        body = f"Hi {kol.name},\n\n"
        body += f"We would like to invite you to participate in our {campaign.name} campaign.\n\n"
        body += f"Campaign Details:\n"
        body += f"- Description: {campaign.description}\n"
        body += f"- Duration: {campaign.start_date.strftime('%Y-%m-%d')} to {campaign.end_date.strftime('%Y-%m-%d')}\n"
        body += f"- Budget: {campaign.currency} {campaign.budget:,.2f}\n\n"

        if custom_message:
            body += f"{custom_message}\n\n"

        body += "Please review the campaign brief and let us know if you're interested.\n\n"
        body += "Best regards,\nThe Campaign Team"

        return body

    def send_notification(
        self,
        recipient_id: int,
        title: str,
        message: str,
        channels: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notification through specified channels.

        Args:
            recipient_id (int): Recipient ID.
            title (str): Notification title.
            message (str): Notification message.
            channels (List[str]): List of channels to use.
            metadata (Optional[Dict[str, Any]]): Additional metadata.

        Returns:
            Dict[str, Any]: Notification send result.
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP]

        results = {}

        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    # Would integrate with email service (SendGrid, AWS SES, etc.)
                    logger.info(f"Sending email notification to recipient {recipient_id}")
                    results[channel] = {"success": True, "sent_at": get_current_utc().isoformat()}

                elif channel == NotificationChannel.IN_APP:
                    # Would save to in-app notification table
                    logger.info(f"Creating in-app notification for recipient {recipient_id}")
                    results[channel] = {"success": True, "created_at": get_current_utc().isoformat()}

                elif channel == NotificationChannel.SMS:
                    # Would integrate with SMS service (Twilio, etc.)
                    logger.info(f"Sending SMS notification to recipient {recipient_id}")
                    results[channel] = {"success": True, "sent_at": get_current_utc().isoformat()}

                elif channel == NotificationChannel.PUSH:
                    # Would integrate with push notification service (FCM, etc.)
                    logger.info(f"Sending push notification to recipient {recipient_id}")
                    results[channel] = {"success": True, "sent_at": get_current_utc().isoformat()}

            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
                results[channel] = {"success": False, "error": str(e)}

        return {
            "recipient_id": recipient_id,
            "title": title,
            "channels_sent": channels,
            "results": results,
            "sent_at": get_current_utc().isoformat()
        }

    def send_content_feedback(
        self,
        content_id: int,
        sender_id: int,
        kol_id: int,
        feedback: str,
        is_approved: bool
    ) -> Dict[str, Any]:
        """
        Send content feedback to KOL.

        Args:
            content_id (int): Content ID.
            sender_id (int): User ID sending feedback.
            kol_id (int): KOL ID.
            feedback (str): Feedback message.
            is_approved (bool): Whether content is approved.

        Returns:
            Dict[str, Any]: Feedback send result.
        """
        subject = "Content Approved" if is_approved else "Content Revision Requested"
        body = f"Hi,\n\n"

        if is_approved:
            body += f"Your content has been approved! Great work.\n\n"
        else:
            body += f"We've reviewed your content and have some feedback:\n\n"

        body += f"{feedback}\n\n"
        body += "Thank you for your collaboration."

        result = self.send_message(
            sender_id=sender_id,
            recipient_id=kol_id,
            subject=subject,
            body=body,
            message_type=MessageType.CONTENT_FEEDBACK,
            metadata={"content_id": content_id, "is_approved": is_approved}
        )

        # Send notification
        self.send_notification(
            recipient_id=kol_id,
            title=subject,
            message=body,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            metadata={"content_id": content_id, "feedback_type": "approval" if is_approved else "revision"}
        )

        return result

    def send_reminder(
        self,
        recipient_id: int,
        reminder_type: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send reminder notification.

        Args:
            recipient_id (int): Recipient ID.
            reminder_type (str): Type of reminder.
            details (Dict[str, Any]): Reminder details.

        Returns:
            Dict[str, Any]: Reminder send result.
        """
        # Build reminder message based on type
        if reminder_type == "deadline_approaching":
            subject = "Reminder: Deadline Approaching"
            body = f"This is a reminder that your deadline is approaching:\n\n"
            body += f"Task: {details.get('task_name')}\n"
            body += f"Due: {details.get('due_date')}\n\n"
            body += "Please ensure you complete this on time."

        elif reminder_type == "content_pending_approval":
            subject = "Reminder: Content Pending Your Approval"
            body = f"You have content waiting for your approval:\n\n"
            body += f"Content ID: {details.get('content_id')}\n"
            body += f"Submitted: {details.get('submitted_at')}\n\n"
            body += "Please review and provide feedback."

        elif reminder_type == "payment_due":
            subject = "Reminder: Payment Due"
            body = f"Payment is now due:\n\n"
            body += f"Amount: {details.get('currency')} {details.get('amount')}\n"
            body += f"Due Date: {details.get('due_date')}\n\n"
            body += "Please process payment at your earliest convenience."

        else:
            subject = "Reminder"
            body = details.get("message", "You have a pending task.")

        result = self.send_message(
            sender_id=1,  # System sender
            recipient_id=recipient_id,
            subject=subject,
            body=body,
            message_type=MessageType.REMINDER,
            metadata={"reminder_type": reminder_type, **details}
        )

        # Send notification
        self.send_notification(
            recipient_id=recipient_id,
            title=subject,
            message=body,
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            metadata={"reminder_type": reminder_type}
        )

        return result

    def get_message_thread(
        self,
        user_id: int,
        other_user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get message thread between two users.

        Args:
            user_id (int): First user ID.
            other_user_id (int): Second user ID.
            limit (int): Maximum messages to return.

        Returns:
            List[Dict[str, Any]]: List of messages in thread.
        """
        # In real implementation, would query message table
        # For now, return empty list
        logger.info(f"Getting message thread between {user_id} and {other_user_id}")
        return []

    def mark_as_read(self, message_id: str, user_id: int) -> bool:
        """
        Mark message as read.

        Args:
            message_id (str): Message ID.
            user_id (int): User ID marking as read.

        Returns:
            bool: True if marked successfully.
        """
        # In real implementation, would update message status
        logger.info(f"Message {message_id} marked as read by user {user_id}")
        return True


def get_communication_service(db: Session) -> CommunicationService:
    """
    Dependency for FastAPI to inject CommunicationService.

    Args:
        db (Session): Database session.

    Returns:
        CommunicationService: Service instance.
    """
    return CommunicationService(db)
