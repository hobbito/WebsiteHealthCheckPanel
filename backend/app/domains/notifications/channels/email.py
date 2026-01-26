"""Email notification channel using SMTP"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict

from .base import BaseNotificationChannel, NotificationPayload
from .registry import register_channel


@register_channel
class EmailChannel(BaseNotificationChannel):
    """Send notifications via email using SMTP"""

    @property
    def channel_type(self) -> str:
        return "email"

    @property
    def display_name(self) -> str:
        return "Email (SMTP)"

    async def send(self, config: Dict[str, Any], payload: NotificationPayload) -> bool:
        """Send email notification"""
        # Build email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = self._build_subject(payload)
        msg["From"] = config.get("from_address")
        msg["To"] = ", ".join(config.get("to_addresses", []))

        # Build HTML body
        html_body = self._build_html_body(payload)
        text_body = self._build_text_body(payload)

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Send via SMTP
        smtp_config = {
            "hostname": config.get("smtp_host"),
            "port": config.get("smtp_port", 587),
            "username": config.get("smtp_user"),
            "password": config.get("smtp_password"),
            "start_tls": config.get("use_tls", True),
        }

        await aiosmtplib.send(
            msg,
            hostname=smtp_config["hostname"],
            port=smtp_config["port"],
            username=smtp_config["username"],
            password=smtp_config["password"],
            start_tls=smtp_config["start_tls"],
        )

        return True

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["smtp_host", "from_address", "to_addresses"],
            "properties": {
                "smtp_host": {
                    "type": "string",
                    "title": "SMTP Host",
                    "description": "SMTP server hostname"
                },
                "smtp_port": {
                    "type": "integer",
                    "default": 587,
                    "title": "SMTP Port",
                    "description": "SMTP server port"
                },
                "smtp_user": {
                    "type": "string",
                    "title": "SMTP Username",
                    "description": "Username for SMTP authentication"
                },
                "smtp_password": {
                    "type": "string",
                    "title": "SMTP Password",
                    "format": "password",
                    "description": "Password for SMTP authentication"
                },
                "from_address": {
                    "type": "string",
                    "format": "email",
                    "title": "From Address",
                    "description": "Email address to send from"
                },
                "to_addresses": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "title": "Recipients",
                    "description": "Email addresses to send notifications to"
                },
                "use_tls": {
                    "type": "boolean",
                    "default": True,
                    "title": "Use TLS",
                    "description": "Use STARTTLS for secure connection"
                }
            }
        }

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test SMTP connection without sending"""
        smtp = aiosmtplib.SMTP(
            hostname=config.get("smtp_host"),
            port=config.get("smtp_port", 587),
        )

        await smtp.connect()

        if config.get("use_tls", True):
            await smtp.starttls()

        if config.get("smtp_user"):
            await smtp.login(
                config["smtp_user"],
                config.get("smtp_password", "")
            )

        await smtp.quit()
        return True

    def _build_subject(self, payload: NotificationPayload) -> str:
        """Build email subject line"""
        status_emoji = {
            "failure": "🔴",
            "warning": "🟡",
            "success": "🟢",
        }.get(payload.status, "⚪")

        trigger_label = {
            "check_failure": "ALERT",
            "check_recovery": "RECOVERED",
            "incident_opened": "INCIDENT",
            "incident_resolved": "RESOLVED",
        }.get(payload.trigger, payload.trigger.upper())

        return f"{status_emoji} [{trigger_label}] {payload.site_name} - {payload.check_name}"

    def _build_text_body(self, payload: NotificationPayload) -> str:
        """Build plain text email body"""
        lines = [
            f"Site: {payload.site_name}",
            f"URL: {payload.site_url}",
            f"Check: {payload.check_name} ({payload.check_type})",
            f"Status: {payload.status.upper()}",
            f"Time: {payload.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if payload.response_time_ms:
            lines.append(f"Response Time: {payload.response_time_ms}ms")

        if payload.error_message:
            lines.append(f"\nError: {payload.error_message}")

        if payload.incident_id:
            lines.append(f"\nIncident ID: {payload.incident_id}")

        return "\n".join(lines)

    def _build_html_body(self, payload: NotificationPayload) -> str:
        """Build HTML email body"""
        status_color = {
            "failure": "#dc2626",
            "warning": "#f59e0b",
            "success": "#16a34a",
        }.get(payload.status, "#6b7280")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
                .label {{ color: #6b7280; font-size: 12px; text-transform: uppercase; }}
                .value {{ font-size: 16px; margin-bottom: 16px; }}
                .error {{ background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">{payload.site_name}</h2>
                    <p style="margin: 8px 0 0 0; opacity: 0.9;">{payload.check_name} - {payload.status.upper()}</p>
                </div>
                <div class="content">
                    <div class="label">Site URL</div>
                    <div class="value"><a href="{payload.site_url}">{payload.site_url}</a></div>

                    <div class="label">Check Type</div>
                    <div class="value">{payload.check_type}</div>

                    <div class="label">Time</div>
                    <div class="value">{payload.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        """

        if payload.response_time_ms:
            html += f"""
                    <div class="label">Response Time</div>
                    <div class="value">{payload.response_time_ms}ms</div>
            """

        if payload.error_message:
            html += f"""
                    <div class="error">
                        <strong>Error:</strong> {payload.error_message}
                    </div>
            """

        html += """
                </div>
            </div>
        </body>
        </html>
        """

        return html
