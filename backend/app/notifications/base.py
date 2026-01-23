from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class NotificationMessage:
    """Message to be sent via a notification channel"""
    recipient: str  # Email address, webhook URL, etc.
    subject: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None  # Additional channel-specific data


class BaseNotificationChannel(ABC):
    """
    Abstract base class for notification channels.

    Each channel type must implement:
    - send(): Send the notification
    - get_config_schema(): Return JSON schema for configuration
    - get_display_name(): Human-readable name
    """

    @abstractmethod
    async def send(self, config: Dict[str, Any], message: NotificationMessage) -> tuple[bool, Optional[str]]:
        """
        Send a notification message.

        Args:
            config: Channel-specific configuration
            message: The message to send

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """
        Return JSON Schema for validating channel configuration.

        Returns:
            JSON Schema dict
        """
        pass

    @classmethod
    @abstractmethod
    def get_display_name(cls) -> str:
        """
        Return human-readable name for this channel type.

        Returns:
            Display name (e.g., "Email", "Slack Webhook")
        """
        pass

    @classmethod
    def get_channel_type(cls) -> str:
        """
        Return unique identifier for this channel type.

        Returns:
            Channel type identifier (e.g., "email", "slack")
        """
        class_name = cls.__name__
        if class_name.endswith("Channel"):
            class_name = class_name[:-7]  # Remove "Channel" suffix
        return class_name.lower()
