from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.check import CheckStatus


@dataclass
class CheckResult:
    """Result of a check execution"""
    status: CheckStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    checked_at: datetime = None

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()


class BaseCheck(ABC):
    """
    Abstract base class for all health checks.

    Each check type must implement:
    - execute(): Perform the actual check
    - get_config_schema(): Return JSON schema for configuration validation
    - get_display_name(): Human-readable name for the check type
    """

    @abstractmethod
    async def execute(self, url: str, config: Dict[str, Any]) -> CheckResult:
        """
        Execute the health check.

        Args:
            url: The URL/domain to check
            config: Check-specific configuration from check_configurations.configuration

        Returns:
            CheckResult with status, response_time, and optional error/data
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """
        Return JSON Schema for validating this check's configuration.

        Returns:
            JSON Schema dict describing required/optional config fields
        """
        pass

    @classmethod
    @abstractmethod
    def get_display_name(cls) -> str:
        """
        Return human-readable name for this check type.

        Returns:
            Display name (e.g., "HTTP Status Check", "DNS Record Check")
        """
        pass

    @classmethod
    def get_check_type(cls) -> str:
        """
        Return the unique identifier for this check type.
        Default implementation uses lowercase class name without 'Check' suffix.

        Returns:
            Check type identifier (e.g., "http", "dns", "email")
        """
        class_name = cls.__name__
        if class_name.endswith("Check"):
            class_name = class_name[:-5]  # Remove "Check" suffix
        return class_name.lower()
