import aiosmtplib
from email.message import EmailMessage
from typing import Dict, Any, Optional

from app.notifications.base import BaseNotificationChannel, NotificationMessage
from app.notifications.registry import NotificationRegistry
from app.config import settings


@NotificationRegistry.register
class EmailChannel(BaseNotificationChannel):
    """
    Email notification channel using SMTP.

    Configuration schema:
    {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "user@example.com",
        "smtp_password": "password",
        "from_address": "noreply@healthcheck.com"
    }
    """

    @classmethod
    def get_display_name(cls) -> str:
        return "Email (SMTP)"

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "smtp_host": {
                    "type": "string",
                    "description": "SMTP server hostname"
                },
                "smtp_port": {
                    "type": "integer",
                    "default": 587,
                    "description": "SMTP server port"
                },
                "smtp_user": {
                    "type": "string",
                    "description": "SMTP username"
                },
                "smtp_password": {
                    "type": "string",
                    "description": "SMTP password"
                },
                "from_address": {
                    "type": "string",
                    "format": "email",
                    "description": "From email address"
                },
                "use_tls": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use TLS encryption"
                }
            },
            "required": ["smtp_host", "smtp_user", "smtp_password", "from_address"]
        }

    async def send(self, config: Dict[str, Any], message: NotificationMessage) -> tuple[bool, Optional[str]]:
        """Send email notification"""
        try:
            # Get SMTP configuration
            smtp_host = config.get("smtp_host") or settings.SMTP_HOST
            smtp_port = config.get("smtp_port") or settings.SMTP_PORT
            smtp_user = config.get("smtp_user") or settings.SMTP_USER
            smtp_password = config.get("smtp_password") or settings.SMTP_PASSWORD
            from_address = config.get("from_address") or settings.SMTP_FROM
            use_tls = config.get("use_tls", True)

            if not all([smtp_host, smtp_user, smtp_password]):
                return False, "Missing SMTP configuration"

            # Create email message
            email = EmailMessage()
            email["From"] = from_address
            email["To"] = message.recipient
            email["Subject"] = message.subject or "Health Check Alert"
            email.set_content(message.message)

            # Send email
            await aiosmtplib.send(
                email,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                use_tls=use_tls,
            )

            return True, None

        except aiosmtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"

        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
