"""
Discord communication service for messaging KOLs via Discord.
Implements Discord API for direct messages and server communications.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import aiohttp
import json

from app.core.config import get_settings
from app.services.communication.base import (
    BaseCommunicationService, MessageResult, DeliveryStatus,
    MessageStatus, MessagePriority, Attachment
)

logger = logging.getLogger(__name__)


class DiscordService(BaseCommunicationService):
    """
    Discord communication service for KOL messaging.

    Features:
    - Direct message sending
    - Server/channel messaging
    - File attachments
    - Rich embeds
    - Message reactions
    - Delivery tracking
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.service_name = "discord"
        self.api_base_url = "https://discord.com/api/v10"
        self.bot_token = self.settings.DISCORD_BOT_TOKEN

        # Rate limiting
        self.rate_limit_per_second = 5
        self.rate_limit_per_minute = 30

        # Initialize session
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "Authorization": f"Bot {self.bot_token}",
                "User-Agent": "KOL-Management-System/1.0",
                "Content-Type": "application/json"
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
        Send Discord message to user or channel.

        Args:
            recipient: Discord user ID or channel ID
            subject: Message title (used in embeds)
            content: Message content
            sender: Sender identifier (bot name)
            attachments: List of file attachments
            priority: Message priority
            metadata: Additional metadata (embed settings, etc.)

        Returns:
            MessageResult with send status
        """
        if metadata is None:
            metadata = {}

        # Validate inputs
        if not self.validate_recipient(recipient):
            return self.build_error_response("Invalid Discord recipient ID")

        if not self.validate_content(content, max_length=2000):
            return self.build_error_response("Content is required and must be under 2000 characters")

        try:
            # Determine if recipient is a user or channel
            is_dm = metadata.get("is_dm", True)

            if is_dm:
                # Send direct message
                return await self._send_direct_message(
                    recipient, subject, content, attachments, priority, metadata
                )
            else:
                # Send channel message
                return await self._send_channel_message(
                    recipient, subject, content, attachments, priority, metadata
                )

        except Exception as e:
            self.logger.error(f"Discord message send failed: {str(e)}")
            return self.build_error_response(str(e))

    async def send_embed_message(
        self,
        recipient: str,
        title: str,
        description: str,
        fields: Optional[List[Dict[str, Any]]] = None,
        color: int = 0x3498db,
        footer: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        is_dm: bool = True
    ) -> MessageResult:
        """
        Send Discord embed message.

        Args:
            recipient: Discord user ID or channel ID
            title: Embed title
            description: Embed description
            fields: List of embed fields
            color: Embed color (hex)
            footer: Embed footer text
            thumbnail_url: Thumbnail image URL
            image_url: Main image URL
            is_dm: Whether to send as DM or channel message

        Returns:
            MessageResult with send status
        """
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }

        if fields:
            embed["fields"] = fields

        if footer:
            embed["footer"] = {"text": footer}

        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}

        if image_url:
            embed["image"] = {"url": image_url}

        metadata = {
            "embed": embed,
            "is_dm": is_dm,
            "content_type": "embed"
        }

        return await self.send_message(
            recipient=recipient,
            subject=title,
            content=description,
            metadata=metadata
        )

    async def send_file_message(
        self,
        recipient: str,
        content: str,
        files: List[Attachment],
        is_dm: bool = True
    ) -> MessageResult:
        """
        Send Discord message with file attachments.

        Args:
            recipient: Discord user ID or channel ID
            content: Message content
            files: List of file attachments
            is_dm: Whether to send as DM or channel message

        Returns:
            MessageResult with send status
        """
        if not files:
            return self.build_error_response("No files provided")

        metadata = {
            "is_dm": is_dm,
            "has_files": True
        }

        return await self.send_message(
            recipient=recipient,
            subject=None,
            content=content,
            attachments=files,
            metadata=metadata
        )

    async def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """
        Get delivery status for a Discord message.

        Args:
            message_id: Discord message ID

        Returns:
            DeliveryStatus or None if not found
        """
        try:
            # Try to fetch the message to verify it exists
            url = f"{self.api_base_url}/channels/{message_id.split('_')[0]}/messages/{message_id.split('_')[1]}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    message_data = await response.json()
                    return DeliveryStatus(
                        message_id=message_id,
                        status=MessageStatus.DELIVERED,
                        delivered_at=datetime.fromisoformat(message_data["timestamp"].replace("Z", "+00:00")),
                        metadata={
                            "provider": "discord",
                            "message_data": message_data
                        }
                    )
                else:
                    return None

        except Exception as e:
            self.logger.error(f"Failed to get Discord message status: {str(e)}")
            return None

    async def create_dm_channel(self, user_id: str) -> Optional[str]:
        """
        Create a DM channel with a user.

        Args:
            user_id: Discord user ID

        Returns:
            DM channel ID or None if failed
        """
        try:
            payload = {"recipient_id": user_id}
            url = f"{self.api_base_url}/users/@me/channels"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    channel_data = await response.json()
                    return channel_data["id"]
                else:
                    self.logger.error(f"Failed to create DM channel: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Failed to create DM channel: {str(e)}")
            return None

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Discord user information.

        Args:
            user_id: Discord user ID

        Returns:
            User information dictionary or None if not found
        """
        try:
            url = f"{self.api_base_url}/users/{user_id}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

        except Exception as e:
            self.logger.error(f"Failed to get user info: {str(e)}")
            return None

    # Private helper methods

    async def _send_direct_message(
        self,
        user_id: str,
        subject: Optional[str],
        content: str,
        attachments: Optional[List[Attachment]],
        priority: MessagePriority,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send direct message to a Discord user."""

        # First, create/get DM channel
        dm_channel_id = await self.create_dm_channel(user_id)
        if not dm_channel_id:
            return self.build_error_response("Failed to create DM channel")

        # Send message to DM channel
        return await self._send_to_channel(
            dm_channel_id, subject, content, attachments, priority, metadata
        )

    async def _send_channel_message(
        self,
        channel_id: str,
        subject: Optional[str],
        content: str,
        attachments: Optional[List[Attachment]],
        priority: MessagePriority,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send message to a Discord channel."""

        return await self._send_to_channel(
            channel_id, subject, content, attachments, priority, metadata
        )

    async def _send_to_channel(
        self,
        channel_id: str,
        subject: Optional[str],
        content: str,
        attachments: Optional[List[Attachment]],
        priority: MessagePriority,
        metadata: Dict[str, Any]
    ) -> MessageResult:
        """Send message to a specific Discord channel."""

        # Build message payload
        payload = {}

        # Check if this is an embed message
        if metadata.get("content_type") == "embed" and metadata.get("embed"):
            payload["embeds"] = [metadata["embed"]]
            if content and content != metadata["embed"].get("description", ""):
                payload["content"] = content
        else:
            payload["content"] = content

        url = f"{self.api_base_url}/channels/{channel_id}/messages"

        # Handle file attachments
        if attachments and metadata.get("has_files"):
            return await self._send_with_files(url, payload, attachments, channel_id)
        else:
            return await self._send_json_message(url, payload, channel_id)

    async def _send_json_message(
        self,
        url: str,
        payload: Dict[str, Any],
        channel_id: str
    ) -> MessageResult:
        """Send JSON message to Discord."""

        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                message_data = await response.json()
                message_id = f"{channel_id}_{message_data['id']}"

                return self.build_success_response(
                    message_id=message_id,
                    provider_id=message_data["id"],
                    status=MessageStatus.SENT,
                    metadata={
                        "provider": "discord",
                        "channel_id": channel_id,
                        "message_data": message_data
                    }
                )
            else:
                error_data = await response.text()
                return self.build_error_response(
                    f"Discord API error: {error_data}",
                    f"discord_{response.status}"
                )

    async def _send_with_files(
        self,
        url: str,
        payload: Dict[str, Any],
        attachments: List[Attachment],
        channel_id: str
    ) -> MessageResult:
        """Send message with file attachments to Discord."""

        # Prepare multipart form data
        data = aiohttp.FormData()

        # Add JSON payload
        data.add_field("payload_json", json.dumps(payload), content_type="application/json")

        # Add files
        for i, attachment in enumerate(attachments):
            data.add_field(
                f"file{i}",
                attachment.content,
                filename=attachment.filename,
                content_type=attachment.content_type
            )

        # Temporary headers without Content-Type (aiohttp will set it for multipart)
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "User-Agent": "KOL-Management-System/1.0"
        }

        async with self.session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                message_data = await response.json()
                message_id = f"{channel_id}_{message_data['id']}"

                return self.build_success_response(
                    message_id=message_id,
                    provider_id=message_data["id"],
                    status=MessageStatus.SENT,
                    metadata={
                        "provider": "discord",
                        "channel_id": channel_id,
                        "message_data": message_data,
                        "attachments_count": len(attachments)
                    }
                )
            else:
                error_data = await response.text()
                return self.build_error_response(
                    f"Discord file upload error: {error_data}",
                    f"discord_files_{response.status}"
                )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate Discord ID format."""
        # Discord IDs are 17-19 digit numbers
        return bool(recipient and recipient.isdigit() and 17 <= len(recipient) <= 19)

    def get_service_name(self) -> str:
        """Get service name."""
        return self.service_name

    def get_supported_features(self) -> List[str]:
        """Get list of supported features."""
        return [
            "direct_messages", "channel_messages", "rich_embeds",
            "file_attachments", "message_reactions", "delivery_tracking",
            "user_lookup", "markdown_formatting"
        ]

    async def check_service_health(self) -> Dict[str, Any]:
        """Check Discord service health."""
        try:
            # Test bot connectivity
            url = f"{self.api_base_url}/users/@me"

            async with self.session.get(url) as response:
                healthy = response.status == 200
                if healthy:
                    bot_data = await response.json()
                    metadata = {"bot_info": bot_data}
                else:
                    metadata = {"error": await response.text()}

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