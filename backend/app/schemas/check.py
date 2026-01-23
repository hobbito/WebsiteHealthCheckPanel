from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class CheckConfigurationCreate(BaseModel):
    """Schema for creating a check configuration"""
    site_id: int
    check_type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    interval_seconds: int = Field(default=300, ge=60, le=86400)  # 1 min to 24 hours
    is_enabled: bool = True


class CheckConfigurationUpdate(BaseModel):
    """Schema for updating a check configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    configuration: Optional[Dict[str, Any]] = None
    interval_seconds: Optional[int] = Field(None, ge=60, le=86400)
    is_enabled: Optional[bool] = None


class CheckConfigurationResponse(BaseModel):
    """Schema for check configuration response"""
    id: int
    site_id: int
    check_type: str
    name: str
    configuration: Dict[str, Any]
    interval_seconds: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckResultResponse(BaseModel):
    """Schema for check result response"""
    id: int
    check_configuration_id: int
    status: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    checked_at: datetime

    class Config:
        from_attributes = True


class CheckTypeInfo(BaseModel):
    """Schema for check type information"""
    type: str
    display_name: str
    config_schema: Dict[str, Any]
