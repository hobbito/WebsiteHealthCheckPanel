"""TCP port check plugin"""
import time
import socket
import asyncio
from typing import Any, Dict, List
from urllib.parse import urlparse

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class PortCheck(BaseCheck):
    """Check that verifies TCP port accessibility"""

    @property
    def check_type(self) -> str:
        return "port"

    @property
    def display_name(self) -> str:
        return "TCP Port Check"

    @property
    def description(self) -> str:
        return "Verifies that specific TCP ports are open and accepting connections"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        ports = config.get("ports", [80, 443])
        timeout_seconds = config.get("timeout_seconds", 5)

        # Extract hostname from URL
        parsed = urlparse(site_url)
        hostname = parsed.netloc or parsed.path
        # Remove port if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            results = {}
            open_ports = []
            closed_ports = []

            for port in ports:
                try:
                    port_start = time.time()

                    # Try to connect to the port
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda p=port: self._check_port(hostname, p, timeout_seconds)
                        ),
                        timeout=timeout_seconds + 1
                    )

                    port_time = int((time.time() - port_start) * 1000)
                    results[port] = {
                        "status": "open",
                        "response_time_ms": port_time
                    }
                    open_ports.append(port)

                except (socket.timeout, socket.error, asyncio.TimeoutError, ConnectionRefusedError):
                    port_time = int((time.time() - port_start) * 1000)
                    results[port] = {
                        "status": "closed",
                        "response_time_ms": port_time
                    }
                    closed_ports.append(port)

            response_time_ms = int((time.time() - start_time) * 1000)

            # Determine overall status
            if closed_ports:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Closed ports: {', '.join(map(str, closed_ports))}",
                    result_data={
                        "hostname": hostname,
                        "open_ports": open_ports,
                        "closed_ports": closed_ports,
                        "port_details": results
                    }
                )

            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data={
                    "hostname": hostname,
                    "open_ports": open_ports,
                    "closed_ports": closed_ports,
                    "port_details": results
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

    def _check_port(self, hostname: str, port: int, timeout: int) -> bool:
        """Check if a TCP port is open (blocking)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((hostname, port))
            return result == 0
        finally:
            sock.close()

        if result != 0:
            raise ConnectionRefusedError(f"Port {port} is closed")

        return True

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ports": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 65535
                    },
                    "default": [80, 443],
                    "description": "List of TCP ports to check"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 30,
                    "description": "Connection timeout per port in seconds"
                }
            }
        }
