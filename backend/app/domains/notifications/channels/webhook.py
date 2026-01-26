"""Webhook notification channel using HTTP POST"""
import httpx
from typing import Any, Dict

from .base import BaseNotificationChannel, NotificationPayload
from .registry import register_channel


@register_channel
class WebhookChannel(BaseNotificationChannel):
    """Send notifications via HTTP webhook"""

    @property
    def channel_type(self) -> str:
        return "webhook"

    @property
    def display_name(self) -> str:
        return "Webhook (HTTP)"

    async def send(self, config: Dict[str, Any], payload: NotificationPayload) -> bool:
        """Send webhook notification"""
        url = config.get("url")
        method = config.get("method", "POST").upper()
        headers = dict(config.get("headers", {}))

        # Set content type
        headers.setdefault("Content-Type", "application/json")

        # Add authentication if configured
        auth_type = config.get("auth_type", "none")
        auth = None

        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {config.get('auth_token', '')}"
        elif auth_type == "basic":
            auth = httpx.BasicAuth(
                username=config.get("auth_username", ""),
                password=config.get("auth_password", "")
            )

        # Prepare payload as dict
        payload_dict = payload.model_dump(mode="json")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method,
                url=url,
                json=payload_dict,
                headers=headers,
                auth=auth
            )
            response.raise_for_status()

        return True

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "title": "Webhook URL",
                    "description": "URL to send notifications to"
                },
                "method": {
                    "type": "string",
                    "enum": ["POST", "PUT"],
                    "default": "POST",
                    "title": "HTTP Method",
                    "description": "HTTP method to use"
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Custom Headers",
                    "description": "Additional HTTP headers to include"
                },
                "auth_type": {
                    "type": "string",
                    "enum": ["none", "bearer", "basic"],
                    "default": "none",
                    "title": "Authentication Type",
                    "description": "Type of authentication to use"
                },
                "auth_token": {
                    "type": "string",
                    "title": "Bearer Token",
                    "description": "Bearer token for authentication (if auth_type is 'bearer')"
                },
                "auth_username": {
                    "type": "string",
                    "title": "Basic Auth Username",
                    "description": "Username for basic authentication (if auth_type is 'basic')"
                },
                "auth_password": {
                    "type": "string",
                    "title": "Basic Auth Password",
                    "format": "password",
                    "description": "Password for basic authentication (if auth_type is 'basic')"
                }
            }
        }

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test webhook connection with a HEAD or OPTIONS request"""
        url = config.get("url")
        headers = dict(config.get("headers", {}))

        # Add authentication if configured
        auth_type = config.get("auth_type", "none")
        auth = None

        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {config.get('auth_token', '')}"
        elif auth_type == "basic":
            auth = httpx.BasicAuth(
                username=config.get("auth_username", ""),
                password=config.get("auth_password", "")
            )

        async with httpx.AsyncClient(timeout=10) as client:
            # Try OPTIONS first (CORS preflight), fall back to HEAD
            try:
                response = await client.options(url, headers=headers, auth=auth)
            except httpx.HTTPStatusError:
                response = await client.head(url, headers=headers, auth=auth)

            # Accept 2xx, 405 (method not allowed), or 404 (endpoint might only accept POST)
            # These all indicate the server is reachable
            if response.status_code < 500:
                return True
            response.raise_for_status()

        return True
