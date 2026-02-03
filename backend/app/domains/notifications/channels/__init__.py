"""Notification channels package"""
from .base import BaseNotificationChannel, NotificationPayload
from .registry import ChannelRegistry, register_channel

# Import channel implementations to trigger registration
from . import email
from . import webhook

__all__ = [
    "BaseNotificationChannel",
    "NotificationPayload",
    "ChannelRegistry",
    "register_channel",
]
