"""Slack notification channel using Slack Webhook"""
import httpx
from typing import Any, Dict

from .base import BaseNotificationChannel, NotificationPayload
from .registry import register_channel


@register_channel
class SlackChannel(BaseNotificationChannel):
    """Send notifications via Slack Webhook"""

    @property
    def channel_type(self) -> str:
        return "slack"

    @property
    def display_name(self) -> str:
        return "Slack"

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        if status == "success":
            return ":white_check_mark:"
        elif status == "failure":
            return ":x:"
        else:
            return ":warning:"

    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        if status == "success":
            return "#36a64f"  # Green
        elif status == "failure":
            return "#dc3545"  # Red
        else:
            return "#ffc107"  # Yellow

    def _format_message(self, payload: NotificationPayload, config: Dict[str, Any]) -> Dict[str, Any]:
        """Format the Slack message using Block Kit"""
        status_emoji = self._get_status_emoji(payload.status)
        status_color = self._get_status_color(payload.status)

        # Build title based on trigger
        trigger_titles = {
            "check_failure": f"{status_emoji} Check Failed",
            "check_recovery": f"{status_emoji} Check Recovered",
            "incident_opened": ":rotating_light: Incident Opened",
            "incident_resolved": ":white_check_mark: Incident Resolved",
        }
        title = trigger_titles.get(payload.trigger, f"{status_emoji} Notification")

        # Build message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Site:*\n<{payload.site_url}|{payload.site_name}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Check:*\n{payload.check_name} ({payload.check_type})"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{payload.status.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{payload.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]

        # Add response time if available
        if payload.response_time_ms is not None:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Response Time:* {payload.response_time_ms}ms"
                }
            })

        # Add error message if available
        if payload.error_message:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{payload.error_message}```"
                }
            })

        # Add divider and context
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Sent from Health Check Panel"
                    }
                ]
            }
        ])

        message = {
            "attachments": [
                {
                    "color": status_color,
                    "blocks": blocks
                }
            ]
        }

        # Add channel override if specified
        if config.get("channel"):
            message["channel"] = config["channel"]

        # Add username override if specified
        if config.get("username"):
            message["username"] = config["username"]

        # Add icon override if specified
        if config.get("icon_emoji"):
            message["icon_emoji"] = config["icon_emoji"]
        elif config.get("icon_url"):
            message["icon_url"] = config["icon_url"]

        return message

    async def send(self, config: Dict[str, Any], payload: NotificationPayload) -> bool:
        """Send Slack notification via webhook"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Slack webhook URL is required")

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
                    "description": "Slack Incoming Webhook URL (get from Slack App settings)"
                },
                "channel": {
                    "type": "string",
                    "title": "Channel Override",
                    "description": "Override the default channel (e.g., #alerts). Leave empty for default.",
                    "pattern": "^#?[a-zA-Z0-9_-]+$"
                },
                "username": {
                    "type": "string",
                    "title": "Bot Username",
                    "description": "Override the bot username. Leave empty for default.",
                    "default": "Health Check Bot"
                },
                "icon_emoji": {
                    "type": "string",
                    "title": "Icon Emoji",
                    "description": "Emoji to use as the bot icon (e.g., :robot_face:)",
                    "pattern": "^:[a-zA-Z0-9_+-]+:$"
                },
                "icon_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "Icon URL",
                    "description": "URL to an image to use as the bot icon"
                }
            }
        }

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test Slack webhook connection by sending a test message"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Slack webhook URL is required")

        test_message = {
            "text": ":white_check_mark: Health Check Panel connection test successful!",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":white_check_mark: *Health Check Panel*\nConnection test successful! This channel is now configured to receive alerts."
                    }
                }
            ]
        }

        # Add channel override if specified
        if config.get("channel"):
            test_message["channel"] = config["channel"]

        if config.get("username"):
            test_message["username"] = config["username"]

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                webhook_url,
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        return True
