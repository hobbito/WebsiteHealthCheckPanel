"""Notifications domain API routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from .models import NotificationChannel, NotificationRule, NotificationLog
from .schemas import (
    NotificationChannelCreate,
    NotificationChannelUpdate,
    NotificationChannelResponse,
    NotificationRuleCreate,
    NotificationRuleUpdate,
    NotificationRuleResponse,
    NotificationLogResponse,
    ChannelTypeInfo,
    TestConnectionResponse,
)
from .channels.registry import ChannelRegistry
from .service import NotificationService

router = APIRouter()


# ============ Channel Types ============

@router.get("/channel-types", response_model=List[ChannelTypeInfo])
async def list_channel_types():
    """List all available notification channel types with their configuration schemas"""
    return ChannelRegistry.list_channels()


# ============ Channels CRUD ============

@router.get("/channels", response_model=List[NotificationChannelResponse])
async def list_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all notification channels for the current user's organization"""
    result = await db.execute(
        select(NotificationChannel)
        .where(NotificationChannel.organization_id == current_user.organization_id)
        .order_by(NotificationChannel.created_at.desc())
    )
    return result.scalars().all()


@router.post("/channels", response_model=NotificationChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: NotificationChannelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification channel"""
    # Verify channel type is valid
    if not ChannelRegistry.is_registered(channel_data.channel_type.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel type: {channel_data.channel_type}"
        )

    # Create channel
    channel = NotificationChannel(
        **channel_data.model_dump(),
        organization_id=current_user.organization_id
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return channel


@router.get("/channels/{channel_id}", response_model=NotificationChannelResponse)
async def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification channel"""
    result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == current_user.organization_id
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    return channel


@router.put("/channels/{channel_id}", response_model=NotificationChannelResponse)
async def update_channel(
    channel_id: int,
    channel_data: NotificationChannelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a notification channel"""
    result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == current_user.organization_id
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    # Update fields
    update_data = channel_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    return channel


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification channel"""
    result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == current_user.organization_id
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    await db.delete(channel)
    await db.commit()

    return None


@router.post("/channels/{channel_id}/test", response_model=TestConnectionResponse)
async def test_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test a notification channel configuration"""
    result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == current_user.organization_id
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    try:
        success = await NotificationService.send_test_notification(db, channel)
        return TestConnectionResponse(
            success=success,
            message="Connection test successful"
        )
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=str(e)
        )


# ============ Rules CRUD ============

@router.get("/rules", response_model=List[NotificationRuleResponse])
async def list_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all notification rules for the current user's organization"""
    result = await db.execute(
        select(NotificationRule)
        .where(NotificationRule.organization_id == current_user.organization_id)
        .order_by(NotificationRule.created_at.desc())
    )
    return result.scalars().all()


@router.post("/rules", response_model=NotificationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: NotificationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification rule"""
    # Verify channel exists and belongs to org
    channel_result = await db.execute(
        select(NotificationChannel).where(
            NotificationChannel.id == rule_data.channel_id,
            NotificationChannel.organization_id == current_user.organization_id
        )
    )
    if not channel_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel not found"
        )

    # Create rule
    rule = NotificationRule(
        **rule_data.model_dump(),
        organization_id=current_user.organization_id
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return rule


@router.get("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def get_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification rule"""
    result = await db.execute(
        select(NotificationRule).where(
            NotificationRule.id == rule_id,
            NotificationRule.organization_id == current_user.organization_id
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    return rule


@router.put("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: NotificationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a notification rule"""
    result = await db.execute(
        select(NotificationRule).where(
            NotificationRule.id == rule_id,
            NotificationRule.organization_id == current_user.organization_id
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    # If channel_id is being updated, verify it exists
    update_data = rule_data.model_dump(exclude_unset=True)
    if "channel_id" in update_data:
        channel_result = await db.execute(
            select(NotificationChannel).where(
                NotificationChannel.id == update_data["channel_id"],
                NotificationChannel.organization_id == current_user.organization_id
            )
        )
        if not channel_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel not found"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification rule"""
    result = await db.execute(
        select(NotificationRule).where(
            NotificationRule.id == rule_id,
            NotificationRule.organization_id == current_user.organization_id
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    await db.delete(rule)
    await db.commit()

    return None


# ============ Logs ============

@router.get("/logs", response_model=List[NotificationLogResponse])
async def list_logs(
    rule_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List notification logs for the current user's organization"""
    query = (
        select(NotificationLog)
        .join(NotificationRule)
        .where(NotificationRule.organization_id == current_user.organization_id)
    )

    if rule_id:
        query = query.where(NotificationLog.rule_id == rule_id)

    query = query.order_by(NotificationLog.sent_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
