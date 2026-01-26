"""Ping/ICMP check plugin"""
import time
import asyncio
import platform
import subprocess
from typing import Any, Dict
from urllib.parse import urlparse

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class PingCheck(BaseCheck):
    """Check that verifies host reachability using ping (ICMP)"""

    @property
    def check_type(self) -> str:
        return "ping"

    @property
    def display_name(self) -> str:
        return "Ping (ICMP) Check"

    @property
    def description(self) -> str:
        return "Verifies host reachability and measures round-trip time using ICMP ping"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        count = config.get("count", 3)
        timeout_seconds = config.get("timeout_seconds", 10)
        max_latency_ms = config.get("max_latency_ms", 1000)

        # Extract hostname from URL
        parsed = urlparse(site_url)
        hostname = parsed.netloc or parsed.path
        # Remove port if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            # Build ping command based on OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout_seconds * 1000), hostname]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout_seconds), hostname]

            # Run ping in executor
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds + 5
                    )
                ),
                timeout=timeout_seconds + 10
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Parse ping output
            ping_stats = self._parse_ping_output(result.stdout, platform.system().lower())

            if result.returncode != 0 or ping_stats["packets_received"] == 0:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Host {hostname} is unreachable",
                    result_data={
                        "hostname": hostname,
                        "packets_sent": ping_stats["packets_sent"],
                        "packets_received": ping_stats["packets_received"],
                        "packet_loss": ping_stats["packet_loss"]
                    }
                )

            # Check latency threshold
            avg_latency = ping_stats.get("avg_latency", 0)
            if avg_latency > max_latency_ms:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message=f"High latency: {avg_latency}ms (threshold: {max_latency_ms}ms)",
                    result_data={
                        "hostname": hostname,
                        **ping_stats
                    }
                )

            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data={
                    "hostname": hostname,
                    **ping_stats
                }
            )

        except subprocess.TimeoutExpired:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Ping timed out after {timeout_seconds}s",
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

        except FileNotFoundError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message="Ping command not found on this system",
                result_data={
                    "hostname": hostname,
                    "error_type": "CommandNotFound"
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

    def _parse_ping_output(self, output: str, os_type: str) -> Dict[str, Any]:
        """Parse ping command output to extract statistics"""
        stats = {
            "packets_sent": 0,
            "packets_received": 0,
            "packet_loss": 100.0,
            "min_latency": None,
            "avg_latency": None,
            "max_latency": None
        }

        try:
            lines = output.strip().split("\n")

            for line in lines:
                line_lower = line.lower()

                # Parse packet statistics
                if "packets transmitted" in line_lower or "packets: sent" in line_lower:
                    # Unix: "3 packets transmitted, 3 received, 0% packet loss"
                    # Windows: "Packets: Sent = 3, Received = 3, Lost = 0"
                    parts = line.replace(",", " ").replace("=", " ").split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            if stats["packets_sent"] == 0:
                                stats["packets_sent"] = int(part)
                            elif stats["packets_received"] == 0 and "received" in parts[i-1:i+2] if i > 0 else False:
                                stats["packets_received"] = int(part)
                                break

                # Try simpler parsing
                if "transmitted" in line_lower and "received" in line_lower:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if len(numbers) >= 2:
                        stats["packets_sent"] = int(numbers[0])
                        stats["packets_received"] = int(numbers[1])

                # Parse latency statistics
                # Unix: "rtt min/avg/max/mdev = 10.123/15.456/20.789/3.456 ms"
                # Windows: "Minimum = 10ms, Maximum = 20ms, Average = 15ms"
                if "min/avg/max" in line_lower or "rtt" in line_lower:
                    import re
                    numbers = re.findall(r'[\d.]+', line)
                    if len(numbers) >= 3:
                        stats["min_latency"] = float(numbers[0])
                        stats["avg_latency"] = float(numbers[1])
                        stats["max_latency"] = float(numbers[2])

                if "minimum" in line_lower and "average" in line_lower:
                    import re
                    numbers = re.findall(r'[\d.]+', line)
                    if len(numbers) >= 3:
                        stats["min_latency"] = float(numbers[0])
                        stats["max_latency"] = float(numbers[1])
                        stats["avg_latency"] = float(numbers[2])

            # Calculate packet loss
            if stats["packets_sent"] > 0:
                stats["packet_loss"] = round(
                    (1 - stats["packets_received"] / stats["packets_sent"]) * 100, 2
                )

        except Exception:
            pass  # Return default stats on parse error

        return stats

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Number of ping requests to send"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 30,
                    "description": "Timeout for each ping request"
                },
                "max_latency_ms": {
                    "type": "integer",
                    "default": 1000,
                    "minimum": 1,
                    "description": "Maximum acceptable latency in milliseconds (triggers warning if exceeded)"
                }
            }
        }
