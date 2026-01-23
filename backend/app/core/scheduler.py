from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    """
    Create and configure APScheduler with PostgreSQL jobstore.

    Using APScheduler instead of Celery because:
    - No Redis/RabbitMQ needed (saves ~$30/mo)
    - Persists jobs in PostgreSQL (we already have it)
    - Perfect for single-container DigitalOcean Apps deployment
    - Async execution with asyncio (non-blocking)
    """

    # Convert asyncpg URL to psycopg2 format for APScheduler
    # APScheduler's SQLAlchemyJobStore uses psycopg2, not asyncpg
    db_url = settings.DATABASE_URL.replace("+asyncpg", "")

    # Job store configuration
    jobstores = {
        'default': SQLAlchemyJobStore(url=db_url)
    }

    # Executor configuration
    executors = {
        'default': AsyncIOExecutor()  # Async execution, non-blocking
    }

    # Job defaults
    job_defaults = {
        'coalesce': False,  # Run all missed jobs (important for health checks)
        'max_instances': 3,  # Max concurrent instances per job
        'misfire_grace_time': 60  # 1 minute grace for missed jobs
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='UTC'
    )

    # Add event listeners for logging
    def job_executed_listener(event):
        logger.info(f"Job {event.job_id} executed successfully")

    def job_error_listener(event):
        logger.error(f"Job {event.job_id} raised an exception: {event.exception}")

    scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)

    return scheduler


# Global scheduler instance (will be initialized in main.py)
scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance"""
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    return scheduler


def init_scheduler() -> AsyncIOScheduler:
    """Initialize and start the global scheduler"""
    global scheduler
    scheduler = create_scheduler()
    logger.info("✅ APScheduler initialized")
    return scheduler
