"""SMTP email sending check plugin"""
import time
import ssl
import socket
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional
from datetime import datetime

from .base import BaseCheck, CheckResult
from .registry import register_check


@register_check
class SMTPCheck(BaseCheck):
    """Check that verifies SMTP server connectivity and optionally sends test emails"""

    @property
    def check_type(self) -> str:
        return "smtp"

    @property
    def display_name(self) -> str:
        return "SMTP Email Check"

    @property
    def description(self) -> str:
        return "Verifies SMTP server connectivity, authentication, and optionally sends test emails"

    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        # SMTP server configuration
        smtp_host = config.get("smtp_host") or self._extract_host(site_url)
        smtp_port = config.get("smtp_port", 587)
        use_tls = config.get("use_tls", True)
        use_ssl = config.get("use_ssl", False)
        timeout_seconds = config.get("timeout_seconds", 30)

        # Authentication (optional)
        username = config.get("username")
        password = config.get("password")

        # Test email settings (optional)
        send_test_email = config.get("send_test_email", False)
        test_from_address = config.get("test_from_address")
        test_to_address = config.get("test_to_address")

        # Verification level
        verify_auth = config.get("verify_auth", False)

        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()

            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._check_smtp(
                        smtp_host, smtp_port, use_tls, use_ssl, timeout_seconds,
                        username, password, verify_auth,
                        send_test_email, test_from_address, test_to_address
                    )
                ),
                timeout=timeout_seconds + 10
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
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
                error_message=f"SMTP operation timed out after {timeout_seconds}s",
                result_data={"smtp_host": smtp_host, "smtp_port": smtp_port}
            )

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                status="failure",
                response_time_ms=response_time_ms,
                error_message=str(e),
                result_data={
                    "smtp_host": smtp_host,
                    "smtp_port": smtp_port,
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

    def _check_smtp(
        self,
        host: str,
        port: int,
        use_tls: bool,
        use_ssl: bool,
        timeout: int,
        username: Optional[str],
        password: Optional[str],
        verify_auth: bool,
        send_test_email: bool,
        test_from: Optional[str],
        test_to: Optional[str]
    ) -> Dict[str, Any]:
        """Perform SMTP check (blocking)"""
        result_data = {
            "smtp_host": host,
            "smtp_port": port,
            "use_tls": use_tls,
            "use_ssl": use_ssl,
            "connection_established": False,
            "tls_established": False,
            "authenticated": False,
            "test_email_sent": False
        }

        smtp = None
        try:
            # Create SMTP connection
            if use_ssl:
                context = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
                result_data["tls_established"] = True
            else:
                smtp = smtplib.SMTP(host, port, timeout=timeout)

            result_data["connection_established"] = True

            # Get server greeting/banner
            banner = smtp.ehlo_or_helo_if_needed()
            result_data["server_banner"] = str(smtp.ehlo_resp or smtp.helo_resp or "")[:200]

            # Get supported extensions
            if hasattr(smtp, 'esmtp_features'):
                result_data["esmtp_features"] = list(smtp.esmtp_features.keys())[:10]

            # Start TLS if requested (and not already using SSL)
            if use_tls and not use_ssl:
                if smtp.has_extn('starttls'):
                    context = ssl.create_default_context()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                    result_data["tls_established"] = True
                else:
                    return {
                        "success": False,
                        "error": "Server does not support STARTTLS",
                        "data": result_data
                    }

            # Authenticate if credentials provided
            if username and password:
                if verify_auth or send_test_email:
                    smtp.login(username, password)
                    result_data["authenticated"] = True

            # Send test email if requested
            if send_test_email and test_from and test_to:
                if not result_data["authenticated"] and username and password:
                    smtp.login(username, password)
                    result_data["authenticated"] = True

                msg = MIMEMultipart()
                msg['From'] = test_from
                msg['To'] = test_to
                msg['Subject'] = f"Health Check Test - {datetime.utcnow().isoformat()}"

                body = f"""This is an automated health check test email.

Timestamp: {datetime.utcnow().isoformat()}
SMTP Server: {host}:{port}

If you received this email, SMTP sending is working correctly.
"""
                msg.attach(MIMEText(body, 'plain'))

                smtp.sendmail(test_from, [test_to], msg.as_string())
                result_data["test_email_sent"] = True
                result_data["test_email_to"] = test_to

            smtp.quit()

            return {
                "success": True,
                "data": result_data
            }

        except smtplib.SMTPAuthenticationError as e:
            result_data["auth_error"] = str(e)
            return {
                "success": False,
                "error": f"SMTP authentication failed: {e.smtp_code} {e.smtp_error}",
                "data": result_data
            }

        except smtplib.SMTPConnectError as e:
            return {
                "success": False,
                "error": f"Failed to connect to SMTP server: {str(e)}",
                "data": result_data
            }

        except smtplib.SMTPServerDisconnected as e:
            return {
                "success": False,
                "error": f"SMTP server disconnected unexpectedly: {str(e)}",
                "data": result_data
            }

        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}",
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
            if smtp:
                try:
                    smtp.close()
                except Exception:
                    pass

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "smtp_host": {
                    "type": "string",
                    "description": "SMTP server hostname (defaults to site URL hostname)"
                },
                "smtp_port": {
                    "type": "integer",
                    "default": 587,
                    "enum": [25, 465, 587, 2525],
                    "description": "SMTP port (587=submission/TLS, 465=SSL, 25=standard)"
                },
                "use_tls": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use STARTTLS to upgrade connection to TLS"
                },
                "use_ssl": {
                    "type": "boolean",
                    "default": False,
                    "description": "Use implicit SSL/TLS (for port 465)"
                },
                "username": {
                    "type": "string",
                    "description": "SMTP authentication username (optional)"
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "description": "SMTP authentication password (optional)"
                },
                "verify_auth": {
                    "type": "boolean",
                    "default": False,
                    "description": "Actually attempt authentication (requires credentials)"
                },
                "send_test_email": {
                    "type": "boolean",
                    "default": False,
                    "description": "Send a test email to verify full delivery"
                },
                "test_from_address": {
                    "type": "string",
                    "format": "email",
                    "description": "From address for test email"
                },
                "test_to_address": {
                    "type": "string",
                    "format": "email",
                    "description": "Recipient address for test email"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 120,
                    "description": "Connection timeout in seconds"
                }
            }
        }
