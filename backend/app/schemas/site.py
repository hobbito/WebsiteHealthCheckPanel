from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime


class SiteCreate(BaseModel):
    """Schema for creating a site"""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class SiteUpdate(BaseModel):
    """Schema for updating a site"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SiteResponse(BaseModel):
    """Schema for site response"""
    id: int
    name: str
    url: str
    description: Optional[str] = None
    is_active: bool
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
