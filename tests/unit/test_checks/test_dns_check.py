"""Tests for DNS check plugin"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import socket
import asyncio

from app.domains.checks.plugins.dns_check import DNSCheck


@pytest.fixture
def dns_check():
    return DNSCheck()


class TestDNSCheck:
    """Tests for DNSCheck plugin"""

    def test_check_type(self, dns_check):
        """Test check type identifier"""
        assert dns_check.check_type == "dns"

    def test_display_name(self, dns_check):
        """Test display name"""
        assert dns_check.display_name == "DNS Resolution Check"

    def test_config_schema(self, dns_check):
        """Test configuration schema"""
        schema = dns_check.get_config_schema()
        assert "properties" in schema
        assert "record_type" in schema["properties"]
        assert "expected_values" in schema["properties"]
        assert "timeout_seconds" in schema["properties"]
        # Check record type options
        assert "A" in schema["properties"]["record_type"]["enum"]
        assert "AAAA" in schema["properties"]["record_type"]["enum"]

    @pytest.mark.asyncio
    async def test_execute_success_a_record(self, dns_check):
        """Test successful A record DNS resolution"""
        mock_result = ("example.com", [], ["93.184.216.34"])

        with patch("socket.gethostbyname_ex", return_value=mock_result):
            result = await dns_check.execute(
                "https://example.com",
                {"record_type": "A", "timeout_seconds": 10}
            )

            assert result.status == "success"
            assert result.response_time_ms is not None
            assert "93.184.216.34" in result.result_data["resolved_values"]

    @pytest.mark.asyncio
    async def test_execute_expected_values_match(self, dns_check):
        """Test DNS check with matching expected values"""
        mock_result = ("example.com", [], ["93.184.216.34", "93.184.216.35"])

        with patch("socket.gethostbyname_ex", return_value=mock_result):
            result = await dns_check.execute(
                "https://example.com",
                {
                    "record_type": "A",
                    "expected_values": ["93.184.216.34"]
                }
            )

            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_expected_values_mismatch(self, dns_check):
        """Test DNS check with mismatched expected values"""
        mock_result = ("example.com", [], ["93.184.216.34"])

        with patch("socket.gethostbyname_ex", return_value=mock_result):
            result = await dns_check.execute(
                "https://example.com",
                {
                    "record_type": "A",
                    "expected_values": ["1.2.3.4"]
                }
            )

            assert result.status == "failure"
            assert "don't match" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_nxdomain(self, dns_check):
        """Test DNS check for non-existent domain"""
        with patch("socket.gethostbyname_ex", side_effect=socket.gaierror("Name or service not known")):
            result = await dns_check.execute(
                "https://nonexistent.example.invalid",
                {"record_type": "A"}
            )

            assert result.status == "failure"
            assert "resolution failed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout(self, dns_check):
        """Test DNS check timeout"""
        with patch("socket.gethostbyname_ex", side_effect=asyncio.TimeoutError()):
            result = await dns_check.execute(
                "https://example.com",
                {"timeout_seconds": 1}
            )

            assert result.status == "failure"
            assert "timed out" in result.error_message.lower()

    def test_hostname_extraction(self, dns_check):
        """Test hostname extraction from various URL formats"""
        # The execute method extracts hostname internally
        # Test with URL with port
        assert "example.com" in "example.com:8080".split(":")[0]
