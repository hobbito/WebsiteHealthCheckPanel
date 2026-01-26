"""DNS resolution check plugin"""
import time
import asyncio
import socket
from typing import Any, Dict, List
from urllib.parse import urlparse

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class DNSCheck(BaseCheck):
    """Check that verifies DNS resolution for a domain"""

    @property
    def check_type(self) -> str:
        return "dns"

    @property
    def display_name(self) -> str:
        return "DNS Resolution Check"

    @property
    def description(self) -> str:
        return "Verifies DNS records resolve correctly and optionally checks expected values"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        record_type = config.get("record_type", "A")
        expected_values = config.get("expected_values", [])
        timeout_seconds = config.get("timeout_seconds", 10)

        # Extract hostname from URL
        parsed = urlparse(site_url)
        hostname = parsed.netloc or parsed.path
        # Remove port if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        start_time = time.time()

        try:
            # Use asyncio's DNS resolution
            loop = asyncio.get_event_loop()

            if record_type == "A":
                # IPv4 address lookup
                resolved = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: socket.gethostbyname_ex(hostname)
                    ),
                    timeout=timeout_seconds
                )
                resolved_values = resolved[2]  # List of IP addresses

            elif record_type == "AAAA":
                # IPv6 address lookup
                resolved = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: socket.getaddrinfo(hostname, None, socket.AF_INET6)
                    ),
                    timeout=timeout_seconds
                )
                resolved_values = list(set(addr[4][0] for addr in resolved))

            elif record_type == "CNAME":
                # CNAME lookup (returns canonical name)
                resolved = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: socket.gethostbyname_ex(hostname)
                    ),
                    timeout=timeout_seconds
                )
                resolved_values = [resolved[0]] if resolved[0] != hostname else []

            elif record_type == "MX":
                # MX record lookup using DNS library if available, otherwise basic check
                try:
                    import dns.resolver
                    answers = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: dns.resolver.resolve(hostname, "MX")
                        ),
                        timeout=timeout_seconds
                    )
                    resolved_values = [str(rdata.exchange).rstrip('.') for rdata in answers]
                except ImportError:
                    # Fallback: just verify the domain exists
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: socket.gethostbyname(hostname)
                        ),
                        timeout=timeout_seconds
                    )
                    resolved_values = ["MX lookup requires dnspython"]

            else:
                # Default to A record
                resolved = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: socket.gethostbyname_ex(hostname)
                    ),
                    timeout=timeout_seconds
                )
                resolved_values = resolved[2]

            response_time_ms = int((time.time() - start_time) * 1000)

            # Check if expected values match (if specified)
            if expected_values:
                matches = all(ev in resolved_values for ev in expected_values)
                if not matches:
                    return CheckResult(
                        status="failure",
                        response_time_ms=response_time_ms,
                        error_message=f"DNS records don't match expected values",
                        result_data={
                            "hostname": hostname,
                            "record_type": record_type,
                            "resolved": resolved_values,
                            "expected": expected_values
                        }
                    )

            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data={
                    "hostname": hostname,
                    "record_type": record_type,
                    "resolved_values": resolved_values
                }
            )

        except socket.gaierror as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"DNS resolution failed: {str(e)}",
                result_data={
                    "hostname": hostname,
                    "record_type": record_type,
                    "error_type": "gaierror"
                }
            )

        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"DNS query timed out after {timeout_seconds}s",
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

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "record_type": {
                    "type": "string",
                    "enum": ["A", "AAAA", "CNAME", "MX"],
                    "default": "A",
                    "description": "DNS record type to check"
                },
                "expected_values": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Expected DNS values (leave empty to just verify resolution)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 30,
                    "description": "Query timeout in seconds"
                }
            }
        }
