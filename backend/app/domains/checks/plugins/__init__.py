"""Check plugins - extensible health check implementations"""
from .base import BaseCheck, CheckResult
from .registry import CheckRegistry, register_check

# Import all check implementations to register them
from . import http_check
from . import dns_check
from . import ssl_check
from . import ping_check
from . import keyword_check
from . import port_check
from . import response_time_check
from . import json_api_check
from . import header_check
from . import tls_check
from . import redirect_check
from . import smtp_check
from . import imap_check
from . import pop3_check

__all__ = [
    "BaseCheck",
    "CheckResult",
    "CheckRegistry",
    "register_check",
]
