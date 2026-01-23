import httpx
import time
from typing import Dict, Any
from urllib.parse import urlparse

from app.checks.base import BaseCheck, CheckResult
from app.checks.registry import CheckRegistry
from app.models.check import CheckStatus


@CheckRegistry.register
class HTTPCheck(BaseCheck):
    """
    HTTP health check - verifies status code and measures response time.

    Configuration schema:
    {
        "expected_status_code": 200,  # Optional, defaults to 200
        "timeout_seconds": 10,         # Optional, defaults to 10
        "follow_redirects": true,      # Optional, defaults to true
        "verify_ssl": true,            # Optional, defaults to true
        "max_response_time_ms": 3000   # Optional, warn if exceeded
    }
    """

    @classmethod
    def get_display_name(cls) -> str:
        return "HTTP Status Check"

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expected_status_code": {
                    "type": "integer",
                    "default": 200,
                    "description": "Expected HTTP status code (default: 200)"
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
                },
                "verify_ssl": {
                    "type": "boolean",
                    "default": True,
                    "description": "Verify SSL certificates"
                },
                "max_response_time_ms": {
                    "type": "integer",
                    "default": 3000,
                    "description": "Maximum acceptable response time in ms (triggers warning if exceeded)"
                }
            },
            "additionalProperties": False
        }

    async def execute(self, url: str, config: Dict[str, Any]) -> CheckResult:
        """Execute HTTP check"""
        # Parse configuration with defaults
        expected_status = config.get("expected_status_code", 200)
        timeout = config.get("timeout_seconds", 10)
        follow_redirects = config.get("follow_redirects", True)
        verify_ssl = config.get("verify_ssl", True)
        max_response_time = config.get("max_response_time_ms", 3000)

        # Ensure URL has scheme
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = f"https://{url}"

        start_time = time.time()

        try:
            async with httpx.AsyncClient(
                follow_redirects=follow_redirects,
                verify=verify_ssl,
                timeout=timeout
            ) as client:
                response = await client.get(url)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Check status code
            if response.status_code == expected_status:
                # Check if response time exceeds threshold
                if response_time_ms > max_response_time:
                    return CheckResult(
                        status=CheckStatus.WARNING,
                        response_time_ms=response_time_ms,
                        error_message=f"Response time ({response_time_ms:.0f}ms) exceeds threshold ({max_response_time}ms)",
                        result_data={
                            "status_code": response.status_code,
                            "response_time_ms": response_time_ms,
                            "url": str(response.url),
                        }
                    )

                return CheckResult(
                    status=CheckStatus.SUCCESS,
                    response_time_ms=response_time_ms,
                    result_data={
                        "status_code": response.status_code,
                        "response_time_ms": response_time_ms,
                        "url": str(response.url),
                    }
                )
            else:
                return CheckResult(
                    status=CheckStatus.FAILURE,
                    response_time_ms=response_time_ms,
                    error_message=f"Expected status code {expected_status}, got {response.status_code}",
                    result_data={
                        "status_code": response.status_code,
                        "expected_status_code": expected_status,
                        "response_time_ms": response_time_ms,
                        "url": str(response.url),
                    }
                )

        except httpx.TimeoutException:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"Request timed out after {timeout} seconds",
                result_data={"timeout_seconds": timeout}
            )

        except httpx.ConnectError as e:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"Connection error: {str(e)}",
                result_data={"error_type": "connection_error"}
            )

        except httpx.HTTPStatusError as e:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"HTTP error: {str(e)}",
                result_data={"error_type": "http_error"}
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"Unexpected error: {str(e)}",
                result_data={"error_type": "unexpected_error"}
            )
