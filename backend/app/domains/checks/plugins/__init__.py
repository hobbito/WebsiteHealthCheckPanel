"""Check plugins - extensible health check implementations"""
from .base import BaseCheck, CheckResult
from .registry import CheckRegistry, register_check

# Import all check implementations to register them
from . import http_check

__all__ = [
    "BaseCheck",
    "CheckResult",
    "CheckRegistry",
    "register_check",
]
