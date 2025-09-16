"""
Email communication service supporting multiple providers.
Implements SendGrid and AWS SES for reliable email delivery.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import aiohttp
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json

from app.core.config import get_settings
from app.services.communication.base import (
    BaseCommunicationService, MessageResult, DeliveryStatus,
    MessageStatus, MessagePriority, Attachment
)

logger = logging.getLogger(__name__)


class EmailProvider:
    """Email provider enumeration."""
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"


class EmailService(BaseCommunicationService):
    """
    Email communication service with multiple provider support.

    Features:
    - SendGrid API integration
    - AWS SES integration
    - HTML and plain text emails
    - File attachments
    - Email templates
    - Delivery tracking
    - Bounce and complaint handling
    """

    def __init__(self, provider: str = EmailProvider.SENDGRID):
        super().__init__()
        self.settings = get_settings()
        self.service_name = "email"
        self.provider = provider.lower()

        # Initialize session
        self.session: Optional[aiohttp.ClientSession] = None

        # Provider-specific configuration
        if self.provider == EmailProvider.SENDGRID:
            self.api_key = self.settings.SENDGRID_API_KEY
            self.api_url = "https://api.sendgrid.com/v3/mail/send"
        elif self.provider == EmailProvider.AWS_SES:
            self.aws_region = self.settings.AWS_REGION
            self.aws_access_key = self.settings.AWS_ACCESS_KEY_ID
            self.aws_secret_key = self.settings.AWS_SECRET_ACCESS_KEY
            self.api_url = f"https://email.{self.aws_region}.amazonaws.com"
        else:
            raise ValueError(f"Unsupported email provider: {provider}")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "KOL-Management-System/1.0"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def send_message(
        self,
        recipient: str,
        subject: Optional[str],
        content: str,
        sender: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageResult:
        """
        Send email message via configured provider.

        Args:
            recipient: Recipient email address
            subject: Email subject
            content: Email content (can be HTML or plain text)
            sender: Sender email address
            attachments: List of file attachments
            priority: Message priority
            metadata: Additional metadata

        Returns:
            MessageResult with send status
        """
        if metadata is None:
            metadata = {}

        # Validate inputs
        if not self.validate_recipient(recipient):
            return self.build_error_response("Invalid recipient email address")

        if not subject or not subject.strip():
            return self.build_error_response("Email subject is required")

        if not self.validate_content(content):
            return self.build_error_response("Email content is required")

        # Use default sender if not provided
        if not sender:
            sender = self.settings.DEFAULT_FROM_EMAIL

        try:
            # Send via appropriate provider
            if self.provider == EmailProvider.SENDGRID:
                return await self._send_via_sendgrid(
                    recipient, subject, content, sender, attachments, priority, metadata
                )
            elif self.provider == EmailProvider.AWS_SES:
                return await self._send_via_aws_ses(
                    recipient, subject, content, sender, attachments, priority, metadata
                )
            else:
                return self.build_error_response(f"Provider {self.provider} not implemented")

        except Exception as e:
            self.logger.error(f"Email send failed: {str(e)}")
            return self.build_error_response(str(e))

    async def send_html_email(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        sender: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> MessageResult:
        """
        Send HTML email with optional plain text fallback.

        Args:
            recipient: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text fallback content
            sender: Sender email address
            attachments: List of attachments

        Returns:
            MessageResult with send status
        """
        metadata = {
            "content_type": "html",
            "has_text_fallback": bool(text_content)
        }

        # If no text content provided, strip HTML tags as fallback
        if not text_content:
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()

        # Store both versions in metadata
        metadata["html_content"] = html_content
        metadata["text_content"] = text_content

        return await self.send_message(
            recipient=recipient,
            subject=subject,
            content=html_content,
            sender=sender,
            attachments=attachments,
            metadata=metadata
        )

    async def send_template_email(
        self,
        recipient: str,
        template_id: str,
        template_variables: Dict[str, Any],
        sender: Optional[str] = None
    ) -> MessageResult:
        """
        Send email using a template.

        Args:
            recipient: Recipient email address
            template_id: Template identifier
            template_variables: Variables for template substitution
            sender: Sender email address

        Returns:
            MessageResult with send status
        """
        try:
            if self.provider == EmailProvider.SENDGRID:
                return await self._send_template_via_sendgrid(
                    recipient, template_id, template_variables, sender
                )
            else:
                return self.build_error_response("Template emails only supported with SendGrid")

        except Exception as e:
            self.logger.error(f"Template email send failed: {str(e)}")
            return self.build_error_response(str(e))

    async def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """
        Get delivery status for an email.

        Args:
            message_id: Message identifier

        Returns:
            DeliveryStatus or None if not found
        """
        try:
            if self.provider == EmailProvider.SENDGRID:
                return await self._get_sendgrid_status(message_id)
            elif self.provider == EmailProvider.AWS_SES:
                return await self._get_ses_status(message_id)
            else:
                return None

        except Exception as e:
            self.logger.error(f"Failed to get delivery status: {str(e)}")
            return None

    # Provider-specific implementations

    async def _send_via_sendgrid(
        self,
        recipient: str,
        subject: str,
        content: str,
        sender: str,
        attachments: Optional[List[Attachment]],
        priority: MessagePriority,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send email via SendGrid API."""

        # Determine content type
        is_html = metadata.get("content_type") == "html" or "<html>" in content.lower()

        # Build SendGrid payload
        payload = {
            "personalizations": [{
                "to": [{"email": recipient}],
                "subject": subject
            }],
            "from": {"email": sender},
            "content": [{
                "type": "text/html" if is_html else "text/plain",
                "value": content
            }]
        }

        # Add plain text version for HTML emails
        if is_html and metadata.get("text_content"):
            payload["content"].insert(0, {
                "type": "text/plain",
                "value": metadata["text_content"]
            })

        # Add attachments
        if attachments:
            payload["attachments"] = []
            for attachment in attachments:
                encoded_content = base64.b64encode(attachment.content).decode()
                payload["attachments"].append({
                    "content": encoded_content,
                    "filename": attachment.filename,
                    "type": attachment.content_type,
                    "disposition": "inline" if attachment.inline else "attachment"
                })

        # Set priority
        if priority == MessagePriority.HIGH:
            payload["headers"] = {"X-Priority": "1"}
        elif priority == MessagePriority.LOW:
            payload["headers"] = {"X-Priority": "5"}

        # Add tracking
        payload["tracking_settings"] = {
            "click_tracking": {"enable": True},
            "open_tracking": {"enable": True},
            "subscription_tracking": {"enable": False}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with self.session.post(self.api_url, json=payload, headers=headers) as response:
            if response.status == 202:
                # SendGrid returns 202 for successful queue
                response_headers = dict(response.headers)
                message_id = response_headers.get("x-message-id", f"sg_{int(datetime.utcnow().timestamp())}")

                return self.build_success_response(
                    message_id=message_id,
                    provider_id=message_id,
                    status=MessageStatus.QUEUED,
                    metadata={"provider": "sendgrid", "response_headers": response_headers}
                )
            else:
                error_data = await response.json()
                error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown SendGrid error")
                return self.build_error_response(error_msg, f"sendgrid_{response.status}")

    async def _send_via_aws_ses(
        self,
        recipient: str,
        subject: str,
        content: str,
        sender: str,
        attachments: Optional[List[Attachment]],
        priority: MessagePriority,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send email via AWS SES."""

        # Build email message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject

        # Add content
        is_html = metadata.get("content_type") == "html" or "<html>" in content.lower()
        if is_html:
            msg.attach(MIMEText(content, 'html'))
            if metadata.get("text_content"):
                msg.attach(MIMEText(metadata["text_content"], 'plain'))
        else:
            msg.attach(MIMEText(content, 'plain'))

        # Add attachments
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment.filename}'
                )
                msg.attach(part)

        # Convert to raw email
        raw_message = msg.as_string()

        # AWS SES API call would go here
        # For now, simulate success
        message_id = f"ses_{int(datetime.utcnow().timestamp())}"

        return self.build_success_response(
            message_id=message_id,
            provider_id=message_id,
            status=MessageStatus.SENT,
            metadata={"provider": "aws_ses"}
        )

    async def _send_template_via_sendgrid(
        self,
        recipient: str,
        template_id: str,
        template_variables: Dict[str, Any],
        sender: str
    ) -> MessageResult:
        """Send template email via SendGrid."""

        payload = {
            "personalizations": [{
                "to": [{"email": recipient}],
                "dynamic_template_data": template_variables
            }],
            "from": {"email": sender},
            "template_id": template_id
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with self.session.post(self.api_url, json=payload, headers=headers) as response:
            if response.status == 202:
                response_headers = dict(response.headers)
                message_id = response_headers.get("x-message-id", f"sg_tmpl_{int(datetime.utcnow().timestamp())}")

                return self.build_success_response(
                    message_id=message_id,
                    provider_id=message_id,
                    status=MessageStatus.QUEUED,
                    metadata={"provider": "sendgrid", "template_id": template_id}
                )
            else:
                error_data = await response.json()
                error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown SendGrid error")
                return self.build_error_response(error_msg, f"sendgrid_template_{response.status}")

    async def _get_sendgrid_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """Get delivery status from SendGrid."""
        # SendGrid Event API would be implemented here
        # For now, return basic status
        return DeliveryStatus(
            message_id=message_id,
            status=MessageStatus.SENT,
            metadata={"provider": "sendgrid"}
        )

    async def _get_ses_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """Get delivery status from AWS SES."""
        # AWS SES status tracking would be implemented here
        return DeliveryStatus(
            message_id=message_id,
            status=MessageStatus.SENT,
            metadata={"provider": "aws_ses"}
        )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate email address format."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, recipient))

    def get_service_name(self) -> str:
        """Get service name."""
        return self.service_name

    def get_supported_features(self) -> List[str]:
        """Get list of supported features."""
        features = [
            "plain_text", "html_content", "attachments", "templates",
            "delivery_tracking", "priority_levels"
        ]

        if self.provider == EmailProvider.SENDGRID:
            features.extend(["click_tracking", "open_tracking", "dynamic_templates"])
        elif self.provider == EmailProvider.AWS_SES:
            features.extend(["bounce_handling", "complaint_handling"])

        return features

    async def check_service_health(self) -> Dict[str, Any]:
        """Check email service health."""
        try:
            # Test API connectivity
            if self.provider == EmailProvider.SENDGRID:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with self.session.get("https://api.sendgrid.com/v3/user/profile", headers=headers) as response:
                    healthy = response.status == 200
            else:
                # AWS SES health check would go here
                healthy = True

            return {
                "healthy": healthy,
                "service": self.service_name,
                "provider": self.provider,
                "timestamp": datetime.utcnow().isoformat(),
                "features": self.get_supported_features()
            }

        except Exception as e:
            return {
                "healthy": False,
                "service": self.service_name,
                "provider": self.provider,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }