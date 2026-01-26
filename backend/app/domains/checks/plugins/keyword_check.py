"""Keyword/content check plugin"""
import time
import re
from typing import Any, Dict, List
import httpx

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class KeywordCheck(BaseCheck):
    """Check that verifies specific keywords or patterns exist (or don't exist) in page content"""

    @property
    def check_type(self) -> str:
        return "keyword"

    @property
    def display_name(self) -> str:
        return "Keyword/Content Check"

    @property
    def description(self) -> str:
        return "Verifies that specific keywords or patterns exist (or are absent) in the page content"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        keywords_present = config.get("keywords_present", [])
        keywords_absent = config.get("keywords_absent", [])
        use_regex = config.get("use_regex", False)
        case_sensitive = config.get("case_sensitive", False)
        timeout_seconds = config.get("timeout_seconds", 10)

        start_time = time.time()

        try:
            # Fetch page content
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(site_url, timeout=timeout_seconds)

            response_time_ms = int((time.time() - start_time) * 1000)
            content = response.text

            # Prepare content for matching
            search_content = content if case_sensitive else content.lower()

            # Check for keywords that should be present
            missing_keywords = []
            for keyword in keywords_present:
                search_keyword = keyword if case_sensitive else keyword.lower()

                if use_regex:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    if not re.search(keyword, content, flags):
                        missing_keywords.append(keyword)
                else:
                    if search_keyword not in search_content:
                        missing_keywords.append(keyword)

            # Check for keywords that should be absent
            found_forbidden = []
            for keyword in keywords_absent:
                search_keyword = keyword if case_sensitive else keyword.lower()

                if use_regex:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    if re.search(keyword, content, flags):
                        found_forbidden.append(keyword)
                else:
                    if search_keyword in search_content:
                        found_forbidden.append(keyword)

            # Determine result
            if missing_keywords or found_forbidden:
                errors = []
                if missing_keywords:
                    errors.append(f"Missing keywords: {', '.join(missing_keywords)}")
                if found_forbidden:
                    errors.append(f"Found forbidden keywords: {', '.join(found_forbidden)}")

                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message="; ".join(errors),
                    result_data={
                        "status_code": response.status_code,
                        "content_length": len(content),
                        "missing_keywords": missing_keywords,
                        "found_forbidden": found_forbidden,
                        "keywords_checked": len(keywords_present) + len(keywords_absent)
                    }
                )

            return CheckResult(
                status="success",
                response_time_ms=response_time_ms,
                result_data={
                    "status_code": response.status_code,
                    "content_length": len(content),
                    "keywords_present_checked": len(keywords_present),
                    "keywords_absent_checked": len(keywords_absent),
                    "all_keywords_validated": True
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
                "keywords_present": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Keywords or patterns that MUST be present in the page"
                },
                "keywords_absent": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Keywords or patterns that must NOT be present (e.g., error messages)"
                },
                "use_regex": {
                    "type": "boolean",
                    "default": False,
                    "description": "Treat keywords as regular expressions"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Perform case-sensitive matching"
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
