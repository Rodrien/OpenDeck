"""
Celery Application Configuration

Configures Celery for background task processing with Redis broker.
Implements task routing, time limits, and retry policies.
"""

from celery import Celery
from celery.signals import task_failure, task_success
import structlog

from app.config import settings

logger = structlog.get_logger()


# Initialize Celery app
celery_app = Celery(
    "opendeck",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Celery Configuration
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.workers.tasks.process_documents_task": {"queue": "documents"},
    },

    # Time limits
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,

    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "visibility_timeout": 43200,  # 12 hours
    },

    # Task acknowledgement
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Monitoring
    task_track_started=True,
    task_send_sent_event=True,
)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, **kw):
    """
    Handle task failures with structured logging.

    Args:
        sender: Task class
        task_id: Unique task identifier
        exception: Exception that caused the failure
        args: Task positional arguments
        kwargs: Task keyword arguments
    """
    logger.error(
        "celery_task_failed",
        task_id=task_id,
        task_name=sender.name if sender else "unknown",
        exception=str(exception),
        exception_type=type(exception).__name__,
        args=args,
        kwargs=kwargs,
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """
    Handle task success with structured logging.

    Args:
        sender: Task class
        result: Task return value
    """
    logger.info(
        "celery_task_succeeded",
        task_name=sender.name if sender else "unknown",
        result_type=type(result).__name__,
    )


if __name__ == "__main__":
    celery_app.start()
