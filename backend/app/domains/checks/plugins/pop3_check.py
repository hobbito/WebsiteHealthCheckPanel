"""POP3 email receiving check plugin"""
import time
import ssl
import socket
import asyncio
import poplib
from typing import Any, Dict, Optional

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class POP3Check(BaseCheck):
    """Check that verifies POP3 server connectivity and email receiving capability"""

    @property
    def check_type(self) -> str:
        return "pop3"

    @property
    def display_name(self) -> str:
        return "POP3 Email Check"

    @property
    def description(self) -> str:
        return "Verifies POP3 server connectivity, authentication, and mailbox access for receiving emails"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        # POP3 server configuration
        pop3_host = config.get("pop3_host") or self._extract_host(site_url)
        pop3_port = config.get("pop3_port", 995)
        use_ssl = config.get("use_ssl", True)
        timeout_seconds = config.get("timeout_seconds", 30)

        # Authentication
        username = config.get("username")
        password = config.get("password")

        # Mailbox settings
        warn_if_empty = config.get("warn_if_empty", False)
        min_messages = config.get("min_messages", 1)

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._check_pop3(
                        pop3_host, pop3_port, use_ssl, timeout_seconds,
                        username, password, warn_if_empty, min_messages
                    )
                ),
                timeout=timeout_seconds + 10
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
                if result.get("warning"):
                    return CheckResult(
                        status="warning",
                        response_time_ms=response_time_ms,
                        error_message=result["warning"],
                        result_data=result["data"]
                    )
                return CheckResult(
                    status="success",
                    response_time_ms=response_time_ms,
                    result_data=result["data"]
                )
            else:
                return CheckResult(
                    status="failure",
                    response_time_ms=response_time_ms,
                    error_message=result["error"],
                    result_data=result.get("data", {})
                )

        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=f"POP3 operation timed out after {timeout_seconds}s",
                result_data={"pop3_host": pop3_host, "pop3_port": pop3_port}
            )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=str(e),
                result_data={
                    "pop3_host": pop3_host,
                    "pop3_port": pop3_port,
                    "error_type": type(e).__name__
                }
            )

    def _extract_host(self, url: str) -> str:
        """Extract hostname from URL or return as-is if already a hostname"""
        if "://" in url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.netloc or parsed.path
        else:
            host = url

        if ":" in host:
            host = host.split(":")[0]

        return host

    def _check_pop3(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        timeout: int,
        username: Optional[str],
        password: Optional[str],
        warn_if_empty: bool,
        min_messages: int
    ) -> Dict[str, Any]:
        """Perform POP3 check (blocking)"""
        result_data = {
            "pop3_host": host,
            "pop3_port": port,
            "use_ssl": use_ssl,
            "connection_established": False,
            "authenticated": False
        }

        pop3 = None
        try:
            # Set socket timeout
            socket.setdefaulttimeout(timeout)

            # Create POP3 connection
            if use_ssl:
                context = ssl.create_default_context()
                pop3 = poplib.POP3_SSL(host, port, context=context)
            else:
                pop3 = poplib.POP3(host, port)

            result_data["connection_established"] = True

            # Get server greeting
            welcome = pop3.getwelcome()
            if welcome:
                result_data["server_banner"] = welcome.decode('utf-8', errors='replace')[:200]

            # Check server capabilities if available
            try:
                caps = pop3.capa()
                if caps:
                    result_data["capabilities"] = list(caps.keys())[:10]
            except poplib.error_proto:
                # Server doesn't support CAPA command
                pass

            # Authenticate if credentials provided
            if username and password:
                pop3.user(username)
                pop3.pass_(password)
                result_data["authenticated"] = True

                # Get mailbox statistics
                message_count, mailbox_size = pop3.stat()
                result_data["message_count"] = message_count
                result_data["mailbox_size_bytes"] = mailbox_size

                # Format size for readability
                if mailbox_size >= 1024 * 1024:
                    result_data["mailbox_size_formatted"] = f"{mailbox_size / (1024*1024):.2f} MB"
                elif mailbox_size >= 1024:
                    result_data["mailbox_size_formatted"] = f"{mailbox_size / 1024:.2f} KB"
                else:
                    result_data["mailbox_size_formatted"] = f"{mailbox_size} bytes"

                # Get UIDL for message IDs if available
                try:
                    uidl_response = pop3.uidl()
                    result_data["uidl_supported"] = True
                except poplib.error_proto:
                    result_data["uidl_supported"] = False

                # Check for minimum messages if requested
                if warn_if_empty and message_count < min_messages:
                    pop3.quit()
                    return {
                        "success": True,
                        "warning": f"Mailbox has {message_count} message(s), expected at least {min_messages}",
                        "data": result_data
                    }

            pop3.quit()

            return {
                "success": True,
                "data": result_data
            }

        except poplib.error_proto as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "login" in error_msg.lower() or "denied" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"POP3 authentication failed: {error_msg}",
                    "data": result_data
                }
            return {
                "success": False,
                "error": f"POP3 protocol error: {error_msg}",
                "data": result_data
            }

        except socket.timeout:
            return {
                "success": False,
                "error": f"Connection timed out after {timeout}s",
                "data": result_data
            }

        except socket.gaierror as e:
            return {
                "success": False,
                "error": f"DNS resolution failed for {host}: {str(e)}",
                "data": result_data
            }

        except ConnectionRefusedError:
            return {
                "success": False,
                "error": f"Connection refused on {host}:{port}",
                "data": result_data
            }

        except ssl.SSLError as e:
            return {
                "success": False,
                "error": f"SSL/TLS error: {str(e)}",
                "data": result_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": result_data
            }

        finally:
            if pop3:
                try:
                    pop3.quit()
                except Exception:
                    pass

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pop3_host": {
                    "type": "string",
                    "description": "POP3 server hostname (defaults to site URL hostname)"
                },
                "pop3_port": {
                    "type": "integer",
                    "default": 995,
                    "enum": [110, 995],
                    "description": "POP3 port (995=SSL/TLS, 110=plain)"
                },
                "use_ssl": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use SSL/TLS connection (required for port 995)"
                },
                "username": {
                    "type": "string",
                    "description": "POP3 login username (usually email address)"
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "description": "POP3 login password"
                },
                "warn_if_empty": {
                    "type": "boolean",
                    "default": False,
                    "description": "Warn if mailbox has fewer than min_messages"
                },
                "min_messages": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 0,
                    "description": "Minimum expected messages in mailbox"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 120,
                    "description": "Connection timeout in seconds"
                }
            },
            "required": ["username", "password"]
        }
