"""Pytest configuration and shared fixtures"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


# ============ Check Plugin Fixtures ============

@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response"""
    def _create_response(status_code=200, content=b"OK", headers=None):
        response = MagicMock()
        response.status_code = status_code
        response.content = content
        response.text = content.decode() if isinstance(content, bytes) else content
        response.headers = headers or {"content-type": "text/html"}
        response.raise_for_status = MagicMock()
        return response
    return _create_response


@pytest.fixture
def sample_site_url():
    """Sample site URL for testing"""
    return "https://example.com"


# ============ Notification Fixtures ============

@pytest.fixture
def sample_notification_payload():
    """Sample notification payload for testing"""
    from app.domains.notifications.channels.base import NotificationPayload
    return NotificationPayload(
        trigger="check_failure",
        site_name="Test Site",
        site_url="https://example.com",
        check_name="HTTP Check",
        check_type="http",
        status="failure",
        error_message="Connection refused",
        response_time_ms=None,
        checked_at=datetime.now(timezone.utc),
        incident_id=None
    )


@pytest.fixture
def email_channel_config():
    """Sample email channel configuration"""
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "user@example.com",
        "smtp_password": "password",
        "from_address": "alerts@example.com",
        "to_addresses": ["admin@example.com"],
        "use_tls": True
    }


@pytest.fixture
def webhook_channel_config():
    """Sample webhook channel configuration"""
    return {
        "url": "https://hooks.example.com/webhook",
        "method": "POST",
        "headers": {"X-Custom-Header": "value"},
        "auth_type": "none"
    }


# ============ Async Test Utilities ============

@pytest.fixture
def event_loop_policy():
    """Use default event loop policy"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
