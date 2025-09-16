"""
Line Messaging API service for communicating with KOLs via Line.
Popular messaging platform in Asia for influencer communications.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import aiohttp
import json
import hashlib
import hmac
import base64

from app.core.config import get_settings
from app.services.communication.base import (
    BaseCommunicationService, MessageResult, DeliveryStatus,
    MessageStatus, MessagePriority, Attachment
)

logger = logging.getLogger(__name__)


class LineMessageType:
    """Line message type constants."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    LOCATION = "location"
    STICKER = "sticker"
    TEMPLATE = "template"
    FLEX = "flex"


class LineService(BaseCommunicationService):
    """
    Line Messaging API service for KOL communications.

    Features:
    - Text messages
    - Rich messages (images, videos, audio)
    - Template messages
    - Flex messages
    - Quick replies
    - Push notifications
    - Delivery tracking
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.service_name = "line"
        self.api_base_url = "https://api.line.me/v2/bot"
        self.channel_access_token = self.settings.LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = self.settings.LINE_CHANNEL_SECRET

        # Rate limiting (1000 requests per minute)
        self.rate_limit_per_minute = 1000

        # Initialize session
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "Authorization": f"Bearer {self.channel_access_token}",
                "Content-Type": "application/json",
                "User-Agent": "KOL-Management-System/1.0"
            }
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
        Send Line message to user.

        Args:
            recipient: Line user ID
            subject: Message title (used in templates)
            content: Message content
            sender: Sender identifier (not used in Line)
            attachments: List of media attachments
            priority: Message priority
            metadata: Additional metadata (message type, templates, etc.)

        Returns:
            MessageResult with send status
        """
        if metadata is None:
            metadata = {}

        # Validate inputs
        if not self.validate_recipient(recipient):
            return self.build_error_response("Invalid Line user ID")

        if not self.validate_content(content, max_length=5000):
            return self.build_error_response("Content is required and must be under 5000 characters")

        try:
            # Determine message type
            message_type = metadata.get("message_type", LineMessageType.TEXT)

            if message_type == LineMessageType.TEXT:
                return await self._send_text_message(recipient, content, metadata)
            elif message_type == LineMessageType.FLEX:
                return await self._send_flex_message(recipient, subject, content, metadata)
            elif message_type == LineMessageType.TEMPLATE:
                return await self._send_template_message(recipient, subject, content, metadata)
            elif attachments:
                return await self._send_media_message(recipient, content, attachments, metadata)
            else:
                return await self._send_text_message(recipient, content, metadata)

        except Exception as e:
            self.logger.error(f"Line message send failed: {str(e)}")
            return self.build_error_response(str(e))

    async def send_rich_message(
        self,
        recipient: str,
        title: str,
        description: str,
        image_url: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> MessageResult:
        """
        Send Line rich message with title, description, and actions.

        Args:
            recipient: Line user ID
            title: Message title
            description: Message description
            image_url: Optional header image URL
            actions: List of action buttons

        Returns:
            MessageResult with send status
        """
        # Build template message
        template = {
            "type": "buttons",
            "title": title,
            "text": description
        }

        if image_url:
            template["thumbnailImageUrl"] = image_url

        if actions:
            template["actions"] = actions[:4]  # Line allows max 4 actions

        metadata = {
            "message_type": LineMessageType.TEMPLATE,
            "template": template
        }

        return await self.send_message(
            recipient=recipient,
            subject=title,
            content=description,
            metadata=metadata
        )

    async def send_carousel_message(
        self,
        recipient: str,
        columns: List[Dict[str, Any]]
    ) -> MessageResult:
        """
        Send Line carousel message with multiple cards.

        Args:
            recipient: Line user ID
            columns: List of carousel columns

        Returns:
            MessageResult with send status
        """
        template = {
            "type": "carousel",
            "columns": columns[:10]  # Line allows max 10 columns
        }

        metadata = {
            "message_type": LineMessageType.TEMPLATE,
            "template": template
        }

        return await self.send_message(
            recipient=recipient,
            subject=None,
            content="Carousel Message",
            metadata=metadata
        )

    async def send_flex_message(
        self,
        recipient: str,
        alt_text: str,
        flex_content: Dict[str, Any]
    ) -> MessageResult:
        """
        Send Line Flex message with custom layout.

        Args:
            recipient: Line user ID
            alt_text: Alternative text for non-Flex capable devices
            flex_content: Flex message content structure

        Returns:
            MessageResult with send status
        """
        metadata = {
            "message_type": LineMessageType.FLEX,
            "flex_content": flex_content,
            "alt_text": alt_text
        }

        return await self.send_message(
            recipient=recipient,
            subject=None,
            content=alt_text,
            metadata=metadata
        )

    async def send_image_message(
        self,
        recipient: str,
        image_url: str,
        preview_url: Optional[str] = None
    ) -> MessageResult:
        """
        Send Line image message.

        Args:
            recipient: Line user ID
            image_url: Image URL
            preview_url: Preview image URL

        Returns:
            MessageResult with send status
        """
        metadata = {
            "message_type": LineMessageType.IMAGE,
            "image_url": image_url,
            "preview_url": preview_url or image_url
        }

        return await self.send_message(
            recipient=recipient,
            subject=None,
            content="Image message",
            metadata=metadata
        )

    async def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """
        Get delivery status for a Line message.

        Args:
            message_id: Line message ID

        Returns:
            DeliveryStatus or None if not found
        """
        try:
            # Line doesn't provide detailed delivery status in real-time
            # Return basic delivered status
            return DeliveryStatus(
                message_id=message_id,
                status=MessageStatus.SENT,
                metadata={"provider": "line"}
            )

        except Exception as e:
            self.logger.error(f"Failed to get Line message status: {str(e)}")
            return None

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Line user profile information.

        Args:
            user_id: Line user ID

        Returns:
            User profile dictionary or None if not found
        """
        try:
            url = f"{self.api_base_url}/profile/{user_id}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

        except Exception as e:
            self.logger.error(f"Failed to get Line user profile: {str(e)}")
            return None

    # Private helper methods

    async def _send_text_message(
        self,
        recipient: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send simple text message via Line."""

        message = {
            "type": "text",
            "text": content
        }

        # Add quick reply if specified
        if metadata.get("quick_reply"):
            message["quickReply"] = metadata["quick_reply"]

        return await self._send_line_message(recipient, [message])

    async def _send_flex_message(
        self,
        recipient: str,
        subject: Optional[str],
        content: str,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send Flex message via Line."""

        message = {
            "type": "flex",
            "altText": metadata.get("alt_text", content),
            "contents": metadata.get("flex_content", {})
        }

        return await self._send_line_message(recipient, [message])

    async def _send_template_message(
        self,
        recipient: str,
        subject: Optional[str],
        content: str,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send template message via Line."""

        message = {
            "type": "template",
            "altText": subject or content,
            "template": metadata.get("template", {})
        }

        return await self._send_line_message(recipient, [message])

    async def _send_media_message(
        self,
        recipient: str,
        content: str,
        attachments: List[Attachment],
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send media message via Line."""

        messages = []

        # Add text message if content provided
        if content:
            messages.append({
                "type": "text",
                "text": content
            })

        # Add media messages
        for attachment in attachments:
            if attachment.content_type.startswith("image/"):
                # For image attachments, we'd need to upload to a public URL first
                # This is a simplified version
                messages.append({
                    "type": "image",
                    "originalContentUrl": metadata.get("image_url", ""),
                    "previewImageUrl": metadata.get("preview_url", "")
                })
            elif attachment.content_type.startswith("video/"):
                messages.append({
                    "type": "video",
                    "originalContentUrl": metadata.get("video_url", ""),
                    "previewImageUrl": metadata.get("preview_url", "")
                })

        return await self._send_line_message(recipient, messages)

    async def _send_line_message(
        self,
        recipient: str,
        messages: List[Dict[str, Any]]
    ) -> MessageResult:
        """Send message(s) to Line user."""

        payload = {
            "to": recipient,
            "messages": messages[:5]  # Line allows max 5 messages per request
        }

        url = f"{self.api_base_url}/message/push"

        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                # Line doesn't return message ID in push response
                message_id = f"line_{recipient}_{int(datetime.utcnow().timestamp())}"

                return self.build_success_response(
                    message_id=message_id,
                    provider_id=message_id,
                    status=MessageStatus.SENT,
                    metadata={
                        "provider": "line",
                        "recipient": recipient,
                        "message_count": len(messages)
                    }
                )
            else:
                error_data = await response.json()
                error_msg = error_data.get("message", "Unknown Line API error")
                return self.build_error_response(
                    error_msg,
                    f"line_{response.status}"
                )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate Line user ID format."""
        # Line user IDs are typically 33 characters starting with 'U'
        return bool(recipient and len(recipient) == 33 and recipient.startswith('U'))

    def validate_signature(self, body: str, signature: str) -> bool:
        """
        Validate Line webhook signature.

        Args:
            body: Request body
            signature: X-Line-Signature header value

        Returns:
            True if signature is valid
        """
        hash_value = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()

        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        return hmac.compare_digest(signature, expected_signature)

    def get_service_name(self) -> str:
        """Get service name."""
        return self.service_name

    def get_supported_features(self) -> List[str]:
        """Get list of supported features."""
        return [
            "text_messages", "rich_messages", "template_messages",
            "flex_messages", "carousel_messages", "image_messages",
            "video_messages", "quick_replies", "push_notifications",
            "user_profiles", "webhook_validation"
        ]

    async def check_service_health(self) -> Dict[str, Any]:
        """Check Line service health."""
        try:
            # Test bot info endpoint
            url = f"{self.api_base_url}/info"

            async with self.session.get(url) as response:
                healthy = response.status == 200
                if healthy:
                    bot_info = await response.json()
                    metadata = {"bot_info": bot_info}
                else:
                    error_data = await response.json()
                    metadata = {"error": error_data}

            return {
                "healthy": healthy,
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "features": self.get_supported_features(),
                "metadata": metadata
            }

        except Exception as e:
            return {
                "healthy": False,
                "service": self.service_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }