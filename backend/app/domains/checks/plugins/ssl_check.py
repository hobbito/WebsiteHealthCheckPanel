"""SSL certificate check plugin"""
import ssl
import socket
import time
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import urlparse

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class SSLCheck(BaseCheck):
    """Check that verifies SSL certificate validity and expiration"""

    @property
    def check_type(self) -> str:
        return "ssl"

    @property
    def display_name(self) -> str:
        return "SSL Certificate Check"

    @property
    def description(self) -> str:
        return "Verifies SSL certificate validity and warns before expiration"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        warning_days = config.get("warning_days_before_expiry", 30)
        timeout_seconds = config.get("timeout_seconds", 10)

        # Extract hostname and port
        parsed = urlparse(site_url)
        hostname = parsed.netloc or parsed.path
        port = parsed.port or 443

        # Remove port from hostname if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            # Get certificate info in executor (blocking operation)
            cert_info = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._get_certificate_info(hostname, port, timeout_seconds)
                ),
                timeout=timeout_seconds + 5
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Parse dates
            not_after = datetime.strptime(cert_info["not_after"], "%b %d %H:%M:%S %Y %Z")
            not_before = datetime.strptime(cert_info["not_before"], "%b %d %H:%M:%S %Y %Z")

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            days_until_expiry = (not_after - now).days

            result_data = {
                "hostname": hostname,
                "issuer": cert_info["issuer"],
                "subject": cert_info["subject"],
                "not_before": not_before.isoformat(),
                "not_after": not_after.isoformat(),
                "days_until_expiry": days_until_expiry,
                "serial_number": cert_info.get("serial_number", "Unknown")
            }

            # Check expiration
            if days_until_expiry <= 0:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"SSL certificate has expired ({abs(days_until_expiry)} days ago)",
                    result_data=result_data
                )
            elif days_until_expiry <= warning_days:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message=f"SSL certificate expires in {days_until_expiry} days",
                    result_data=result_data
                )
            else:
                return CheckResult(
                    status="success",
                    response_time_ms=response_time_ms,
                    result_data=result_data
                )

        except ssl.SSLCertVerificationError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"SSL certificate verification failed: {str(e)}",
                result_data={
                    "hostname": hostname,
                    "error_type": "SSLVerificationError"
                }
            )

        except socket.timeout:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Connection timed out after {timeout_seconds}s",
                result_data={
                    "hostname": hostname,
                    "timeout": timeout_seconds
                }
            )

        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Operation timed out after {timeout_seconds}s",
                result_data={
                    "hostname": hostname,
                    "timeout": timeout_seconds
                }
            )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=str(e),
                result_data={
                    "hostname": hostname,
                    "error_type": type(e).__name__
                }
            )

    def _get_certificate_info(self, hostname: str, port: int, timeout: int) -> Dict[str, Any]:
        """Get SSL certificate information (blocking)"""
        context = ssl.create_default_context()

        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        # Extract subject info
        subject = {}
        for item in cert.get("subject", []):
            for key, value in item:
                subject[key] = value

        # Extract issuer info
        issuer = {}
        for item in cert.get("issuer", []):
            for key, value in item:
                issuer[key] = value

        return {
            "subject": subject.get("commonName", "Unknown"),
            "issuer": issuer.get("organizationName", issuer.get("commonName", "Unknown")),
            "not_before": cert.get("notBefore", ""),
            "not_after": cert.get("notAfter", ""),
            "serial_number": cert.get("serialNumber", "Unknown")
        }

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warning_days_before_expiry": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 365,
                    "description": "Days before expiry to trigger warning"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 60,
                    "description": "Connection timeout in seconds"
                }
            }
        }
