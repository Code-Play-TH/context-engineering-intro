"""
Communication Service Factory for managing multi-channel messaging.
Provides centralized access to all communication services.
"""

import logging
from typing import Dict, List, Optional, Any, Type, Union
from enum import Enum

from app.services.communication.base import (
    BaseCommunicationService, MessageResult, DeliveryStatus,
    MessageStatus, MessagePriority, Attachment
)
from app.services.communication.email import EmailService, EmailProvider
from app.services.communication.discord import DiscordService
from app.services.communication.line import LineService

logger = logging.getLogger(__name__)


class SupportedChannel(Enum):
    """Enumeration of supported communication channels."""
    EMAIL = "email"
    DISCORD = "discord"
    LINE = "line"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"


class CommunicationServiceFactory:
    """
    Factory class for creating and managing communication services.

    Features:
    - Channel-specific service creation
    - Service caching and reuse
    - Unified interface for all channels
    - Multi-channel message broadcasting
    - Delivery tracking across channels
    """

    def __init__(self):
        self._services: Dict[str, BaseCommunicationService] = {}
        self._service_classes: Dict[str, Type[BaseCommunicationService]] = {
            SupportedChannel.EMAIL.value: EmailService,
            SupportedChannel.DISCORD.value: DiscordService,
            SupportedChannel.LINE.value: LineService,
            # Additional services can be added here
        }

    def get_service(
        self,
        channel: Union[str, SupportedChannel],
        provider: Optional[str] = None
    ) -> BaseCommunicationService:
        """
        Get service instance for specified communication channel.

        Args:
            channel: Communication channel name or enum
            provider: Optional provider for channels that support multiple providers

        Returns:
            Channel-specific service instance

        Raises:
            ValueError: If channel is not supported
        """
        if isinstance(channel, SupportedChannel):
            channel_name = channel.value
        else:
            channel_name = channel.lower()

        if channel_name not in self._service_classes:
            raise ValueError(f"Unsupported communication channel: {channel_name}")

        # Create service key including provider if specified
        service_key = f"{channel_name}_{provider}" if provider else channel_name

        # Return cached service or create new one
        if service_key not in self._services:
            service_class = self._service_classes[channel_name]

            # Handle provider-specific initialization
            if channel_name == SupportedChannel.EMAIL.value and provider:
                self._services[service_key] = service_class(provider=provider)
            else:
                self._services[service_key] = service_class()

        return self._services[service_key]

    async def send_message_to_channel(
        self,
        channel: str,
        recipient: str,
        subject: Optional[str],
        content: str,
        sender: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None
    ) -> MessageResult:
        """
        Send message via specific communication channel.

        Args:
            channel: Communication channel name
            recipient: Recipient address/identifier
            subject: Message subject
            content: Message content
            sender: Sender address/identifier
            attachments: List of attachments
            priority: Message priority
            metadata: Additional metadata
            provider: Optional provider for multi-provider channels

        Returns:
            MessageResult with send status
        """
        try:
            service = self.get_service(channel, provider)

            async with service:
                return await service.send_message(
                    recipient=recipient,
                    subject=subject,
                    content=content,
                    sender=sender,
                    attachments=attachments,
                    priority=priority,
                    metadata=metadata
                )

        except Exception as e:
            logger.error(f"Failed to send message via {channel}: {str(e)}")
            return MessageResult(
                success=False,
                status=MessageStatus.FAILED,
                error=str(e),
                metadata={"channel": channel, "provider": provider}
            )

    async def broadcast_message(
        self,
        channels: List[str],
        recipients: Dict[str, str],
        subject: Optional[str],
        content: str,
        sender: Optional[str] = None,
        channel_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Dict[str, MessageResult]:
        """
        Broadcast message across multiple communication channels.

        Args:
            channels: List of communication channels
            recipients: Dict of channel -> recipient mapping
            subject: Message subject
            content: Message content
            sender: Sender address/identifier
            channel_metadata: Channel-specific metadata
            priority: Message priority

        Returns:
            Dict of channel -> MessageResult
        """
        if channel_metadata is None:
            channel_metadata = {}

        results = {}

        # Send to each channel concurrently
        import asyncio

        async def send_to_channel(channel: str) -> tuple:
            recipient = recipients.get(channel)
            if not recipient:
                return channel, MessageResult(
                    success=False,
                    status=MessageStatus.FAILED,
                    error=f"No recipient specified for {channel}"
                )

            metadata = channel_metadata.get(channel, {})
            result = await self.send_message_to_channel(
                channel=channel,
                recipient=recipient,
                subject=subject,
                content=content,
                sender=sender,
                priority=priority,
                metadata=metadata
            )
            return channel, result

        # Execute all sends concurrently
        tasks = [send_to_channel(channel) for channel in channels]
        channel_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in channel_results:
            if isinstance(result, Exception):
                logger.error(f"Broadcast send failed: {str(result)}")
                continue

            channel, message_result = result
            results[channel] = message_result

        return results

    async def send_personalized_messages(
        self,
        messages: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[MessageResult]:
        """
        Send multiple personalized messages across different channels.

        Args:
            messages: List of message configurations
            max_concurrent: Maximum concurrent sends

        Returns:
            List of MessageResult objects
        """
        import asyncio

        # Create semaphore to limit concurrent sends
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_single_message(msg_config: Dict[str, Any]) -> MessageResult:
            async with semaphore:
                try:
                    return await self.send_message_to_channel(
                        channel=msg_config.get("channel"),
                        recipient=msg_config.get("recipient"),
                        subject=msg_config.get("subject"),
                        content=msg_config.get("content"),
                        sender=msg_config.get("sender"),
                        attachments=msg_config.get("attachments"),
                        priority=MessagePriority(msg_config.get("priority", MessagePriority.NORMAL.value)),
                        metadata=msg_config.get("metadata"),
                        provider=msg_config.get("provider")
                    )
                except Exception as e:
                    logger.error(f"Failed to send personalized message: {str(e)}")
                    return MessageResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        error=str(e)
                    )

        # Execute all sends concurrently
        tasks = [send_single_message(msg) for msg in messages]
        return await asyncio.gather(*tasks)

    async def get_delivery_statuses(
        self,
        message_tracking: List[Dict[str, str]]
    ) -> Dict[str, Optional[DeliveryStatus]]:
        """
        Get delivery statuses for multiple messages across channels.

        Args:
            message_tracking: List of dicts with channel, message_id, provider

        Returns:
            Dict of tracking_key -> DeliveryStatus
        """
        results = {}

        async def get_status(tracking_info: Dict[str, str]) -> tuple:
            channel = tracking_info.get("channel")
            message_id = tracking_info.get("message_id")
            provider = tracking_info.get("provider")

            tracking_key = f"{channel}_{message_id}"

            try:
                service = self.get_service(channel, provider)
                async with service:
                    status = await service.get_delivery_status(message_id)
                return tracking_key, status

            except Exception as e:
                logger.error(f"Failed to get delivery status for {tracking_key}: {str(e)}")
                return tracking_key, None

        # Execute all status checks concurrently
        tasks = [get_status(tracking) for tracking in message_tracking]
        status_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in status_results:
            if isinstance(result, Exception):
                logger.error(f"Status check failed: {str(result)}")
                continue

            tracking_key, status = result
            results[tracking_key] = status

        return results

    async def validate_recipients(
        self,
        recipients: Dict[str, str]
    ) -> Dict[str, bool]:
        """
        Validate recipient addresses across multiple channels.

        Args:
            recipients: Dict of channel -> recipient mapping

        Returns:
            Dict of channel -> is_valid
        """
        validation_results = {}

        for channel, recipient in recipients.items():
            try:
                service = self.get_service(channel)
                is_valid = service.validate_recipient(recipient)
                validation_results[channel] = is_valid

            except Exception as e:
                logger.warning(f"Validation failed for {channel}: {str(e)}")
                validation_results[channel] = False

        return validation_results

    async def check_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health status of all communication services.

        Returns:
            Dict of channel -> health status
        """
        health_results = {}

        for channel_name in self._service_classes.keys():
            try:
                service = self.get_service(channel_name)
                async with service:
                    health_status = await service.check_service_health()
                health_results[channel_name] = health_status

            except Exception as e:
                health_results[channel_name] = {
                    "healthy": False,
                    "service": channel_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        return health_results

    def get_supported_channels(self) -> List[str]:
        """Get list of supported communication channels."""
        return list(self._service_classes.keys())

    def is_channel_supported(self, channel: str) -> bool:
        """Check if communication channel is supported."""
        return channel.lower() in self._service_classes

    def get_channel_capabilities(self, channel: str) -> List[str]:
        """
        Get capabilities of a specific communication channel.

        Args:
            channel: Channel name

        Returns:
            List of supported features
        """
        try:
            service = self.get_service(channel)
            return service.get_supported_features()

        except ValueError:
            return []

    def get_channel_limits(self, channel: str) -> Dict[str, Any]:
        """
        Get rate limits and constraints for a channel.

        Args:
            channel: Channel name

        Returns:
            Dict of limits and constraints
        """
        channel_limits = {
            "email": {
                "max_recipients_per_message": 1000,
                "max_attachment_size_mb": 25,
                "max_attachments": 10,
                "rate_limit_per_hour": 10000,
                "content_max_length": 100000
            },
            "discord": {
                "max_recipients_per_message": 1,
                "max_attachment_size_mb": 8,
                "max_attachments": 10,
                "rate_limit_per_second": 5,
                "content_max_length": 2000
            },
            "line": {
                "max_recipients_per_message": 500,
                "max_attachment_size_mb": 10,
                "max_messages_per_request": 5,
                "rate_limit_per_minute": 1000,
                "content_max_length": 5000
            },
            "whatsapp": {
                "max_recipients_per_message": 256,
                "max_attachment_size_mb": 16,
                "max_attachments": 1,
                "rate_limit_per_second": 10,
                "content_max_length": 4096
            },
            "telegram": {
                "max_recipients_per_message": 1,
                "max_attachment_size_mb": 50,
                "max_attachments": 10,
                "rate_limit_per_second": 30,
                "content_max_length": 4096
            },
            "sms": {
                "max_recipients_per_message": 1,
                "max_attachments": 0,
                "rate_limit_per_minute": 100,
                "content_max_length": 1600
            }
        }

        return channel_limits.get(channel.lower(), {})

    def create_bulk_message_config(
        self,
        base_content: str,
        recipients_by_channel: Dict[str, List[str]],
        personalizations: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create bulk message configuration for multiple channels and recipients.

        Args:
            base_content: Base message content
            recipients_by_channel: Dict of channel -> list of recipients
            personalizations: Optional personalizations per recipient

        Returns:
            List of message configurations ready for sending
        """
        if personalizations is None:
            personalizations = {}

        message_configs = []

        for channel, recipients in recipients_by_channel.items():
            for recipient in recipients:
                # Get personalization for this recipient
                recipient_data = personalizations.get(recipient, {})

                # Render personalized content
                personalized_content = self._render_personalized_content(
                    base_content, recipient_data
                )

                config = {
                    "channel": channel,
                    "recipient": recipient,
                    "content": personalized_content,
                    "subject": recipient_data.get("subject"),
                    "sender": recipient_data.get("sender"),
                    "metadata": recipient_data.get("metadata", {}),
                    "priority": recipient_data.get("priority", MessagePriority.NORMAL.value)
                }

                message_configs.append(config)

        return message_configs

    def _render_personalized_content(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render personalized content using template variables."""
        try:
            from jinja2 import Template
            tmpl = Template(template)
            return tmpl.render(**variables)
        except Exception as e:
            logger.warning(f"Template rendering failed: {str(e)}")
            return template


# Global factory instance
communication_factory = CommunicationServiceFactory()