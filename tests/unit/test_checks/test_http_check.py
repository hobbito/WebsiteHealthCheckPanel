"""Tests for HTTP check plugin"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.domains.checks.plugins.http_check import HTTPCheck


@pytest.fixture
def http_check():
    return HTTPCheck()


class TestHTTPCheck:
    """Tests for HTTPCheck plugin"""

    def test_check_type(self, http_check):
        """Test check type identifier"""
        assert http_check.check_type == "http"

    def test_display_name(self, http_check):
        """Test display name"""
        assert http_check.display_name == "HTTP Status Check"

    def test_description(self, http_check):
        """Test description"""
        assert "HTTP status code" in http_check.description

    def test_config_schema(self, http_check):
        """Test configuration schema"""
        schema = http_check.get_config_schema()
        assert "properties" in schema
        assert "expected_status_code" in schema["properties"]
        assert "timeout_seconds" in schema["properties"]
        assert "follow_redirects" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_success(self, http_check, mock_httpx_response):
        """Test successful HTTP check"""
        mock_response = mock_httpx_response(status_code=200, content=b"OK")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await http_check.execute(
                "https://example.com",
                {"expected_status_code": 200, "timeout_seconds": 10}
            )

            assert result.status == "success"
            assert result.response_time_ms is not None
            assert result.result_data["status_code"] == 200

    @pytest.mark.asyncio
    async def test_execute_wrong_status(self, http_check, mock_httpx_response):
        """Test HTTP check with unexpected status code"""
        mock_response = mock_httpx_response(status_code=404, content=b"Not Found")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await http_check.execute(
                "https://example.com",
                {"expected_status_code": 200}
            )

            assert result.status == "failure"
            assert "Expected status 200" in result.error_message
            assert result.result_data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_execute_timeout(self, http_check):
        """Test HTTP check timeout"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            result = await http_check.execute(
                "https://example.com",
                {"timeout_seconds": 5}
            )

            assert result.status == "failure"
            assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_connection_error(self, http_check):
        """Test HTTP check connection error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            result = await http_check.execute(
                "https://example.com",
                {}
            )

            assert result.status == "failure"
            assert result.error_message is not None
