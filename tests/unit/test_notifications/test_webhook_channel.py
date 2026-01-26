"""Tests for webhook notification channel"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import httpx

from app.domains.notifications.channels.webhook import WebhookChannel
from app.domains.notifications.channels.base import NotificationPayload


@pytest.fixture
def webhook_channel():
    return WebhookChannel()


@pytest.fixture
def sample_payload():
    return NotificationPayload(
        trigger="check_failure",
        site_name="Test Site",
        site_url="https://example.com",
        check_name="HTTP Check",
        check_type="http",
        status="failure",
        error_message="Connection refused",
        response_time_ms=None,
        checked_at=datetime.now(timezone.utc)
    )


class TestWebhookChannel:
    """Tests for WebhookChannel"""

    def test_channel_type(self, webhook_channel):
        """Test channel type identifier"""
        assert webhook_channel.channel_type == "webhook"

    def test_display_name(self, webhook_channel):
        """Test display name"""
        assert "Webhook" in webhook_channel.display_name

    def test_config_schema(self, webhook_channel):
        """Test configuration schema"""
        schema = webhook_channel.get_config_schema()
        assert "properties" in schema
        assert "url" in schema["properties"]
        assert "method" in schema["properties"]
        assert "auth_type" in schema["properties"]
        assert "url" in schema.get("required", [])

    @pytest.mark.asyncio
    async def test_send_success(self, webhook_channel, sample_payload):
        """Test successful webhook delivery"""
        config = {
            "url": "https://hooks.example.com/webhook",
            "method": "POST"
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            result = await webhook_channel.send(config, sample_payload)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_with_bearer_auth(self, webhook_channel, sample_payload):
        """Test webhook with bearer authentication"""
        config = {
            "url": "https://api.example.com/webhook",
            "method": "POST",
            "auth_type": "bearer",
            "auth_token": "secret-token"
        }

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.request = AsyncMock(return_value=mock_response)

            await webhook_channel.send(config, sample_payload)

            # Verify Authorization header was included
            call_kwargs = mock_instance.request.call_args
            assert "Authorization" in call_kwargs.kwargs.get("headers", {})
            assert "Bearer secret-token" in call_kwargs.kwargs["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_send_with_basic_auth(self, webhook_channel, sample_payload):
        """Test webhook with basic authentication"""
        config = {
            "url": "https://api.example.com/webhook",
            "method": "POST",
            "auth_type": "basic",
            "auth_username": "user",
            "auth_password": "pass"
        }

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.request = AsyncMock(return_value=mock_response)

            await webhook_channel.send(config, sample_payload)

            # Verify auth was passed
            call_kwargs = mock_instance.request.call_args
            assert call_kwargs.kwargs.get("auth") is not None

    @pytest.mark.asyncio
    async def test_send_with_custom_headers(self, webhook_channel, sample_payload):
        """Test webhook with custom headers"""
        config = {
            "url": "https://hooks.example.com/webhook",
            "method": "POST",
            "headers": {"X-Custom-Header": "custom-value"}
        }

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.request = AsyncMock(return_value=mock_response)

            await webhook_channel.send(config, sample_payload)

            call_kwargs = mock_instance.request.call_args
            assert "X-Custom-Header" in call_kwargs.kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_send_http_error(self, webhook_channel, sample_payload):
        """Test webhook with HTTP error response"""
        config = {
            "url": "https://hooks.example.com/webhook",
            "method": "POST"
        }

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await webhook_channel.send(config, sample_payload)

    @pytest.mark.asyncio
    async def test_test_connection_success(self, webhook_channel):
        """Test connection test success"""
        config = {"url": "https://hooks.example.com/webhook"}

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.options = AsyncMock(
                return_value=mock_response
            )

            result = await webhook_channel.test_connection(config)
            assert result is True
