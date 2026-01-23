from typing import Dict, Type, List
from app.notifications.base import BaseNotificationChannel


class NotificationRegistry:
    """Registry for all available notification channel types"""

    _channels: Dict[str, Type[BaseNotificationChannel]] = {}

    @classmethod
    def register(cls, channel_class: Type[BaseNotificationChannel]) -> Type[BaseNotificationChannel]:
        """Register a notification channel"""
        channel_type = channel_class.get_channel_type()
        cls._channels[channel_type] = channel_class
        return channel_class

    @classmethod
    def get_channel(cls, channel_type: str) -> Type[BaseNotificationChannel]:
        """Get a channel class by type"""
        if channel_type not in cls._channels:
            raise KeyError(f"Channel type '{channel_type}' not registered")
        return cls._channels[channel_type]

    @classmethod
    def list_channels(cls) -> List[Dict[str, any]]:
        """List all registered channels with metadata"""
        return [
            {
                "type": channel_type,
                "display_name": channel_class.get_display_name(),
                "config_schema": channel_class.get_config_schema(),
            }
            for channel_type, channel_class in cls._channels.items()
        ]

    @classmethod
    def is_registered(cls, channel_type: str) -> bool:
        """Check if a channel type is registered"""
        return channel_type in cls._channels
