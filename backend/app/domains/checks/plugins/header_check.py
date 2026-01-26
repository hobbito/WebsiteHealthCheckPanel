"""HTTP Header check plugin"""
import time
import re
from typing import Any, Dict, List, Optional
import httpx

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class HeaderCheck(BaseCheck):
    """Check that verifies specific HTTP response headers"""

    @property
    def check_type(self) -> str:
        return "header"

    @property
    def display_name(self) -> str:
        return "HTTP Header Check"

    @property
    def description(self) -> str:
        return "Verifies that specific HTTP headers are present with expected values (useful for security headers)"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        timeout_seconds = config.get("timeout_seconds", 10)
        required_headers = config.get("required_headers", {})
        forbidden_headers = config.get("forbidden_headers", [])
        security_headers_check = config.get("security_headers_check", False)
        method = config.get("method", "HEAD").upper()

        start_time = time.time()

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                if method == "GET":
                    response = await client.get(site_url, timeout=timeout_seconds)
                else:
                    response = await client.head(site_url, timeout=timeout_seconds)

            response_time_ms = int((time.time() - start_time) * 1000)
            response_headers = dict(response.headers)

            errors = []
            warnings = []
            header_results = {}

            # Check required headers
            for header_name, expected_value in required_headers.items():
                header_name_lower = header_name.lower()
                actual_value = None

                # Find header (case-insensitive)
                for key, value in response_headers.items():
                    if key.lower() == header_name_lower:
                        actual_value = value
                        break

                if actual_value is None:
                    errors.append(f"Missing required header: {header_name}")
                    header_results[header_name] = {"status": "missing", "expected": expected_value}
                elif expected_value and expected_value != "*":
                    # Check if expected value matches (supports regex with /pattern/ syntax)
                    if expected_value.startswith("/") and expected_value.endswith("/"):
                        pattern = expected_value[1:-1]
                        if not re.search(pattern, actual_value, re.IGNORECASE):
                            errors.append(f"Header '{header_name}' value mismatch: expected pattern {expected_value}, got '{actual_value}'")
                            header_results[header_name] = {
                                "status": "mismatch",
                                "expected": expected_value,
                                "actual": actual_value
                            }
                        else:
                            header_results[header_name] = {"status": "ok", "value": actual_value}
                    elif actual_value.lower() != expected_value.lower():
                        errors.append(f"Header '{header_name}' value mismatch: expected '{expected_value}', got '{actual_value}'")
                        header_results[header_name] = {
                            "status": "mismatch",
                            "expected": expected_value,
                            "actual": actual_value
                        }
                    else:
                        header_results[header_name] = {"status": "ok", "value": actual_value}
                else:
                    # Just checking existence
                    header_results[header_name] = {"status": "ok", "value": actual_value}

            # Check forbidden headers
            for header_name in forbidden_headers:
                header_name_lower = header_name.lower()
                for key, value in response_headers.items():
                    if key.lower() == header_name_lower:
                        errors.append(f"Forbidden header present: {header_name}")
                        header_results[header_name] = {"status": "forbidden", "value": value}
                        break

            # Security headers check (common security headers)
            if security_headers_check:
                security_headers = {
                    "Strict-Transport-Security": "HSTS - Enforces HTTPS",
                    "X-Content-Type-Options": "Prevents MIME-type sniffing",
                    "X-Frame-Options": "Clickjacking protection",
                    "X-XSS-Protection": "XSS filter (legacy)",
                    "Content-Security-Policy": "CSP - Controls resource loading",
                    "Referrer-Policy": "Controls referrer information"
                }

                missing_security = []
                present_security = []

                for header, description in security_headers.items():
                    header_lower = header.lower()
                    found = False
                    for key in response_headers.keys():
                        if key.lower() == header_lower:
                            found = True
                            present_security.append(header)
                            break
                    if not found:
                        missing_security.append(header)
                        warnings.append(f"Missing security header: {header} ({description})")

                header_results["_security_check"] = {
                    "present": present_security,
                    "missing": missing_security,
                    "score": f"{len(present_security)}/{len(security_headers)}"
                }

            result_data = {
                "status_code": response.status_code,
                "headers_checked": len(required_headers) + len(forbidden_headers),
                "header_results": header_results,
                "total_response_headers": len(response_headers)
            }

            if errors:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message="; ".join(errors),
                    result_data=result_data
                )

            if warnings:
                return CheckResult(
                    status="warning",
                    response_time_ms=response_time_ms,
                    error_message="; ".join(warnings[:3]),  # Limit warning messages
                    result_data=result_data
                )

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
                "required_headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "description": "Headers that must be present. Use '*' for any value, or '/pattern/' for regex matching. Example: {'Content-Type': 'application/json', 'X-Custom': '*'}"
                },
                "forbidden_headers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Headers that must NOT be present (e.g., 'Server', 'X-Powered-By' for security)"
                },
                "security_headers_check": {
                    "type": "boolean",
                    "default": False,
                    "description": "Check for common security headers (HSTS, CSP, X-Frame-Options, etc.) and warn if missing"
                },
                "method": {
                    "type": "string",
                    "enum": ["HEAD", "GET"],
                    "default": "HEAD",
                    "description": "HTTP method to use (HEAD is faster)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 60,
                    "description": "Request timeout in seconds"
                }
            }
        }
