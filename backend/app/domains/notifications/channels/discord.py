"""Discord notification channel using Discord Webhook"""
import httpx
from typing import Any, Dict, List

from .base import BaseNotificationChannel, NotificationPayload
from .registry import register_channel


@register_channel
class DiscordChannel(BaseNotificationChannel):
    """Send notifications via Discord Webhook"""

    @property
    def channel_type(self) -> str:
        return "discord"

    @property
    def display_name(self) -> str:
        return "Discord"

    def _get_status_color(self, status: str) -> int:
        """Get Discord embed color for status (decimal format)"""
        if status == "success":
            return 3066993  # Green (#2ecc71)
        elif status == "failure":
            return 15158332  # Red (#e74c3c)
        else:
            return 15844367  # Yellow (#f1c40f)

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        if status == "success":
            return "\u2705"  # Green check mark
        elif status == "failure":
            return "\u274c"  # Red X
        else:
            return "\u26a0"  # Warning sign

    def _format_message(self, payload: NotificationPayload, config: Dict[str, Any]) -> Dict[str, Any]:
        """Format the Discord message using embeds"""
        status_emoji = self._get_status_emoji(payload.status)
        status_color = self._get_status_color(payload.status)

        # Build title based on trigger
        trigger_titles = {
            "check_failure": f"{status_emoji} Check Failed",
            "check_recovery": f"{status_emoji} Check Recovered",
            "incident_opened": "\U0001f6a8 Incident Opened",  # Rotating light emoji
            "incident_resolved": "\u2705 Incident Resolved",
        }
        title = trigger_titles.get(payload.trigger, f"{status_emoji} Notification")

        # Build embed fields
        fields: List[Dict[str, Any]] = [
            {
                "name": "Site",
                "value": f"[{payload.site_name}]({payload.site_url})",
                "inline": True
            },
            {
                "name": "Check",
                "value": f"{payload.check_name} ({payload.check_type})",
                "inline": True
            },
            {
                "name": "Status",
                "value": payload.status.upper(),
                "inline": True
            }
        ]

        # Add response time if available
        if payload.response_time_ms is not None:
            fields.append({
                "name": "Response Time",
                "value": f"{payload.response_time_ms}ms",
                "inline": True
            })

        # Add incident ID if available
        if payload.incident_id:
            fields.append({
                "name": "Incident ID",
                "value": str(payload.incident_id),
                "inline": True
            })

        # Add error message if available
        if payload.error_message:
            fields.append({
                "name": "Error Message",
                "value": f"```{payload.error_message[:1000]}```" if len(payload.error_message) > 0 else "N/A",
                "inline": False
            })

        # Build the embed
        embed = {
            "title": title,
            "color": status_color,
            "fields": fields,
            "timestamp": payload.checked_at.isoformat(),
            "footer": {
                "text": "Health Check Panel"
            }
        }

        # Add thumbnail if configured
        if config.get("thumbnail_url"):
            embed["thumbnail"] = {"url": config["thumbnail_url"]}

        # Build the message payload
        message: Dict[str, Any] = {
            "embeds": [embed]
        }

        # Add username override if specified
        if config.get("username"):
            message["username"] = config["username"]

        # Add avatar override if specified
        if config.get("avatar_url"):
            message["avatar_url"] = config["avatar_url"]

        # Add content (plain text before embed) if configured
        if config.get("content"):
            message["content"] = config["content"]

        # Add thread ID if specified (for posting to a specific thread)
        # Note: This needs to be handled at the URL level in Discord

        return message

    async def send(self, config: Dict[str, Any], payload: NotificationPayload) -> bool:
        """Send Discord notification via webhook"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Discord webhook URL is required")

        # Handle thread_id by appending to URL
        if config.get("thread_id"):
            separator = "&" if "?" in webhook_url else "?"
            webhook_url = f"{webhook_url}{separator}thread_id={config['thread_id']}"

        message = self._format_message(payload, config)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        return True

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["webhook_url"],
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "Webhook URL",
                    "description": "Discord Webhook URL (get from Server Settings > Integrations > Webhooks)"
                },
                "username": {
                    "type": "string",
                    "title": "Bot Username",
                    "description": "Override the webhook bot username",
                    "default": "Health Check Bot"
                },
                "avatar_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "Avatar URL",
                    "description": "URL to an image to use as the bot avatar"
                },
                "content": {
                    "type": "string",
                    "title": "Message Content",
                    "description": "Plain text to include before the embed (supports @mentions)",
                    "maxLength": 2000
                },
                "thumbnail_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "Thumbnail URL",
                    "description": "URL for the embed thumbnail image"
                },
                "thread_id": {
                    "type": "string",
                    "title": "Thread ID",
                    "description": "Post to a specific thread (Discord thread/forum post ID)"
                }
            }
        }

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test Discord webhook connection by sending a test message"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Discord webhook URL is required")

        # Handle thread_id by appending to URL
        if config.get("thread_id"):
            separator = "&" if "?" in webhook_url else "?"
            webhook_url = f"{webhook_url}{separator}thread_id={config['thread_id']}"

        test_message: Dict[str, Any] = {
            "embeds": [
                {
                    "title": "\u2705 Connection Test Successful",
                    "description": "This channel is now configured to receive alerts from Health Check Panel.",
                    "color": 3066993,  # Green
                    "footer": {
                        "text": "Health Check Panel"
                    }
                }
            ]
        }

        if config.get("username"):
            test_message["username"] = config["username"]

        if config.get("avatar_url"):
            test_message["avatar_url"] = config["avatar_url"]

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                webhook_url,
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        return True
