import time
from typing import Any, Dict
import httpx
from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class HTTPCheck(BaseCheck):
    @property
    def check_type(self) -> str:
        return "http"

    @property
    def display_name(self) -> str:
        return "HTTP Status Check"

    @property
    def description(self) -> str:
        return "Verifies HTTP status code and measures response time"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        expected_status = config.get("expected_status_code", 200)
        timeout_seconds = config.get("timeout_seconds", 10)
        follow_redirects = config.get("follow_redirects", True)

        start_time = time.time()

        try:
            async with httpx.AsyncClient(follow_redirects=follow_redirects) as client:
                response = await client.get(site_url, timeout=timeout_seconds)

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code == expected_status:
                return CheckResult(
                    status="success",
                    response_time_ms=response_time_ms,
                    error_message=None,
                    result_data={
                        "status_code": response.status_code,
                        "content_length": len(response.content),
                        "headers": dict(response.headers)
                    }
                )
            else:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Expected status {expected_status}, got {response.status_code}",
                    result_data={
                        "status_code": response.status_code,
                        "expected_status": expected_status
                    }
                )

        except httpx.TimeoutException:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Request timed out after {timeout_seconds}s",
                result_data={"timeout": timeout_seconds}
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
                "expected_status_code": {
                    "type": "integer",
                    "default": 200,
                    "description": "Expected HTTP status code"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 60,
                    "description": "Request timeout in seconds"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Follow HTTP redirects"
                }
            }
        }
