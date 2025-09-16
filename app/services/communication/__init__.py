"""
Communication Services Package

Provides comprehensive multi-channel messaging capabilities:
- Email (SendGrid, AWS SES)
- Discord messaging
- Line Messaging API
- WhatsApp Business API (extensible)
- Telegram Bot API (extensible)
- SMS (extensible)

Features:
- Unified interface across all channels
- Multi-channel broadcasting
- Template rendering and personalization
- Delivery tracking and status monitoring
- Rate limiting and error handling
- Rich media support
"""

from app.services.communication.base import (
    BaseCommunicationService, MessageResult, DeliveryStatus,
    MessageStatus, MessagePriority, Attachment
)
from app.services.communication.email import EmailService, EmailProvider
from app.services.communication.discord import DiscordService
from app.services.communication.line import LineService, LineMessageType
from app.services.communication.factory import (
    CommunicationServiceFactory,
    SupportedChannel,
    communication_factory
)

# Export all classes and the factory instance
__all__ = [
    # Base classes and types
    "BaseCommunicationService",
    "MessageResult",
    "DeliveryStatus",
    "MessageStatus",
    "MessagePriority",
    "Attachment",

    # Service implementations
    "EmailService",
    "EmailProvider",
    "DiscordService",
    "LineService",
    "LineMessageType",

    # Factory and utilities
    "CommunicationServiceFactory",
    "SupportedChannel",
    "communication_factory",
]

# Convenience functions for common operations
async def send_email(
    recipient: str,
    subject: str,
    content: str,
    sender: str = None,
    html: bool = False,
    attachments: list = None,
    provider: str = EmailProvider.SENDGRID
) -> MessageResult:
    """
    Send email message via configured provider.

    Args:
        recipient: Recipient email address
        subject: Email subject
        content: Email content
        sender: Sender email address
        html: Whether content is HTML
        attachments: List of attachments
        provider: Email provider to use

    Returns:
        MessageResult with send status

    Example:
        result = await send_email(
            "kol@example.com",
            "Campaign Brief",
            "<h1>Hello!</h1>",
            html=True
        )
    """
    metadata = {"content_type": "html" if html else "plain"}

    service = communication_factory.get_service("email", provider)
    async with service:
        return await service.send_message(
            recipient=recipient,
            subject=subject,
            content=content,
            sender=sender,
            attachments=attachments,
            metadata=metadata
        )


async def send_discord_message(
    user_id: str,
    content: str,
    embed: dict = None,
    files: list = None
) -> MessageResult:
    """
    Send Discord message to user.

    Args:
        user_id: Discord user ID
        content: Message content
        embed: Optional Discord embed object
        files: Optional file attachments

    Returns:
        MessageResult with send status

    Example:
        result = await send_discord_message(
            "123456789012345678",
            "Hi! Here's your campaign brief."
        )
    """
    metadata = {"is_dm": True}

    if embed:
        metadata["content_type"] = "embed"
        metadata["embed"] = embed

    service = communication_factory.get_service("discord")
    async with service:
        return await service.send_message(
            recipient=user_id,
            subject=None,
            content=content,
            attachments=files,
            metadata=metadata
        )


async def send_line_message(
    user_id: str,
    content: str,
    message_type: str = LineMessageType.TEXT,
    template: dict = None,
    flex_content: dict = None
) -> MessageResult:
    """
    Send Line message to user.

    Args:
        user_id: Line user ID
        content: Message content
        message_type: Type of Line message
        template: Template message structure
        flex_content: Flex message content

    Returns:
        MessageResult with send status

    Example:
        result = await send_line_message(
            "U1234567890abcdef1234567890abcdef1",
            "Hello from our campaign team!"
        )
    """
    metadata = {"message_type": message_type}

    if template:
        metadata["template"] = template

    if flex_content:
        metadata["flex_content"] = flex_content

    service = communication_factory.get_service("line")
    async with service:
        return await service.send_message(
            recipient=user_id,
            subject=None,
            content=content,
            metadata=metadata
        )


async def broadcast_to_kol(
    kol_contacts: dict,
    subject: str,
    content: str,
    sender: str = None,
    priority: MessagePriority = MessagePriority.NORMAL
) -> Dict[str, MessageResult]:
    """
    Broadcast message to KOL across all their communication channels.

    Args:
        kol_contacts: Dict of channel -> contact info
        subject: Message subject
        content: Message content
        sender: Sender identifier
        priority: Message priority

    Returns:
        Dict of channel -> MessageResult

    Example:
        result = await broadcast_to_kol(
            {
                "email": "kol@example.com",
                "discord": "123456789012345678",
                "line": "U1234567890abcdef1234567890abcdef1"
            },
            "Campaign Update",
            "Your campaign is ready to begin!"
        )
    """
    channels = list(kol_contacts.keys())

    return await communication_factory.broadcast_message(
        channels=channels,
        recipients=kol_contacts,
        subject=subject,
        content=content,
        sender=sender,
        priority=priority
    )


async def send_personalized_campaign_messages(
    campaign_messages: list,
    max_concurrent: int = 10
) -> List[MessageResult]:
    """
    Send personalized campaign messages to multiple KOLs.

    Args:
        campaign_messages: List of message configurations
        max_concurrent: Maximum concurrent sends

    Returns:
        List of MessageResult objects

    Example:
        messages = [
            {
                "channel": "email",
                "recipient": "kol1@example.com",
                "subject": "Hi {{name}}!",
                "content": "Your campaign brief is ready.",
                "metadata": {"name": "John"}
            },
            {
                "channel": "discord",
                "recipient": "123456789012345678",
                "content": "Hi {{name}}! Campaign brief ready.",
                "metadata": {"name": "Jane"}
            }
        ]
        results = await send_personalized_campaign_messages(messages)
    """
    # Render personalized content for each message
    processed_messages = []

    for msg in campaign_messages:
        # Render template variables if present
        template_vars = msg.get("metadata", {})

        # Render subject
        subject = msg.get("subject", "")
        if subject and template_vars:
            subject = communication_factory._render_personalized_content(subject, template_vars)

        # Render content
        content = msg.get("content", "")
        if content and template_vars:
            content = communication_factory._render_personalized_content(content, template_vars)

        processed_msg = msg.copy()
        processed_msg["subject"] = subject
        processed_msg["content"] = content
        processed_messages.append(processed_msg)

    return await communication_factory.send_personalized_messages(
        processed_messages, max_concurrent
    )


async def track_message_delivery(
    message_tracking: list
) -> Dict[str, Optional[DeliveryStatus]]:
    """
    Track delivery status of multiple messages across channels.

    Args:
        message_tracking: List of tracking info dicts

    Returns:
        Dict of tracking_key -> DeliveryStatus

    Example:
        tracking = [
            {"channel": "email", "message_id": "msg_123", "provider": "sendgrid"},
            {"channel": "discord", "message_id": "123_456789"}
        ]
        statuses = await track_message_delivery(tracking)
    """
    return await communication_factory.get_delivery_statuses(message_tracking)


def get_supported_channels() -> List[str]:
    """
    Get list of supported communication channels.

    Returns:
        List of channel names

    Example:
        channels = get_supported_channels()
        # Returns: ['email', 'discord', 'line']
    """
    return communication_factory.get_supported_channels()


def get_channel_capabilities(channel: str) -> List[str]:
    """
    Get capabilities of a specific communication channel.

    Args:
        channel: Channel name

    Returns:
        List of supported features

    Example:
        caps = get_channel_capabilities("email")
        # Returns: ['html_content', 'attachments', 'templates', ...]
    """
    return communication_factory.get_channel_capabilities(channel)


def get_channel_limits(channel: str) -> Dict[str, Any]:
    """
    Get rate limits and constraints for a channel.

    Args:
        channel: Channel name

    Returns:
        Dict of limits and constraints

    Example:
        limits = get_channel_limits("discord")
        # Returns: {'content_max_length': 2000, 'rate_limit_per_second': 5, ...}
    """
    return communication_factory.get_channel_limits(channel)


async def validate_kol_contacts(contacts: Dict[str, str]) -> Dict[str, bool]:
    """
    Validate KOL contact information across channels.

    Args:
        contacts: Dict of channel -> contact info

    Returns:
        Dict of channel -> is_valid

    Example:
        validation = await validate_kol_contacts({
            "email": "kol@example.com",
            "discord": "123456789012345678",
            "line": "invalid_line_id"
        })
        # Returns: {"email": True, "discord": True, "line": False}
    """
    return await communication_factory.validate_recipients(contacts)


async def check_communication_health() -> Dict[str, Dict[str, Any]]:
    """
    Check health status of all communication services.

    Returns:
        Dict of channel -> health status

    Example:
        health = await check_communication_health()
        # Returns: {"email": {"healthy": True, ...}, "discord": {"healthy": False, ...}}
    """
    return await communication_factory.check_all_services_health()


# Channel-specific configuration and limits
CHANNEL_FEATURES = {
    "email": {
        "supports_html": True,
        "supports_attachments": True,
        "supports_templates": True,
        "supports_scheduling": True,
        "supports_tracking": True,
        "rich_formatting": True
    },
    "discord": {
        "supports_html": False,
        "supports_attachments": True,
        "supports_templates": False,
        "supports_scheduling": False,
        "supports_tracking": True,
        "rich_formatting": True,  # Markdown + embeds
        "supports_embeds": True,
        "supports_reactions": True
    },
    "line": {
        "supports_html": False,
        "supports_attachments": True,
        "supports_templates": True,
        "supports_scheduling": False,
        "supports_tracking": False,
        "rich_formatting": True,  # Flex messages
        "supports_quick_replies": True,
        "supports_carousel": True
    }
}


def get_channel_features(channel: str) -> Dict[str, bool]:
    """
    Get feature matrix for a communication channel.

    Args:
        channel: Channel name

    Returns:
        Dict of feature -> is_supported

    Example:
        features = get_channel_features("email")
        # Returns: {"supports_html": True, "supports_attachments": True, ...}
    """
    return CHANNEL_FEATURES.get(channel.lower(), {})