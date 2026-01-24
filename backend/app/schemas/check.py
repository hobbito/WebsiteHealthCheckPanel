from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class CheckTypeInfo(BaseModel):
    type: str
    display_name: str
    description: str
    config_schema: Dict[str, Any]


class CheckConfigurationBase(BaseModel):
    site_id: int
    check_type: str
    name: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    interval_seconds: int = Field(default=300, ge=60)
    is_enabled: bool = True


class CheckConfigurationCreate(CheckConfigurationBase):
    pass


class CheckConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    interval_seconds: Optional[int] = Field(None, ge=60)
    is_enabled: Optional[bool] = None


class CheckConfigurationResponse(CheckConfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckResultResponse(BaseModel):
    id: int
    check_configuration_id: int
    status: str
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime

    class Config:
        from_attributes = True
