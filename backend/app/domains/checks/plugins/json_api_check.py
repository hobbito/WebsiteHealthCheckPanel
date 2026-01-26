"""JSON API check plugin"""
import time
import json
from typing import Any, Dict, List, Optional
import httpx

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class JSONAPICheck(BaseCheck):
    """Check that validates JSON API responses and their structure"""

    @property
    def check_type(self) -> str:
        return "json_api"

    @property
    def display_name(self) -> str:
        return "JSON API Check"

    @property
    def description(self) -> str:
        return "Validates JSON API endpoints return valid JSON and optionally checks for required fields"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        timeout_seconds = config.get("timeout_seconds", 10)
        method = config.get("method", "GET").upper()
        expected_status_code = config.get("expected_status_code", 200)
        required_fields = config.get("required_fields", [])
        field_type_checks = config.get("field_type_checks", {})
        headers = config.get("headers", {})
        request_body = config.get("request_body")

        start_time = time.time()

        try:
            async with httpx.AsyncClient() as client:
                request_kwargs = {
                    "url": site_url,
                    "timeout": timeout_seconds,
                    "headers": {"Accept": "application/json", **headers}
                }

                if method == "POST" and request_body:
                    request_kwargs["json"] = request_body
                    response = await client.post(**request_kwargs)
                elif method == "PUT" and request_body:
                    request_kwargs["json"] = request_body
                    response = await client.put(**request_kwargs)
                elif method == "DELETE":
                    response = await client.delete(**request_kwargs)
                else:
                    response = await client.get(**request_kwargs)

            response_time_ms = int((time.time() - start_time) * 1000)

            # Check status code
            if response.status_code != expected_status_code:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Expected status {expected_status_code}, got {response.status_code}",
                    result_data={
                        "status_code": response.status_code,
                        "expected_status_code": expected_status_code
                    }
                )

            # Check content type
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type.lower():
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Expected JSON content-type, got: {content_type}",
                    result_data={
                        "status_code": response.status_code,
                        "content_type": content_type
                    }
                )

            # Try to parse JSON
            try:
                json_data = response.json()
            except json.JSONDecodeError as e:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Invalid JSON response: {str(e)}",
                    result_data={
                        "status_code": response.status_code,
                        "content_type": content_type,
                        "parse_error": str(e)
                    }
                )

            # Check required fields
            missing_fields = []
            if required_fields and isinstance(json_data, dict):
                for field in required_fields:
                    if not self._check_field_exists(json_data, field):
                        missing_fields.append(field)

            if missing_fields:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Missing required fields: {', '.join(missing_fields)}",
                    result_data={
                        "status_code": response.status_code,
                        "missing_fields": missing_fields,
                        "required_fields": required_fields
                    }
                )

            # Check field types
            type_errors = []
            if field_type_checks and isinstance(json_data, dict):
                for field, expected_type in field_type_checks.items():
                    error = self._check_field_type(json_data, field, expected_type)
                    if error:
                        type_errors.append(error)

            if type_errors:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=f"Type check failures: {'; '.join(type_errors)}",
                    result_data={
                        "status_code": response.status_code,
                        "type_errors": type_errors
                    }
                )

            # Success - return summary
            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data={
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "json_valid": True,
                    "response_type": type(json_data).__name__,
                    "fields_validated": len(required_fields),
                    "types_validated": len(field_type_checks)
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

    def _check_field_exists(self, data: Dict, field_path: str) -> bool:
        """Check if a field exists in nested dictionary using dot notation"""
        parts = field_path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return False
            else:
                return False
        return True

    def _check_field_type(self, data: Dict, field_path: str, expected_type: str) -> Optional[str]:
        """Check if a field has the expected type. Returns error message or None."""
        parts = field_path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return f"Field '{field_path}' not found"
            else:
                return f"Field '{field_path}' not found"

        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type is None:
            return f"Unknown type '{expected_type}'"

        if not isinstance(current, expected_python_type):
            actual_type = type(current).__name__
            return f"Field '{field_path}' expected {expected_type}, got {actual_type}"

        return None

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expected_status_code": {
                    "type": "integer",
                    "default": 200,
                    "description": "Expected HTTP status code"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                    "default": "GET",
                    "description": "HTTP method to use"
                },
                "required_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Required fields in JSON response (supports dot notation for nested fields, e.g., 'data.user.id')"
                },
                "field_type_checks": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string",
                        "enum": ["string", "number", "integer", "boolean", "array", "object", "null"]
                    },
                    "default": {},
                    "description": "Field type validations (e.g., {'data.count': 'integer'})"
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "description": "Additional headers to send with the request"
                },
                "request_body": {
                    "type": "object",
                    "default": None,
                    "description": "Request body for POST/PUT requests"
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
