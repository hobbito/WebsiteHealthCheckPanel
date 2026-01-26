"""Redirect chain check plugin"""
import time
from typing import Any, Dict, List
from urllib.parse import urlparse
import httpx

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class RedirectCheck(BaseCheck):
    """Check that monitors redirect chains and verifies final destinations"""

    @property
    def check_type(self) -> str:
        return "redirect"

    @property
    def display_name(self) -> str:
        return "Redirect Chain Check"

    @property
    def description(self) -> str:
        return "Monitors HTTP redirect chains, verifies final destination, and detects redirect loops"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        expected_final_url = config.get("expected_final_url")
        max_redirects = config.get("max_redirects", 10)
        require_https = config.get("require_https", False)
        timeout_seconds = config.get("timeout_seconds", 10)
        warn_on_redirect_count = config.get("warn_on_redirect_count", 3)

        start_time = time.time()
        redirect_chain = []
        current_url = site_url

        try:
            async with httpx.AsyncClient(follow_redirects=False) as client:
                for i in range(max_redirects + 1):
                    response = await client.get(current_url, timeout=timeout_seconds)

                    redirect_chain.append({
                        "url": current_url,
                        "status_code": response.status_code,
                        "headers": {
                            "location": response.headers.get("location"),
                            "content-type": response.headers.get("content-type")
                        }
                    })

                    # Check if this is a redirect
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location:
                            response_time_ms = int((time.time() - start_time) * 1000)
                            return CheckResult(
                                status="failure",
                                response_time_ms=response_time_ms,
                                error_message=f"Redirect response ({response.status_code}) missing Location header",
                                result_data={
                                    "redirect_chain": redirect_chain,
                                    "failed_at": current_url
                                }
                            )

                        # Handle relative URLs
                        if location.startswith("/"):
                            parsed = urlparse(current_url)
                            location = f"{parsed.scheme}://{parsed.netloc}{location}"
                        elif not location.startswith(("http://", "https://")):
                            parsed = urlparse(current_url)
                            base_path = "/".join(parsed.path.split("/")[:-1])
                            location = f"{parsed.scheme}://{parsed.netloc}{base_path}/{location}"

                        # Detect redirect loops
                        visited_urls = [r["url"] for r in redirect_chain]
                        if location in visited_urls:
                            response_time_ms = int((time.time() - start_time) * 1000)
                            return CheckResult(
                                status="failure",
                                response_time_ms=response_time_ms,
                                error_message=f"Redirect loop detected: {location}",
                                result_data={
                                    "redirect_chain": redirect_chain,
                                    "loop_url": location
                                }
                            )

                        current_url = location
                    else:
                        # Not a redirect - this is our final destination
                        break
                else:
                    # Exceeded max redirects
                    response_time_ms = int((time.time() - start_time) * 1000)
                    return CheckResult(
                        status="failure",
                        response_time_ms=response_time_ms,
                        error_message=f"Exceeded maximum redirects ({max_redirects})",
                        result_data={
                            "redirect_chain": redirect_chain,
                            "max_redirects": max_redirects
                        }
                    )

            response_time_ms = int((time.time() - start_time) * 1000)
            final_url = redirect_chain[-1]["url"]
            final_status = redirect_chain[-1]["status_code"]
            redirect_count = len(redirect_chain) - 1  # Subtract 1 for the final destination

            result_data = {
                "original_url": site_url,
                "final_url": final_url,
                "final_status_code": final_status,
                "redirect_count": redirect_count,
                "redirect_chain": redirect_chain
            }

            # Check if final URL matches expected
            if expected_final_url:
                # Normalize URLs for comparison
                expected_normalized = expected_final_url.rstrip("/")
                final_normalized = final_url.rstrip("/")

                if expected_normalized.lower() != final_normalized.lower():
                    return CheckResult(
                        status="failure",
                        response_time_ms=response_time_ms,
                        error_message=f"Final URL '{final_url}' does not match expected '{expected_final_url}'",
                        result_data=result_data
                    )

            # Check HTTPS requirement
            if require_https:
                parsed_final = urlparse(final_url)
                if parsed_final.scheme != "https":
                    return CheckResult(
                        status="failure",
                        response_time_ms=response_time_ms,
                        error_message=f"Final URL does not use HTTPS: {final_url}",
                        result_data=result_data
                    )

            # Check final status code
            if final_status >= 400:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Final destination returned error status: {final_status}",
                    result_data=result_data
                )

            # Check redirect count warning
            if redirect_count >= warn_on_redirect_count:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message=f"High number of redirects: {redirect_count}",
                    result_data=result_data
                )

            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data=result_data
            )

        except httpx.TooManyRedirects:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message="Too many redirects",
                result_data={
                    "redirect_chain": redirect_chain,
                    "max_redirects": max_redirects
                }
            )

        except httpx.TimeoutException:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Request timed out after {timeout_seconds}s",
                result_data={
                    "timeout": timeout_seconds,
                    "redirect_chain": redirect_chain
                }
            )

        except httpx.ConnectError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"Connection failed: {str(e)}",
                result_data={
                    "error_type": "ConnectError",
                    "redirect_chain": redirect_chain
                }
            )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=str(e),
                result_data={
                    "error_type": type(e).__name__,
                    "redirect_chain": redirect_chain
                }
            )

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expected_final_url": {
                    "type": "string",
                    "default": None,
                    "description": "Expected final destination URL after all redirects (optional)"
                },
                "max_redirects": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Maximum number of redirects to follow"
                },
                "require_https": {
                    "type": "boolean",
                    "default": False,
                    "description": "Require final destination to use HTTPS"
                },
                "warn_on_redirect_count": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Number of redirects that triggers a warning"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 60,
                    "description": "Timeout per request in seconds"
                }
            }
        }
