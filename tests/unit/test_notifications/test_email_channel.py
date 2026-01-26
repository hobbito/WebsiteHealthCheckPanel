"""Tests for email notification channel"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.domains.notifications.channels.email import EmailChannel
from app.domains.notifications.channels.base import NotificationPayload


@pytest.fixture
def email_channel():
    return EmailChannel()


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


@pytest.fixture
def email_config():
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "user@example.com",
        "smtp_password": "password",
        "from_address": "alerts@example.com",
        "to_addresses": ["admin@example.com"],
        "use_tls": True
    }


class TestEmailChannel:
    """Tests for EmailChannel"""

    def test_channel_type(self, email_channel):
        """Test channel type identifier"""
        assert email_channel.channel_type == "email"

    def test_display_name(self, email_channel):
        """Test display name"""
        assert "Email" in email_channel.display_name
        assert "SMTP" in email_channel.display_name

    def test_config_schema(self, email_channel):
        """Test configuration schema"""
        schema = email_channel.get_config_schema()
        assert "properties" in schema
        assert "smtp_host" in schema["properties"]
        assert "smtp_port" in schema["properties"]
        assert "from_address" in schema["properties"]
        assert "to_addresses" in schema["properties"]
        assert "smtp_host" in schema.get("required", [])
        assert "from_address" in schema.get("required", [])
        assert "to_addresses" in schema.get("required", [])

    @pytest.mark.asyncio
    async def test_send_success(self, email_channel, sample_payload, email_config):
        """Test successful email delivery"""
        with patch("aiosmtplib.send") as mock_send:
            mock_send.return_value = {}

            result = await email_channel.send(email_config, sample_payload)

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_calls_smtp_with_correct_params(self, email_channel, sample_payload, email_config):
        """Test that send calls SMTP with correct parameters"""
        with patch("aiosmtplib.send") as mock_send:
            mock_send.return_value = {}

            await email_channel.send(email_config, sample_payload)

            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["hostname"] == "smtp.example.com"
            assert call_kwargs["port"] == 587
            assert call_kwargs["username"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_send_smtp_error(self, email_channel, sample_payload, email_config):
        """Test email send with SMTP error"""
        with patch("aiosmtplib.send") as mock_send:
            mock_send.side_effect = Exception("SMTP connection failed")

            with pytest.raises(Exception) as exc_info:
                await email_channel.send(email_config, sample_payload)

            assert "SMTP connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_test_connection_success(self, email_channel, email_config):
        """Test connection test success"""
        mock_smtp = MagicMock()
        mock_smtp.connect = AsyncMock()
        mock_smtp.starttls = AsyncMock()
        mock_smtp.login = AsyncMock()
        mock_smtp.quit = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await email_channel.test_connection(email_config)
            assert result is True
            mock_smtp.connect.assert_called_once()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_no_tls(self, email_channel):
        """Test connection test without TLS"""
        config = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 25,
            "use_tls": False
        }

        mock_smtp = MagicMock()
        mock_smtp.connect = AsyncMock()
        mock_smtp.starttls = AsyncMock()
        mock_smtp.quit = AsyncMock()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await email_channel.test_connection(config)
            assert result is True
            mock_smtp.starttls.assert_not_called()

    def test_build_subject_failure(self, email_channel, sample_payload):
        """Test subject line building for failure"""
        subject = email_channel._build_subject(sample_payload)
        assert "ALERT" in subject
        assert "Test Site" in subject
        assert "HTTP Check" in subject

    def test_build_subject_recovery(self, email_channel):
        """Test subject line building for recovery"""
        payload = NotificationPayload(
            trigger="check_recovery",
            site_name="Test Site",
            site_url="https://example.com",
            check_name="HTTP Check",
            check_type="http",
            status="success",
            error_message=None,
            response_time_ms=150,
            checked_at=datetime.now(timezone.utc)
        )
        subject = email_channel._build_subject(payload)
        assert "RECOVERED" in subject

    def test_build_html_body(self, email_channel, sample_payload):
        """Test HTML body building"""
        html = email_channel._build_html_body(sample_payload)
        assert "Test Site" in html
        assert "example.com" in html
        assert "HTTP Check" in html
        assert "Connection refused" in html

    def test_build_text_body(self, email_channel, sample_payload):
        """Test plain text body building"""
        text = email_channel._build_text_body(sample_payload)
        assert "Test Site" in text
        assert "example.com" in text
        assert "Connection refused" in text
