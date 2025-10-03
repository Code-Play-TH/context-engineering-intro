"""
Celery configuration for background tasks.

This module configures Celery for handling asynchronous tasks
such as data ingestion, metrics sync, and scheduled jobs.
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
import os

# Get configuration from environment
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "kol_management",
    broker=BROKER_URL,
    backend=RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,

    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Retry settings
    task_default_retry_delay=300,  # 5 minutes
    task_max_retries=3,

    # Rate limits (requests per time period)
    task_default_rate_limit="100/m",  # 100 tasks per minute

    # Beat schedule for periodic tasks
    beat_schedule={
        # Sync all KOLs daily at 2 AM
        "sync-all-kols-daily": {
            "task": "app.tasks.social_media_tasks.scheduled_sync_all_kols",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "sync"}
        },

        # Sync recent content every 4 hours
        "sync-recent-content": {
            "task": "app.tasks.social_media_tasks.scheduled_sync_recent_content",
            "schedule": crontab(minute=0, hour="*/4"),
            "options": {"queue": "sync"}
        },

        # Check D+1 checkpoints every 6 hours
        "check-d-plus-1-checkpoints": {
            "task": "app.tasks.checkpoint_tasks.process_d_plus_1_checkpoints",
            "schedule": crontab(minute=0, hour="*/6"),
            "options": {"queue": "analytics"}
        },

        # Check D+3 checkpoints daily at 10 AM
        "check-d-plus-3-checkpoints": {
            "task": "app.tasks.checkpoint_tasks.process_d_plus_3_checkpoints",
            "schedule": crontab(hour=10, minute=0),
            "options": {"queue": "analytics"}
        },

        # Check D+7 checkpoints weekly on Monday at 9 AM
        "check-d-plus-7-checkpoints": {
            "task": "app.tasks.checkpoint_tasks.process_d_plus_7_checkpoints",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),
            "options": {"queue": "analytics"}
        },

        # Generate campaign reports daily at 8 AM
        "generate-daily-reports": {
            "task": "app.tasks.report_tasks.generate_daily_campaign_reports",
            "schedule": crontab(hour=8, minute=0),
            "options": {"queue": "reports"}
        },

        # Clean up old tasks monthly on 1st at midnight
        "cleanup-old-tasks": {
            "task": "app.tasks.maintenance_tasks.cleanup_old_results",
            "schedule": crontab(hour=0, minute=0, day_of_month=1),
            "options": {"queue": "maintenance"}
        },
    },

    # Task routing
    task_routes={
        "app.tasks.social_media_tasks.*": {"queue": "sync"},
        "app.tasks.checkpoint_tasks.*": {"queue": "analytics"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "app.tasks.communication.*": {"queue": "notifications"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },

    # Queue definitions
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("sync", Exchange("sync"), routing_key="sync.#"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics.#"),
        Queue("reports", Exchange("reports"), routing_key="reports.#"),
        Queue("notifications", Exchange("notifications"), routing_key="notifications.#"),
        Queue("maintenance", Exchange("maintenance"), routing_key="maintenance.#"),
    ),

    # Default queue
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks([
    "app.tasks.social_media_tasks",
    "app.tasks.checkpoint_tasks",
    "app.tasks.report_tasks",
    "app.tasks.communication",
    "app.tasks.maintenance_tasks",
])


# Celery events for monitoring
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    print(f"Request: {self.request!r}")
    return {"status": "success", "message": "Celery is working!"}
