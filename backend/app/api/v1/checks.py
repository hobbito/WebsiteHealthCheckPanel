from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.site import Site
from app.models.check import CheckConfiguration, CheckResult
from app.schemas.check import (
    CheckConfigurationCreate,
    CheckConfigurationUpdate,
    CheckConfigurationResponse,
    CheckResultResponse,
    CheckTypeInfo
)
from app.core.security import get_current_user
from app.checks.registry import CheckRegistry
from app.services.scheduler_service import SchedulerService

router = APIRouter()


@router.get("/types", response_model=List[CheckTypeInfo])
async def list_check_types():
    """List all available check types with their configuration schemas"""
    return CheckRegistry.list_checks()


@router.get("/", response_model=List[CheckConfigurationResponse])
async def list_checks(
    site_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all check configurations for the current user's organization"""
    query = select(CheckConfiguration).join(Site).where(
        Site.organization_id == current_user.organization_id
    )

    if site_id:
        query = query.where(CheckConfiguration.site_id == site_id)

    result = await db.execute(query.order_by(CheckConfiguration.created_at.desc()))
    checks = result.scalars().all()
    return checks


@router.post("/", response_model=CheckConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_check(
    check_data: CheckConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new check configuration"""

    # Verify site belongs to user's organization
    site_result = await db.execute(
        select(Site).where(
            Site.id == check_data.site_id,
            Site.organization_id == current_user.organization_id
        )
    )
    site = site_result.scalar_one_or_none()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    # Verify check type is valid
    if not CheckRegistry.is_registered(check_data.check_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid check type: {check_data.check_type}"
        )

    # Create check configuration
    check = CheckConfiguration(**check_data.model_dump())
    db.add(check)
    await db.commit()
    await db.refresh(check)

    # Schedule the check if enabled
    if check.is_enabled:
        SchedulerService.add_check_job(check.id, check.interval_seconds)

    return check


@router.get("/{check_id}", response_model=CheckConfigurationResponse)
async def get_check(
    check_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific check configuration"""
    result = await db.execute(
        select(CheckConfiguration)
        .join(Site)
        .where(
            CheckConfiguration.id == check_id,
            Site.organization_id == current_user.organization_id
        )
    )
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found"
        )

    return check


@router.put("/{check_id}", response_model=CheckConfigurationResponse)
async def update_check(
    check_id: int,
    check_data: CheckConfigurationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a check configuration"""
    result = await db.execute(
        select(CheckConfiguration)
        .join(Site)
        .where(
            CheckConfiguration.id == check_id,
            Site.organization_id == current_user.organization_id
        )
    )
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found"
        )

    # Update fields
    update_data = check_data.model_dump(exclude_unset=True)
    old_interval = check.interval_seconds
    old_enabled = check.is_enabled

    for field, value in update_data.items():
        setattr(check, field, value)

    await db.commit()
    await db.refresh(check)

    # Update schedule if interval or enabled status changed
    if check.is_enabled:
        if old_interval != check.interval_seconds or not old_enabled:
            SchedulerService.add_check_job(check.id, check.interval_seconds)
    else:
        if old_enabled:
            SchedulerService.remove_check_job(check.id)

    return check


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_check(
    check_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a check configuration"""
    result = await db.execute(
        select(CheckConfiguration)
        .join(Site)
        .where(
            CheckConfiguration.id == check_id,
            Site.organization_id == current_user.organization_id
        )
    )
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found"
        )

    # Remove from scheduler
    SchedulerService.remove_check_job(check.id)

    await db.delete(check)
    await db.commit()
    return None


@router.post("/{check_id}/run-now", status_code=status.HTTP_202_ACCEPTED)
async def run_check_now(
    check_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger a check execution immediately"""
    result = await db.execute(
        select(CheckConfiguration)
        .join(Site)
        .where(
            CheckConfiguration.id == check_id,
            Site.organization_id == current_user.organization_id
        )
    )
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found"
        )

    # Run check in background
    background_tasks.add_task(SchedulerService.run_check_now, check.id)

    return {"message": "Check execution triggered", "check_id": check.id}


@router.get("/{check_id}/results", response_model=List[CheckResultResponse])
async def get_check_results(
    check_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get results for a specific check"""

    # Verify check belongs to user's organization
    check_result = await db.execute(
        select(CheckConfiguration)
        .join(Site)
        .where(
            CheckConfiguration.id == check_id,
            Site.organization_id == current_user.organization_id
        )
    )
    check = check_result.scalar_one_or_none()

    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found"
        )

    # Fetch results
    result = await db.execute(
        select(CheckResult)
        .where(CheckResult.check_configuration_id == check_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(limit)
    )
    results = result.scalars().all()
    return results
