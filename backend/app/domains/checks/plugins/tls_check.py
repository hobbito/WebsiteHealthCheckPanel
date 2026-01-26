"""TLS version check plugin"""
import ssl
import socket
import time
import asyncio
from typing import Any, Dict, List
from urllib.parse import urlparse

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class TLSCheck(BaseCheck):
    """Check that verifies TLS version and cipher suite configuration"""

    # TLS versions in order of security (higher is better)
    TLS_VERSIONS = {
        "TLSv1": ssl.TLSVersion.TLSv1,
        "TLSv1.1": ssl.TLSVersion.TLSv1_1,
        "TLSv1.2": ssl.TLSVersion.TLSv1_2,
        "TLSv1.3": ssl.TLSVersion.TLSv1_3,
    }

    TLS_VERSION_ORDER = ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"]

    # Weak cipher patterns to flag
    WEAK_CIPHER_PATTERNS = [
        "NULL", "EXPORT", "DES", "RC4", "MD5", "anon", "ADH", "AECDH"
    ]

    @property
    def check_type(self) -> str:
        return "tls"

    @property
    def display_name(self) -> str:
        return "TLS Version Check"

    @property
    def description(self) -> str:
        return "Verifies TLS version meets minimum requirements and checks for weak ciphers"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        minimum_tls_version = config.get("minimum_tls_version", "TLSv1.2")
        check_weak_ciphers = config.get("check_weak_ciphers", True)
        timeout_seconds = config.get("timeout_seconds", 10)

        # Extract hostname and port
        parsed = urlparse(site_url)
        hostname = parsed.netloc or parsed.path
        port = parsed.port or 443

        if ":" in hostname:
            hostname = hostname.split(":")[0]

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            tls_info = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._get_tls_info(hostname, port, timeout_seconds)
                ),
                timeout=timeout_seconds + 5
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            actual_version = tls_info["tls_version"]
            cipher_name = tls_info["cipher_name"]

            result_data = {
                "hostname": hostname,
                "port": port,
                "tls_version": actual_version,
                "cipher_name": cipher_name,
                "cipher_bits": tls_info["cipher_bits"],
                "minimum_required": minimum_tls_version
            }

            # Check TLS version
            if actual_version not in self.TLS_VERSION_ORDER:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Unknown TLS version: {actual_version}",
                    result_data=result_data
                )

            actual_index = self.TLS_VERSION_ORDER.index(actual_version)
            minimum_index = self.TLS_VERSION_ORDER.index(minimum_tls_version)

            if actual_index < minimum_index:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"TLS version {actual_version} is below minimum required {minimum_tls_version}",
                    result_data=result_data
                )

            # Check for weak ciphers
            weak_cipher_found = False
            if check_weak_ciphers:
                cipher_upper = cipher_name.upper()
                for weak_pattern in self.WEAK_CIPHER_PATTERNS:
                    if weak_pattern in cipher_upper:
                        weak_cipher_found = True
                        result_data["weak_cipher_warning"] = f"Weak cipher pattern detected: {weak_pattern}"
                        break

            if weak_cipher_found:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message=f"Weak cipher detected: {cipher_name}",
                    result_data=result_data
                )

            # Check for deprecated TLS versions (warning level)
            if actual_version in ["TLSv1", "TLSv1.1"]:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message=f"TLS version {actual_version} is deprecated",
                    result_data=result_data
                )

            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data=result_data
            )

        except ssl.SSLError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"SSL/TLS error: {str(e)}",
                result_data={
                    "hostname": hostname,
                    "error_type": "SSLError"
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

        except ConnectionRefusedError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Connection refused on port {port}",
                result_data={
                    "hostname": hostname,
                    "port": port
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

    def _get_tls_info(self, hostname: str, port: int, timeout: int) -> Dict[str, Any]:
        """Get TLS connection information (blocking)"""
        context = ssl.create_default_context()

        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get TLS version
                tls_version = ssock.version()

                # Get cipher information
                cipher = ssock.cipher()
                cipher_name = cipher[0] if cipher else "Unknown"
                cipher_bits = cipher[2] if cipher and len(cipher) > 2 else 0

                return {
                    "tls_version": tls_version,
                    "cipher_name": cipher_name,
                    "cipher_bits": cipher_bits
                }

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "minimum_tls_version": {
                    "type": "string",
                    "enum": ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"],
                    "default": "TLSv1.2",
                    "description": "Minimum acceptable TLS version"
                },
                "check_weak_ciphers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Check for weak cipher suites (NULL, EXPORT, DES, RC4, etc.)"
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
