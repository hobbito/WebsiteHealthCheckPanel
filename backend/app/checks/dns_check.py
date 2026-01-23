import dns.resolver
import dns.exception
import time
from typing import Dict, Any, List
from urllib.parse import urlparse

from app.checks.base import BaseCheck, CheckResult
from app.checks.registry import CheckRegistry
from app.models.check import CheckStatus


@CheckRegistry.register
class DNSCheck(BaseCheck):
    """
    DNS health check - verifies DNS records against expected values.

    Configuration schema:
    {
        "record_type": "A",           # Required: A, AAAA, CNAME, MX, TXT, NS
        "expected_values": [...],     # Optional: list of expected values
        "nameserver": "8.8.8.8"       # Optional: custom DNS server
    }
    """

    @classmethod
    def get_display_name(cls) -> str:
        return "DNS Record Check"

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "record_type": {
                    "type": "string",
                    "enum": ["A", "AAAA", "CNAME", "MX", "TXT", "NS"],
                    "description": "DNS record type to query"
                },
                "expected_values": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Expected DNS record values (optional, if not set will just verify records exist)"
                },
                "nameserver": {
                    "type": "string",
                    "description": "Custom DNS nameserver to use (default: system resolver)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 30,
                    "description": "DNS query timeout in seconds"
                }
            },
            "required": ["record_type"],
            "additionalProperties": False
        }

    async def execute(self, url: str, config: Dict[str, Any]) -> CheckResult:
        """Execute DNS check"""
        # Extract domain from URL if needed
        parsed_url = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed_url.netloc or parsed_url.path

        # Parse configuration
        record_type = config.get("record_type")
        expected_values = config.get("expected_values", [])
        nameserver = config.get("nameserver")
        timeout = config.get("timeout_seconds", 5)

        if not record_type:
            return CheckResult(
                status=CheckStatus.FAILURE,
                error_message="record_type is required in configuration"
            )

        start_time = time.time()

        try:
            # Create resolver
            resolver = dns.resolver.Resolver()
            resolver.timeout = timeout
            resolver.lifetime = timeout

            # Set custom nameserver if specified
            if nameserver:
                resolver.nameservers = [nameserver]

            # Query DNS
            answers = resolver.resolve(domain, record_type)
            response_time_ms = (time.time() - start_time) * 1000

            # Extract record values
            record_values = []
            for rdata in answers:
                if record_type == "MX":
                    # MX records have priority and exchange
                    record_values.append(f"{rdata.preference} {rdata.exchange.to_text()}")
                elif record_type == "TXT":
                    # TXT records are quoted strings
                    record_values.append(rdata.to_text().strip('"'))
                else:
                    record_values.append(rdata.to_text())

            # Verify against expected values if provided
            if expected_values:
                # Normalize values for comparison
                expected_set = set(self._normalize_value(v) for v in expected_values)
                actual_set = set(self._normalize_value(v) for v in record_values)

                if expected_set == actual_set:
                    return CheckResult(
                        status=CheckStatus.SUCCESS,
                        response_time_ms=response_time_ms,
                        result_data={
                            "record_type": record_type,
                            "domain": domain,
                            "records": record_values,
                            "matched_expected": True,
                        }
                    )
                else:
                    missing = expected_set - actual_set
                    extra = actual_set - expected_set
                    return CheckResult(
                        status=CheckStatus.FAILURE,
                        response_time_ms=response_time_ms,
                        error_message=f"DNS records do not match expected values",
                        result_data={
                            "record_type": record_type,
                            "domain": domain,
                            "expected": list(expected_values),
                            "actual": record_values,
                            "missing": list(missing) if missing else [],
                            "extra": list(extra) if extra else [],
                        }
                    )
            else:
                # No expected values, just verify records exist
                if record_values:
                    return CheckResult(
                        status=CheckStatus.SUCCESS,
                        response_time_ms=response_time_ms,
                        result_data={
                            "record_type": record_type,
                            "domain": domain,
                            "records": record_values,
                        }
                    )
                else:
                    return CheckResult(
                        status=CheckStatus.FAILURE,
                        response_time_ms=response_time_ms,
                        error_message=f"No {record_type} records found for {domain}",
                        result_data={
                            "record_type": record_type,
                            "domain": domain,
                        }
                    )

        except dns.resolver.NXDOMAIN:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"Domain {domain} does not exist (NXDOMAIN)",
                result_data={"error_type": "nxdomain", "domain": domain}
            )

        except dns.resolver.NoAnswer:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"No {record_type} records found for {domain}",
                result_data={"error_type": "no_answer", "domain": domain, "record_type": record_type}
            )

        except dns.resolver.Timeout:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"DNS query timed out after {timeout} seconds",
                result_data={"error_type": "timeout", "timeout_seconds": timeout}
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return CheckResult(
                status=CheckStatus.FAILURE,
                response_time_ms=response_time_ms,
                error_message=f"DNS query error: {str(e)}",
                result_data={"error_type": "unexpected_error"}
            )

    @staticmethod
    def _normalize_value(value: str) -> str:
        """Normalize DNS record value for comparison (remove trailing dots, lowercase)"""
        return value.rstrip('.').lower()
