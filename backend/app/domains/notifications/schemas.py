"""Notifications domain schemas"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import NotificationChannelType, NotificationTrigger, NotificationStatus


# ============ Channel Type Info ============

class ChannelTypeInfo(BaseModel):
    """Information about a notification channel type"""
    type: str
    display_name: str
    config_schema: Dict[str, Any]


# ============ Channel Schemas ============

class NotificationChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    channel_type: NotificationChannelType
    configuration: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True


class NotificationChannelCreate(NotificationChannelBase):
    pass


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    configuration: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class NotificationChannelResponse(NotificationChannelBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Rule Schemas ============

class NotificationRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    channel_id: int
    trigger: NotificationTrigger
    site_ids: Optional[List[int]] = None  # null means all sites
    check_types: Optional[List[str]] = None  # null means all check types
    consecutive_failures: int = Field(default=1, ge=1)
    is_enabled: bool = True


class NotificationRuleCreate(NotificationRuleBase):
    pass


class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    channel_id: Optional[int] = None
    trigger: Optional[NotificationTrigger] = None
    site_ids: Optional[List[int]] = None
    check_types: Optional[List[str]] = None
    consecutive_failures: Optional[int] = Field(None, ge=1)
    is_enabled: Optional[bool] = None


class NotificationRuleResponse(NotificationRuleBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Log Schemas ============

class NotificationLogResponse(BaseModel):
    id: int
    rule_id: int
    check_result_id: Optional[int] = None
    incident_id: Optional[int] = None
    status: NotificationStatus
    error_message: Optional[str] = None
    sent_at: datetime

    class Config:
        from_attributes = True


# ============ Test Connection Response ============

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
