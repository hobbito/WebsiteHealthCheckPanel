"""Base class for notification channels"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class NotificationPayload(BaseModel):
    """Payload sent to notification channels"""
    trigger: str = Field(..., description="Event that triggered the notification")
    site_name: str = Field(..., description="Name of the site")
    site_url: str = Field(..., description="URL of the site")
    check_name: str = Field(..., description="Name of the check")
    check_type: str = Field(..., description="Type of the check")
    status: str = Field(..., description="Status: 'success', 'failure', or 'warning'")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    checked_at: datetime = Field(..., description="Timestamp of the check")
    incident_id: Optional[int] = Field(None, description="Related incident ID if any")


class BaseNotificationChannel(ABC):
    """Abstract base class for notification channels"""

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Unique identifier for this channel type"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for this channel type"""
        pass

    @abstractmethod
    async def send(self, config: Dict[str, Any], payload: NotificationPayload) -> bool:
        """
        Send a notification.

        Args:
            config: Channel-specific configuration
            payload: The notification payload to send

        Returns:
            True if successful, raises exception otherwise
        """
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for channel configuration.

        Returns:
            JSON Schema dict describing required and optional configuration fields
        """
        pass

    @abstractmethod
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """
        Test if the channel configuration is valid.

        Args:
            config: Channel-specific configuration to test

        Returns:
            True if connection test successful, raises exception otherwise
        """
        pass
