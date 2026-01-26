"""Tests for notification channel registry"""
import pytest
from app.domains.notifications.channels.registry import ChannelRegistry
from app.domains.notifications.channels.base import BaseNotificationChannel


class TestChannelRegistry:
    """Tests for ChannelRegistry"""

    def test_email_channel_is_registered(self):
        """Test that email channel is registered"""
        assert ChannelRegistry.is_registered("email")

    def test_webhook_channel_is_registered(self):
        """Test that webhook channel is registered"""
        assert ChannelRegistry.is_registered("webhook")

    def test_get_channel_returns_class(self):
        """Test that get_channel returns the channel class"""
        channel_class = ChannelRegistry.get_channel("email")
        assert issubclass(channel_class, BaseNotificationChannel)

    def test_get_channel_unknown_type(self):
        """Test that get_channel raises error for unknown type"""
        with pytest.raises(KeyError) as exc_info:
            ChannelRegistry.get_channel("unknown_channel_type")
        assert "not found" in str(exc_info.value).lower()

    def test_is_registered_false_for_unknown(self):
        """Test that is_registered returns False for unknown type"""
        assert not ChannelRegistry.is_registered("unknown_channel_type")

    def test_list_channels_returns_all(self):
        """Test that list_channels returns all registered channels"""
        channels = ChannelRegistry.list_channels()
        assert len(channels) >= 2  # At least email and webhook

        channel_types = [c["type"] for c in channels]
        assert "email" in channel_types
        assert "webhook" in channel_types

    def test_list_channels_contains_schema(self):
        """Test that list_channels includes config schema"""
        channels = ChannelRegistry.list_channels()
        for channel in channels:
            assert "type" in channel
            assert "display_name" in channel
            assert "config_schema" in channel

    def test_channel_instance_has_required_methods(self):
        """Test that channel instances have all required methods"""
        channel_class = ChannelRegistry.get_channel("email")
        channel_instance = channel_class()

        assert hasattr(channel_instance, "channel_type")
        assert hasattr(channel_instance, "display_name")
        assert hasattr(channel_instance, "send")
        assert hasattr(channel_instance, "get_config_schema")
        assert hasattr(channel_instance, "test_connection")
