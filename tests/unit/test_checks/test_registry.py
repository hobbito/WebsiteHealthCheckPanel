"""Tests for check plugin registry"""
import pytest
from app.domains.checks.plugins.registry import CheckRegistry, register_check
from app.domains.checks.plugins.base import BaseCheck, CheckResult


class TestCheckRegistry:
    """Tests for CheckRegistry"""

    def test_http_check_is_registered(self):
        """Test that HTTP check is registered"""
        assert CheckRegistry.is_registered("http")

    def test_dns_check_is_registered(self):
        """Test that DNS check is registered"""
        assert CheckRegistry.is_registered("dns")

    def test_ssl_check_is_registered(self):
        """Test that SSL check is registered"""
        assert CheckRegistry.is_registered("ssl")

    def test_ping_check_is_registered(self):
        """Test that Ping check is registered"""
        assert CheckRegistry.is_registered("ping")

    def test_keyword_check_is_registered(self):
        """Test that Keyword check is registered"""
        assert CheckRegistry.is_registered("keyword")

    def test_port_check_is_registered(self):
        """Test that Port check is registered"""
        assert CheckRegistry.is_registered("port")

    def test_get_check_returns_class(self):
        """Test that get_check returns the check class"""
        check_class = CheckRegistry.get_check("http")
        assert issubclass(check_class, BaseCheck)

    def test_get_check_unknown_type(self):
        """Test that get_check raises error for unknown type"""
        with pytest.raises(KeyError) as exc_info:
            CheckRegistry.get_check("unknown_check_type")
        assert "not found" in str(exc_info.value).lower()

    def test_is_registered_false_for_unknown(self):
        """Test that is_registered returns False for unknown type"""
        assert not CheckRegistry.is_registered("unknown_check_type")

    def test_list_checks_returns_all(self):
        """Test that list_checks returns all registered checks"""
        checks = CheckRegistry.list_checks()
        assert len(checks) >= 6  # At least http, dns, ssl, ping, keyword, port

        check_types = [c["type"] for c in checks]
        assert "http" in check_types
        assert "dns" in check_types
        assert "ssl" in check_types

    def test_list_checks_contains_schema(self):
        """Test that list_checks includes config schema"""
        checks = CheckRegistry.list_checks()
        for check in checks:
            assert "type" in check
            assert "display_name" in check
            assert "description" in check
            assert "config_schema" in check

    def test_check_instance_has_required_methods(self):
        """Test that check instances have all required methods"""
        check_class = CheckRegistry.get_check("http")
        check_instance = check_class()

        assert hasattr(check_instance, "check_type")
        assert hasattr(check_instance, "display_name")
        assert hasattr(check_instance, "description")
        assert hasattr(check_instance, "execute")
        assert hasattr(check_instance, "get_config_schema")
