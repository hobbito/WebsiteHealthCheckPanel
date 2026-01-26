"""Tests for SSL certificate check plugin"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import ssl
import socket
import asyncio

from app.domains.checks.plugins.ssl_check import SSLCheck


@pytest.fixture
def ssl_check():
    return SSLCheck()


@pytest.fixture
def valid_cert():
    """Create a mock valid certificate (expires in 90 days)"""
    future_date = (datetime.now() + timedelta(days=90)).strftime("%b %d %H:%M:%S %Y GMT")
    past_date = (datetime.now() - timedelta(days=30)).strftime("%b %d %H:%M:%S %Y GMT")
    return {
        "notAfter": future_date,
        "notBefore": past_date,
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("organizationName", "Test CA"),),),
        "serialNumber": "123456"
    }


@pytest.fixture
def expiring_cert():
    """Create a mock certificate expiring soon (15 days)"""
    future_date = (datetime.now() + timedelta(days=15)).strftime("%b %d %H:%M:%S %Y GMT")
    past_date = (datetime.now() - timedelta(days=30)).strftime("%b %d %H:%M:%S %Y GMT")
    return {
        "notAfter": future_date,
        "notBefore": past_date,
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("organizationName", "Test CA"),),),
        "serialNumber": "123456"
    }


@pytest.fixture
def expired_cert():
    """Create a mock expired certificate"""
    past_date = (datetime.now() - timedelta(days=30)).strftime("%b %d %H:%M:%S %Y GMT")
    expired_date = (datetime.now() - timedelta(days=5)).strftime("%b %d %H:%M:%S %Y GMT")
    return {
        "notAfter": expired_date,
        "notBefore": past_date,
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("organizationName", "Test CA"),),),
        "serialNumber": "123456"
    }


class TestSSLCheck:
    """Tests for SSLCheck plugin"""

    def test_check_type(self, ssl_check):
        """Test check type identifier"""
        assert ssl_check.check_type == "ssl"

    def test_display_name(self, ssl_check):
        """Test display name"""
        assert ssl_check.display_name == "SSL Certificate Check"

    def test_config_schema(self, ssl_check):
        """Test configuration schema"""
        schema = ssl_check.get_config_schema()
        assert "properties" in schema
        assert "warning_days_before_expiry" in schema["properties"]
        assert "timeout_seconds" in schema["properties"]
        # Check default values
        assert schema["properties"]["warning_days_before_expiry"]["default"] == 30

    @pytest.mark.asyncio
    async def test_execute_valid_cert(self, ssl_check, valid_cert):
        """Test SSL check with valid certificate"""
        with patch.object(ssl_check, "_get_certificate_info", return_value={
            "subject": "example.com",
            "issuer": "Test CA",
            "not_before": valid_cert["notBefore"],
            "not_after": valid_cert["notAfter"],
            "serial_number": "123456"
        }):
            result = await ssl_check.execute(
                "https://example.com",
                {"warning_days_before_expiry": 30}
            )

            assert result.status == "success"
            assert result.result_data["days_until_expiry"] > 30

    @pytest.mark.asyncio
    async def test_execute_expiring_soon(self, ssl_check, expiring_cert):
        """Test SSL check with certificate expiring soon (warning)"""
        with patch.object(ssl_check, "_get_certificate_info", return_value={
            "subject": "example.com",
            "issuer": "Test CA",
            "not_before": expiring_cert["notBefore"],
            "not_after": expiring_cert["notAfter"],
            "serial_number": "123456"
        }):
            result = await ssl_check.execute(
                "https://example.com",
                {"warning_days_before_expiry": 30}
            )

            assert result.status == "warning"
            assert "expires in" in result.error_message.lower()
            assert result.result_data["days_until_expiry"] < 30

    @pytest.mark.asyncio
    async def test_execute_expired(self, ssl_check, expired_cert):
        """Test SSL check with expired certificate"""
        with patch.object(ssl_check, "_get_certificate_info", return_value={
            "subject": "example.com",
            "issuer": "Test CA",
            "not_before": expired_cert["notBefore"],
            "not_after": expired_cert["notAfter"],
            "serial_number": "123456"
        }):
            result = await ssl_check.execute(
                "https://example.com",
                {"warning_days_before_expiry": 30}
            )

            assert result.status == "failure"
            assert "expired" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_ssl_error(self, ssl_check):
        """Test SSL check with SSL verification error"""
        with patch.object(ssl_check, "_get_certificate_info",
                         side_effect=ssl.SSLCertVerificationError("Certificate verify failed")):
            result = await ssl_check.execute(
                "https://example.com",
                {}
            )

            assert result.status == "failure"
            assert "verification failed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout(self, ssl_check):
        """Test SSL check timeout"""
        with patch.object(ssl_check, "_get_certificate_info",
                         side_effect=asyncio.TimeoutError()):
            result = await ssl_check.execute(
                "https://example.com",
                {"timeout_seconds": 5}
            )

            assert result.status == "failure"
            assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_connection_error(self, ssl_check):
        """Test SSL check connection error"""
        with patch.object(ssl_check, "_get_certificate_info",
                         side_effect=socket.timeout("Connection timed out")):
            result = await ssl_check.execute(
                "https://example.com",
                {}
            )

            assert result.status == "failure"
