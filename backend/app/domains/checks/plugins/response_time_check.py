"""Response time check plugin"""
import time
from typing import Any, Dict
import httpx

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class ResponseTimeCheck(BaseCheck):
    """Check that monitors response time with configurable thresholds"""

    @property
    def check_type(self) -> str:
        return "response_time"

    @property
    def display_name(self) -> str:
        return "Response Time Check"

    @property
    def description(self) -> str:
        return "Monitors response time with configurable warning and failure thresholds"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        warning_threshold_ms = config.get("warning_threshold_ms", 1000)
        failure_threshold_ms = config.get("failure_threshold_ms", 5000)
        timeout_seconds = config.get("timeout_seconds", 30)
        method = config.get("method", "GET").upper()
        follow_redirects = config.get("follow_redirects", True)

        start_time = time.time()

        try:
            async with httpx.AsyncClient(follow_redirects=follow_redirects) as client:
                if method == "HEAD":
                    response = await client.head(site_url, timeout=timeout_seconds)
                else:
                    response = await client.get(site_url, timeout=timeout_seconds)

            response_time_ms = int((time.time() - start_time) * 1000)

            # Calculate time to first byte (TTFB) approximation
            result_data = {
                "response_time_ms": response_time_ms,
                "status_code": response.status_code,
                "warning_threshold_ms": warning_threshold_ms,
                "failure_threshold_ms": failure_threshold_ms,
                "content_length": len(response.content) if method != "HEAD" else None,
                "method": method
            }

            # Check against thresholds
            if response_time_ms >= failure_threshold_ms:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Response time {response_time_ms}ms exceeds failure threshold {failure_threshold_ms}ms",
                    result_data=result_data
                )
            elif response_time_ms >= warning_threshold_ms:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message=f"Response time {response_time_ms}ms exceeds warning threshold {warning_threshold_ms}ms",
                    result_data=result_data
                )
            else:
                return CheckResult(
                    status="success",
                    response_time_ms=response_time_ms,
                    result_data=result_data
                )

        except httpx.TimeoutException:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Request timed out after {timeout_seconds}s",
                result_data={
                    "timeout": timeout_seconds,
                    "failure_threshold_ms": failure_threshold_ms
                }
            )

        except httpx.ConnectError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Connection failed: {str(e)}",
                result_data={"error_type": "ConnectError"}
            )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=str(e),
                result_data={"error_type": type(e).__name__}
            )

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warning_threshold_ms": {
                    "type": "integer",
                    "default": 1000,
                    "minimum": 100,
                    "maximum": 30000,
                    "description": "Response time threshold for warning status (milliseconds)"
                },
                "failure_threshold_ms": {
                    "type": "integer",
                    "default": 5000,
                    "minimum": 500,
                    "maximum": 60000,
                    "description": "Response time threshold for failure status (milliseconds)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 120,
                    "description": "Maximum time to wait for response"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "HEAD"],
                    "default": "GET",
                    "description": "HTTP method to use (HEAD is faster but returns no body)"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Follow HTTP redirects"
                }
            }
        }
