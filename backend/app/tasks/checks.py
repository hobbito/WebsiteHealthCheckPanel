import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.domains.checks.models import CheckConfiguration, CheckResult
from app.domains.sites.models import Site
from app.domains.checks.plugins.registry import CheckRegistry
from app.domains.notifications.service import NotificationService
from app.core.event_bus import event_bus
from app.core.scheduler import get_scheduler

logger = logging.getLogger(__name__)


async def execute_check(check_id: int):
    """
    Execute a single health check.
    This function is called by APScheduler according to the check's schedule.

    Args:
        check_id: ID of the CheckConfiguration to execute
    """
    logger.info(f"Executing check {check_id}")

    async with get_db_context() as db:
        # Fetch check configuration
        result = await db.execute(
            select(CheckConfiguration).where(CheckConfiguration.id == check_id)
        )
        check_config = result.scalar_one_or_none()

        if not check_config:
            logger.warning(f"Check configuration {check_id} not found")
            return

        if not check_config.is_enabled:
            logger.info(f"Check {check_id} is disabled, skipping")
            return

        # Fetch site
        site_result = await db.execute(
            select(Site).where(Site.id == check_config.site_id)
        )
        site = site_result.scalar_one_or_none()

        if not site or not site.is_active:
            logger.warning(f"Site {check_config.site_id} not found or inactive")
            return

        try:
            # Get check plugin and execute
            check_class = CheckRegistry.get_check(check_config.check_type)
            check_instance = check_class()

            logger.debug(f"Executing {check_config.check_type} check for {site.url}")
            result = await check_instance.execute(
                site.url,
                check_config.configuration
            )

            # Store result in database
            db_result = CheckResult(
                check_configuration_id=check_id,
                status=result.status,
                response_time_ms=result.response_time_ms,
                error_message=result.error_message,
                result_data=result.result_data,
                checked_at=result.checked_at
            )
            db.add(db_result)
            await db.commit()
            await db.refresh(db_result)

            logger.info(
                f"Check {check_id} completed: {result.status} "
                f"(response_time: {result.response_time_ms}ms)"
            )

            # Publish to event bus for real-time updates
            await event_bus.publish(
                f'org:{site.organization_id}',
                {
                    'type': 'check_result',
                    'check_id': check_id,
                    'site_id': site.id,
                    'site_name': site.name,
                    'check_name': check_config.name,
                    'status': result.status,
                    'response_time_ms': result.response_time_ms,
                    'checked_at': result.checked_at.isoformat(),
                    'error_message': result.error_message,
                }
            )

            # Handle notifications based on check result
            try:
                await NotificationService.handle_check_result(
                    db, check_config, db_result, site
                )
            except Exception as notification_error:
                logger.error(f"Error handling notifications for check {check_id}: {notification_error}")

        except Exception as e:
            logger.error(f"Error executing check {check_id}: {e}", exc_info=True)

            # Store error result
            db_result = CheckResult(
                check_configuration_id=check_id,
                status="failure",
                error_message=f"Check execution error: {str(e)}"
            )
            db.add(db_result)
            await db.commit()


async def sync_check_schedules():
    """
    Sync all enabled check configurations with APScheduler.
    This is called on application startup to restore scheduled jobs.
    """
    logger.info("Syncing check schedules with APScheduler...")

    scheduler = get_scheduler()

    async with get_db_context() as db:
        # Fetch all enabled check configurations
        result = await db.execute(
            select(CheckConfiguration).where(CheckConfiguration.is_enabled == True)
        )
        check_configs = result.scalars().all()

        scheduled_count = 0
        for check_config in check_configs:
            job_id = f"check_{check_config.id}"

            # Remove existing job if present
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)

            # Add job with interval
            scheduler.add_job(
                execute_check,
                'interval',
                seconds=check_config.interval_seconds,
                id=job_id,
                args=[check_config.id],
                replace_existing=True,
                max_instances=1,  # Prevent overlapping executions
            )

            scheduled_count += 1
            logger.debug(f"Scheduled check {check_config.id} with interval {check_config.interval_seconds}s")

    logger.info(f"✅ Synced {scheduled_count} check schedules")
    return scheduled_count
