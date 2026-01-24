from app.core.scheduler import get_scheduler
from app.tasks.checks import execute_check
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    @staticmethod
    def add_check_job(check_id: int, interval_seconds: int):
        """Add or update a check job in the scheduler"""
        scheduler = get_scheduler()
        job_id = f"check_{check_id}"

        # Remove existing job if present
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Add new job
        scheduler.add_job(
            execute_check,
            'interval',
            seconds=interval_seconds,
            id=job_id,
            args=[check_id],
            replace_existing=True,
            max_instances=1,
        )

        logger.info(f"Scheduled check {check_id} with interval {interval_seconds}s")

    @staticmethod
    def remove_check_job(check_id: int):
        """Remove a check job from the scheduler"""
        scheduler = get_scheduler()
        job_id = f"check_{check_id}"

        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Removed check {check_id} from scheduler")

    @staticmethod
    async def run_check_now(check_id: int):
        """Run a check immediately (outside of scheduled interval)"""
        logger.info(f"Running check {check_id} manually")
        await execute_check(check_id)
