"""
Celery application configuration for KOL Management System.
Handles asynchronous task processing for communications, monitoring, and analytics.
"""

import logging
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "kol_management",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.communication",
        "app.tasks.social_media",
        "app.tasks.campaigns",
        "app.tasks.analytics",
        "app.tasks.monitoring"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_on_timeout": True,
        "socket_keepalive": True,
        "socket_keepalive_options": {
            "TCP_KEEPIDLE": 1,
            "TCP_KEEPINTVL": 3,
            "TCP_KEEPCNT": 5,
        },
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # Task routing
    task_routes={
        "app.tasks.communication.*": {"queue": "communication"},
        "app.tasks.social_media.*": {"queue": "social_media"},
        "app.tasks.campaigns.*": {"queue": "campaigns"},
        "app.tasks.analytics.*": {"queue": "analytics"},
        "app.tasks.monitoring.*": {"queue": "monitoring"},
    },

    # Queue definitions
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("communication", routing_key="communication"),
        Queue("social_media", routing_key="social_media"),
        Queue("campaigns", routing_key="campaigns"),
        Queue("analytics", routing_key="analytics"),
        Queue("monitoring", routing_key="monitoring"),
        Queue("priority", routing_key="priority"),
    ),

    # Rate limiting
    task_annotations={
        "app.tasks.communication.send_bulk_emails": {"rate_limit": "100/m"},
        "app.tasks.social_media.collect_social_data": {"rate_limit": "50/m"},
        "app.tasks.social_media.monitor_content": {"rate_limit": "30/m"},
        "app.tasks.campaigns.process_campaign_automation": {"rate_limit": "20/m"},
        "app.tasks.analytics.generate_report": {"rate_limit": "10/m"},
    },

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Beat schedule for periodic tasks
    beat_schedule={
        # Social media monitoring every 5 minutes
        "monitor-social-content": {
            "task": "app.tasks.monitoring.monitor_social_media_content",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "monitoring"}
        },

        # Collect performance data every 30 minutes
        "collect-performance-data": {
            "task": "app.tasks.social_media.collect_performance_data",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "social_media"}
        },

        # Process scheduled messages every minute
        "process-scheduled-messages": {
            "task": "app.tasks.communication.process_scheduled_messages",
            "schedule": crontab(minute="*"),
            "options": {"queue": "communication"}
        },

        # Process campaign automations every 10 minutes
        "process-campaign-automations": {
            "task": "app.tasks.campaigns.process_campaign_automations",
            "schedule": crontab(minute="*/10"),
            "options": {"queue": "campaigns"}
        },

        # Generate daily analytics at 6 AM UTC
        "generate-daily-analytics": {
            "task": "app.tasks.analytics.generate_daily_analytics",
            "schedule": crontab(hour=6, minute=0),
            "options": {"queue": "analytics"}
        },

        # Clean up old task results every 6 hours
        "cleanup-task-results": {
            "task": "app.tasks.maintenance.cleanup_old_results",
            "schedule": crontab(minute=0, hour="*/6"),
            "options": {"queue": "default"}
        },

        # Health check every hour
        "health-check": {
            "task": "app.tasks.monitoring.health_check",
            "schedule": crontab(minute=0),
            "options": {"queue": "monitoring"}
        },
    }
)

# Task failure handler
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery functionality."""
    print(f"Request: {self.request!r}")
    return {"status": "success", "worker_id": self.request.id}


# Error handling
class TaskFailureHandler:
    """Handle task failures and retries."""

    @staticmethod
    def handle_failure(task_id: str, error: str, traceback: str, sender=None, **kwargs):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {error}")
        logger.error(f"Traceback: {traceback}")

        # Could send alerts or notifications here
        # For now, just log the failure

    @staticmethod
    def handle_retry(task_id: str, reason: str, traceback: str, sender=None, **kwargs):
        """Handle task retry."""
        logger.warning(f"Task {task_id} retry: {reason}")


# Register signal handlers
from celery.signals import task_failure, task_retry

task_failure.connect(TaskFailureHandler.handle_failure)
task_retry.connect(TaskFailureHandler.handle_retry)


# Utility functions for task management
def get_task_status(task_id: str) -> dict:
    """
    Get status of a Celery task.

    Args:
        task_id: Task identifier

    Returns:
        Dict with task status information
    """
    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
        "traceback": result.traceback,
        "ready": result.ready(),
        "successful": result.successful(),
        "failed": result.failed()
    }


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task.

    Args:
        task_id: Task identifier

    Returns:
        True if task was cancelled
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
        return False


def get_active_tasks() -> list:
    """
    Get list of currently active tasks.

    Returns:
        List of active task information
    """
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if active_tasks:
            all_tasks = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    task["worker"] = worker
                    all_tasks.append(task)
            return all_tasks

        return []

    except Exception as e:
        logger.error(f"Failed to get active tasks: {str(e)}")
        return []


def get_worker_stats() -> dict:
    """
    Get Celery worker statistics.

    Returns:
        Dict with worker statistics
    """
    try:
        inspect = celery_app.control.inspect()

        stats = {
            "registered_tasks": inspect.registered(),
            "active_queues": inspect.active_queues(),
            "stats": inspect.stats(),
            "reserved": inspect.reserved(),
            "scheduled": inspect.scheduled()
        }

        return stats

    except Exception as e:
        logger.error(f"Failed to get worker stats: {str(e)}")
        return {}


# Queue management utilities
def purge_queue(queue_name: str) -> int:
    """
    Purge all tasks from a specific queue.

    Args:
        queue_name: Name of queue to purge

    Returns:
        Number of tasks purged
    """
    try:
        return celery_app.control.purge()
    except Exception as e:
        logger.error(f"Failed to purge queue {queue_name}: {str(e)}")
        return 0


def get_queue_length(queue_name: str) -> int:
    """
    Get number of tasks in a specific queue.

    Args:
        queue_name: Name of queue

    Returns:
        Number of tasks in queue
    """
    try:
        inspect = celery_app.control.inspect()
        reserved = inspect.reserved()

        if reserved:
            total_tasks = 0
            for worker, tasks in reserved.items():
                total_tasks += len([t for t in tasks if t.get("delivery_info", {}).get("routing_key") == queue_name])
            return total_tasks

        return 0

    except Exception as e:
        logger.error(f"Failed to get queue length for {queue_name}: {str(e)}")
        return 0


# Priority task decorator
def priority_task(*args, **kwargs):
    """
    Decorator for high-priority tasks.
    """
    kwargs.setdefault("queue", "priority")
    kwargs.setdefault("priority", 9)
    return celery_app.task(*args, **kwargs)


# Monitoring utilities
def get_celery_health() -> dict:
    """
    Get Celery cluster health status.

    Returns:
        Dict with health information
    """
    try:
        inspect = celery_app.control.inspect()

        # Check if workers are responding
        stats = inspect.stats()
        active = inspect.active()

        healthy_workers = 0
        total_workers = 0

        if stats:
            for worker, worker_stats in stats.items():
                total_workers += 1
                if worker_stats:  # Worker responded
                    healthy_workers += 1

        return {
            "healthy": healthy_workers > 0,
            "total_workers": total_workers,
            "healthy_workers": healthy_workers,
            "broker_connected": True,  # If we get here, broker is connected
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Export main app
__all__ = ["celery_app"]