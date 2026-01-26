"""IMAP email receiving check plugin"""
import time
import ssl
import socket
import asyncio
import imaplib
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class IMAPCheck(BaseCheck):
    """Check that verifies IMAP server connectivity and email receiving capability"""

    @property
    def check_type(self) -> str:
        return "imap"

    @property
    def display_name(self) -> str:
        return "IMAP Email Check"

    @property
    def description(self) -> str:
        return "Verifies IMAP server connectivity, authentication, and mailbox access for receiving emails"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        # IMAP server configuration
        imap_host = config.get("imap_host") or self._extract_host(site_url)
        imap_port = config.get("imap_port", 993)
        use_ssl = config.get("use_ssl", True)
        timeout_seconds = config.get("timeout_seconds", 30)

        # Authentication
        username = config.get("username")
        password = config.get("password")

        # Mailbox settings
        mailbox = config.get("mailbox", "INBOX")
        check_recent_emails = config.get("check_recent_emails", False)
        recent_hours = config.get("recent_hours", 24)

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._check_imap(
                        imap_host, imap_port, use_ssl, timeout_seconds,
                        username, password, mailbox,
                        check_recent_emails, recent_hours
                    )
                ),
                timeout=timeout_seconds + 10
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
                # Check for warnings
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
                error_message=f"IMAP operation timed out after {timeout_seconds}s",
                result_data={"imap_host": imap_host, "imap_port": imap_port}
            )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=str(e),
                result_data={
                    "imap_host": imap_host,
                    "imap_port": imap_port,
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

    def _check_imap(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        timeout: int,
        username: Optional[str],
        password: Optional[str],
        mailbox: str,
        check_recent_emails: bool,
        recent_hours: int
    ) -> Dict[str, Any]:
        """Perform IMAP check (blocking)"""
        result_data = {
            "imap_host": host,
            "imap_port": port,
            "use_ssl": use_ssl,
            "connection_established": False,
            "authenticated": False,
            "mailbox_accessible": False
        }

        imap = None
        try:
            # Create IMAP connection
            socket.setdefaulttimeout(timeout)

            if use_ssl:
                context = ssl.create_default_context()
                imap = imaplib.IMAP4_SSL(host, port, ssl_context=context)
            else:
                imap = imaplib.IMAP4(host, port)

            result_data["connection_established"] = True

            # Get server capabilities
            caps = imap.capabilities
            if caps:
                result_data["capabilities"] = [str(c) for c in list(caps)[:15]]

            # Authenticate if credentials provided
            if username and password:
                imap.login(username, password)
                result_data["authenticated"] = True

                # Select mailbox
                status, data = imap.select(mailbox, readonly=True)
                if status == 'OK':
                    result_data["mailbox_accessible"] = True
                    result_data["mailbox"] = mailbox

                    # Get message count
                    message_count = int(data[0].decode()) if data and data[0] else 0
                    result_data["total_messages"] = message_count

                    # Get mailbox status
                    status, status_data = imap.status(mailbox, '(MESSAGES RECENT UNSEEN)')
                    if status == 'OK' and status_data:
                        status_str = status_data[0].decode() if status_data[0] else ""
                        result_data["mailbox_status"] = status_str

                        # Parse status response
                        import re
                        messages_match = re.search(r'MESSAGES\s+(\d+)', status_str)
                        recent_match = re.search(r'RECENT\s+(\d+)', status_str)
                        unseen_match = re.search(r'UNSEEN\s+(\d+)', status_str)

                        if messages_match:
                            result_data["total_messages"] = int(messages_match.group(1))
                        if recent_match:
                            result_data["recent_messages"] = int(recent_match.group(1))
                        if unseen_match:
                            result_data["unseen_messages"] = int(unseen_match.group(1))

                    # Check for recent emails if requested
                    if check_recent_emails and message_count > 0:
                        since_date = (datetime.now() - timedelta(hours=recent_hours)).strftime("%d-%b-%Y")
                        status, messages = imap.search(None, f'SINCE {since_date}')

                        if status == 'OK' and messages[0]:
                            recent_ids = messages[0].split()
                            result_data["emails_since_check"] = len(recent_ids)
                            result_data["check_period_hours"] = recent_hours

                            if len(recent_ids) == 0:
                                return {
                                    "success": True,
                                    "warning": f"No emails received in the last {recent_hours} hours",
                                    "data": result_data
                                }
                        else:
                            result_data["emails_since_check"] = 0
                            result_data["check_period_hours"] = recent_hours

                else:
                    return {
                        "success": False,
                        "error": f"Failed to select mailbox '{mailbox}': {data}",
                        "data": result_data
                    }

            imap.logout()

            return {
                "success": True,
                "data": result_data
            }

        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            if "AUTHENTICATIONFAILED" in error_msg.upper() or "LOGIN" in error_msg.upper():
                return {
                    "success": False,
                    "error": f"IMAP authentication failed: {error_msg}",
                    "data": result_data
                }
            return {
                "success": False,
                "error": f"IMAP error: {error_msg}",
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
            if imap:
                try:
                    imap.logout()
                except Exception:
                    pass

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "imap_host": {
                    "type": "string",
                    "description": "IMAP server hostname (defaults to site URL hostname)"
                },
                "imap_port": {
                    "type": "integer",
                    "default": 993,
                    "enum": [143, 993],
                    "description": "IMAP port (993=SSL/TLS, 143=plain/STARTTLS)"
                },
                "use_ssl": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use SSL/TLS connection (required for port 993)"
                },
                "username": {
                    "type": "string",
                    "description": "IMAP login username (usually email address)"
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "description": "IMAP login password"
                },
                "mailbox": {
                    "type": "string",
                    "default": "INBOX",
                    "description": "Mailbox to check (default: INBOX)"
                },
                "check_recent_emails": {
                    "type": "boolean",
                    "default": False,
                    "description": "Check if emails were received recently (warns if none)"
                },
                "recent_hours": {
                    "type": "integer",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                    "description": "Hours to look back for recent emails"
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
