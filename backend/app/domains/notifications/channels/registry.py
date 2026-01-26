"""Registry for notification channels"""
from typing import Dict, Type, List, Any
from .base import BaseNotificationChannel


class ChannelRegistry:
    """Registry for notification channel implementations"""
    _channels: Dict[str, Type[BaseNotificationChannel]] = {}

    @classmethod
    def register(cls, channel_class: Type[BaseNotificationChannel]) -> None:
        """Register a notification channel class"""
        instance = channel_class()
        channel_type = instance.channel_type

        if channel_type in cls._channels:
            raise ValueError(f"Channel type '{channel_type}' is already registered")

        cls._channels[channel_type] = channel_class
        print(f"✓ Registered notification channel: {channel_type}")

    @classmethod
    def is_registered(cls, channel_type: str) -> bool:
        """Check if a channel type is registered"""
        return channel_type in cls._channels

    @classmethod
    def get_channel(cls, channel_type: str) -> Type[BaseNotificationChannel]:
        """Get a channel class by type"""
        if channel_type not in cls._channels:
            available = ", ".join(cls._channels.keys())
            raise KeyError(f"Channel type '{channel_type}' not found. Available: {available}")
        return cls._channels[channel_type]

    @classmethod
    def list_channels(cls) -> List[Dict[str, Any]]:
        """List all registered channels with their schemas"""
        result = []
        for channel_type, channel_class in cls._channels.items():
            instance = channel_class()
            result.append({
                "type": channel_type,
                "display_name": instance.display_name,
                "config_schema": instance.get_config_schema()
            })
        return result


def register_channel(channel_class: Type[BaseNotificationChannel]) -> Type[BaseNotificationChannel]:
    """Decorator to register a notification channel"""
    ChannelRegistry.register(channel_class)
    return channel_class
