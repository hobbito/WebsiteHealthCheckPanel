import logging
from typing import Optional

from app.core.scheduler import get_scheduler
from app.tasks.checks import execute_check

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing check schedules dynamically"""

    @staticmethod
    def add_check_job(check_id: int, interval_seconds: int) -> bool:
        """
        Add or update a scheduled job for a check.

        Args:
            check_id: ID of the CheckConfiguration
            interval_seconds: Interval between executions in seconds

        Returns:
            True if job was added/updated successfully
        """
        try:
            scheduler = get_scheduler()
            job_id = f"check_{check_id}"

            # Remove existing job if present
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                logger.debug(f"Removed existing job {job_id}")

            # Add new job
            scheduler.add_job(
                execute_check,
                'interval',
                seconds=interval_seconds,
                id=job_id,
                args=[check_id],
                replace_existing=True,
                max_instances=1,  # Prevent overlapping executions
            )

            logger.info(f"Added job {job_id} with interval {interval_seconds}s")
            return True

        except Exception as e:
            logger.error(f"Error adding job for check {check_id}: {e}")
            return False

    @staticmethod
    def remove_check_job(check_id: int) -> bool:
        """
        Remove a scheduled job for a check.

        Args:
            check_id: ID of the CheckConfiguration

        Returns:
            True if job was removed successfully
        """
        try:
            scheduler = get_scheduler()
            job_id = f"check_{check_id}"

            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                logger.info(f"Removed job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error removing job for check {check_id}: {e}")
            return False

    @staticmethod
    def pause_check_job(check_id: int) -> bool:
        """
        Pause a scheduled job for a check.

        Args:
            check_id: ID of the CheckConfiguration

        Returns:
            True if job was paused successfully
        """
        try:
            scheduler = get_scheduler()
            job_id = f"check_{check_id}"

            job = scheduler.get_job(job_id)
            if job:
                scheduler.pause_job(job_id)
                logger.info(f"Paused job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error pausing job for check {check_id}: {e}")
            return False

    @staticmethod
    def resume_check_job(check_id: int) -> bool:
        """
        Resume a paused job for a check.

        Args:
            check_id: ID of the CheckConfiguration

        Returns:
            True if job was resumed successfully
        """
        try:
            scheduler = get_scheduler()
            job_id = f"check_{check_id}"

            job = scheduler.get_job(job_id)
            if job:
                scheduler.resume_job(job_id)
                logger.info(f"Resumed job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error resuming job for check {check_id}: {e}")
            return False

    @staticmethod
    async def run_check_now(check_id: int) -> bool:
        """
        Manually trigger a check execution immediately (outside of schedule).

        Args:
            check_id: ID of the CheckConfiguration

        Returns:
            True if check was triggered successfully
        """
        try:
            logger.info(f"Manually triggering check {check_id}")
            await execute_check(check_id)
            return True

        except Exception as e:
            logger.error(f"Error manually running check {check_id}: {e}")
            return False
