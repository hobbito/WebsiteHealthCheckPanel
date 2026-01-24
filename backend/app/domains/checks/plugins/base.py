from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    status: str = Field(..., description="Status: 'success', 'failure', or 'warning'")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Additional check-specific data")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of check")


class BaseCheck(ABC):
    @property
    @abstractmethod
    def check_type(self) -> str:
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def execute(self, site_url: str, config: Dict[str, Any]) -> CheckResult:
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        pass
