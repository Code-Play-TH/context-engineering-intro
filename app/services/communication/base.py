"""
Base communication service class providing common functionality.
All communication services inherit from this base class.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Message status enumeration."""
    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    SPAM = "spam"


class MessagePriority(Enum):
    """Message priority enumeration."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


@dataclass
class MessageResult:
    """Result of sending a message."""
    success: bool
    message_id: Optional[str] = None
    provider_id: Optional[str] = None
    status: MessageStatus = MessageStatus.QUEUED
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DeliveryStatus:
    """Delivery status information."""
    message_id: str
    status: MessageStatus
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Attachment:
    """Message attachment information."""
    filename: str
    content_type: str
    content: bytes
    size: int
    inline: bool = False


class BaseCommunicationService(ABC):
    """
    Abstract base class for communication services.

    Provides common functionality:
    - Message sending
    - Delivery tracking
    - Error handling
    - Template rendering
    """

    def __init__(self):
        self.service_name = "unknown"
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @abstractmethod
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
        Send a message via the communication channel.

        Args:
            recipient: Recipient address/identifier
            subject: Message subject (if applicable)
            content: Message content
            sender: Sender address/identifier
            attachments: List of attachments
            priority: Message priority
            metadata: Additional metadata

        Returns:
            MessageResult with send status and details
        """
        pass

    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """
        Get delivery status for a message.

        Args:
            message_id: Message identifier

        Returns:
            DeliveryStatus or None if not found
        """
        pass

    @abstractmethod
    def get_service_name(self) -> str:
        """Get service name."""
        pass

    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Get list of supported features."""
        pass

    async def send_bulk_messages(
        self,
        messages: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[MessageResult]:
        """
        Send multiple messages concurrently.

        Args:
            messages: List of message data dictionaries
            max_concurrent: Maximum concurrent sends

        Returns:
            List of MessageResult objects
        """
        import asyncio

        # Create semaphore to limit concurrent sends
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_single_message(msg_data: Dict[str, Any]) -> MessageResult:
            async with semaphore:
                try:
                    return await self.send_message(
                        recipient=msg_data.get("recipient"),
                        subject=msg_data.get("subject"),
                        content=msg_data.get("content"),
                        sender=msg_data.get("sender"),
                        attachments=msg_data.get("attachments"),
                        priority=MessagePriority(msg_data.get("priority", MessagePriority.NORMAL.value)),
                        metadata=msg_data.get("metadata")
                    )
                except Exception as e:
                    self.logger.error(f"Failed to send bulk message: {str(e)}")
                    return MessageResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        error=str(e)
                    )

        # Execute all sends concurrently
        tasks = [send_single_message(msg) for msg in messages]
        return await asyncio.gather(*tasks)

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient address format.

        Args:
            recipient: Recipient address to validate

        Returns:
            True if valid, False otherwise
        """
        # Default implementation - override in subclasses
        return bool(recipient and len(recipient.strip()) > 0)

    def validate_content(self, content: str, max_length: Optional[int] = None) -> bool:
        """
        Validate message content.

        Args:
            content: Message content to validate
            max_length: Maximum content length

        Returns:
            True if valid, False otherwise
        """
        if not content or len(content.strip()) == 0:
            return False

        if max_length and len(content) > max_length:
            return False

        return True

    def sanitize_content(self, content: str) -> str:
        """
        Sanitize message content.

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        if not content:
            return ""

        # Remove control characters except newlines and tabs
        import re
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized.strip())

        return sanitized

    def render_template(
        self,
        template: str,
        variables: Dict[str, Any],
        template_engine: str = "jinja2"
    ) -> str:
        """
        Render template with variables.

        Args:
            template: Template string
            variables: Variables to substitute
            template_engine: Template engine to use

        Returns:
            Rendered content
        """
        try:
            if template_engine == "jinja2":
                from jinja2 import Template
                tmpl = Template(template)
                return tmpl.render(**variables)
            else:
                # Simple string formatting fallback
                return template.format(**variables)

        except Exception as e:
            self.logger.error(f"Template rendering failed: {str(e)}")
            return template

    def extract_variables_from_template(self, template: str) -> List[str]:
        """
        Extract variable names from template.

        Args:
            template: Template string

        Returns:
            List of variable names
        """
        import re

        # Find Jinja2-style variables {{ variable }}
        jinja_vars = re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}', template)

        # Find format-style variables {variable}
        format_vars = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', template)

        # Combine and deduplicate
        all_vars = list(set(jinja_vars + format_vars))
        return sorted(all_vars)

    def calculate_send_time(
        self,
        timezone: str = "UTC",
        send_at: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate optimal send time.

        Args:
            timezone: Recipient timezone
            send_at: Specific send time

        Returns:
            Calculated send time
        """
        if send_at:
            return send_at

        # Default to current time
        return datetime.utcnow()

    def build_error_response(self, error_message: str, error_code: str = None) -> MessageResult:
        """
        Build standardized error response.

        Args:
            error_message: Error message
            error_code: Service-specific error code

        Returns:
            MessageResult with error information
        """
        return MessageResult(
            success=False,
            status=MessageStatus.FAILED,
            error=error_message,
            metadata={
                "error_code": error_code,
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def build_success_response(
        self,
        message_id: str,
        provider_id: str = None,
        status: MessageStatus = MessageStatus.SENT,
        metadata: Dict[str, Any] = None
    ) -> MessageResult:
        """
        Build standardized success response.

        Args:
            message_id: Internal message ID
            provider_id: Provider-specific message ID
            status: Message status
            metadata: Additional metadata

        Returns:
            MessageResult with success information
        """
        if metadata is None:
            metadata = {}

        metadata.update({
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        })

        return MessageResult(
            success=True,
            message_id=message_id,
            provider_id=provider_id,
            status=status,
            metadata=metadata
        )

    async def check_service_health(self) -> Dict[str, Any]:
        """
        Check service health and connectivity.

        Returns:
            Health status dictionary
        """
        try:
            # Basic connectivity check - override in subclasses
            return {
                "healthy": True,
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "features": self.get_supported_features()
            }

        except Exception as e:
            return {
                "healthy": False,
                "service": self.service_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get service usage statistics.

        Returns:
            Usage statistics dictionary
        """
        # Basic implementation - override in subclasses for detailed stats
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }