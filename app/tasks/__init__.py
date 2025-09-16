"""
Background Tasks Package

Provides comprehensive background task processing for the KOL Management System:
- Communication tasks: bulk messaging, scheduled sends, delivery tracking
- Social media tasks: content monitoring, data collection, performance tracking
- Campaign tasks: automation, brief generation, performance monitoring
- Analytics tasks: report generation, ROI analysis, benchmarking
- Monitoring tasks: health checks, performance alerts, system metrics
- Maintenance tasks: data cleanup, optimization, backups

All tasks are processed asynchronously using Celery with Redis as the broker.
"""

from app.tasks.celery_app import celery_app

# Import all task modules to register tasks with Celery
from app.tasks import (
    communication,
    social_media,
    campaigns,
    analytics,
    monitoring,
    maintenance
)

# Export the main Celery app and utility functions
__all__ = [
    "celery_app",

    # Communication tasks
    "communication",

    # Social media tasks
    "social_media",

    # Campaign tasks
    "campaigns",

    # Analytics tasks
    "analytics",

    # Monitoring tasks
    "monitoring",

    # Maintenance tasks
    "maintenance",
]

# Task discovery for Celery auto-discovery
def get_all_tasks():
    """
    Get list of all available background tasks.

    Returns:
        Dict of task categories and their available tasks
    """
    return {
        "communication": [
            "send_bulk_emails",
            "send_bulk_discord_messages",
            "send_bulk_line_messages",
            "process_scheduled_messages",
            "track_message_delivery",
            "send_campaign_notifications",
            "process_communication_templates"
        ],
        "social_media": [
            "collect_kol_profile_data",
            "collect_performance_data",
            "monitor_content_mentions",
            "update_follower_counts",
            "analyze_content_performance",
            "sync_platform_data",
            "verify_content_compliance"
        ],
        "campaigns": [
            "process_campaign_automations",
            "schedule_campaign_content",
            "generate_campaign_brief",
            "monitor_campaign_performance",
            "process_campaign_payments"
        ],
        "analytics": [
            "generate_daily_analytics",
            "generate_campaign_report",
            "generate_kol_performance_report",
            "calculate_engagement_benchmarks",
            "generate_roi_analysis",
            "update_kol_performance_metrics"
        ],
        "monitoring": [
            "monitor_social_media_content",
            "health_check",
            "monitor_performance_alerts",
            "monitor_communication_delivery",
            "cleanup_old_data",
            "generate_system_metrics"
        ],
        "maintenance": [
            "cleanup_old_results",
            "optimize_database",
            "backup_critical_data",
            "monitor_system_health",
            "update_search_indexes",
            "cleanup_expired_sessions"
        ]
    }


def get_task_status_summary():
    """
    Get summary of task execution status across all queues.

    Returns:
        Dict with task queue statistics
    """
    from app.tasks.celery_app import get_active_tasks, get_worker_stats

    try:
        active_tasks = get_active_tasks()
        worker_stats = get_worker_stats()

        return {
            "active_tasks": len(active_tasks),
            "worker_stats": worker_stats,
            "queue_status": {
                "communication": len([t for t in active_tasks if t.get("delivery_info", {}).get("routing_key") == "communication"]),
                "social_media": len([t for t in active_tasks if t.get("delivery_info", {}).get("routing_key") == "social_media"]),
                "campaigns": len([t for t in active_tasks if t.get("delivery_info", {}).get("routing_key") == "campaigns"]),
                "analytics": len([t for t in active_tasks if t.get("delivery_info", {}).get("routing_key") == "analytics"]),
                "monitoring": len([t for t in active_tasks if t.get("delivery_info", {}).get("routing_key") == "monitoring"]),
                "default": len([t for t in active_tasks if t.get("delivery_info", {}).get("routing_key") == "default"])
            }
        }
    except Exception as e:
        return {"error": str(e), "active_tasks": 0}


# Convenience functions for common task operations
def schedule_kol_data_collection(kol_id: int, platforms: list = None):
    """
    Schedule KOL data collection task.

    Args:
        kol_id: KOL identifier
        platforms: List of platforms to collect from
    """
    from app.tasks.social_media import collect_kol_profile_data
    return collect_kol_profile_data.delay(kol_id, platforms)


def schedule_campaign_brief_generation(campaign_id: int, brief_template: dict):
    """
    Schedule campaign brief generation task.

    Args:
        campaign_id: Campaign identifier
        brief_template: Brief template configuration
    """
    from app.tasks.campaigns import generate_campaign_brief
    return generate_campaign_brief.delay(campaign_id, brief_template)


def schedule_bulk_messaging(message_configs: list):
    """
    Schedule bulk messaging task.

    Args:
        message_configs: List of message configurations
    """
    from app.tasks.communication import send_bulk_emails
    return send_bulk_emails.delay(message_configs)


def schedule_performance_monitoring(campaign_id: int):
    """
    Schedule campaign performance monitoring task.

    Args:
        campaign_id: Campaign identifier
    """
    from app.tasks.campaigns import monitor_campaign_performance
    return monitor_campaign_performance.delay(campaign_id)


def schedule_analytics_report(report_type: str, **kwargs):
    """
    Schedule analytics report generation.

    Args:
        report_type: Type of report to generate
        **kwargs: Additional parameters for report generation
    """
    if report_type == "campaign":
        from app.tasks.analytics import generate_campaign_report
        return generate_campaign_report.delay(kwargs.get("campaign_id"), kwargs.get("report_subtype", "performance"))

    elif report_type == "kol":
        from app.tasks.analytics import generate_kol_performance_report
        return generate_kol_performance_report.delay(kwargs.get("kol_id"), kwargs.get("date_range"))

    elif report_type == "roi":
        from app.tasks.analytics import generate_roi_analysis
        return generate_roi_analysis.delay(kwargs.get("campaign_id"), kwargs.get("date_range"))

    else:
        raise ValueError(f"Unknown report type: {report_type}")


# Task execution helpers
def execute_maintenance_cycle():
    """
    Execute a complete maintenance cycle including cleanup and optimization.
    """
    from app.tasks.maintenance import (
        cleanup_old_results,
        optimize_database,
        backup_critical_data,
        monitor_system_health
    )

    # Schedule maintenance tasks
    tasks = [
        cleanup_old_results.delay(),
        optimize_database.delay(),
        backup_critical_data.delay(),
        monitor_system_health.delay()
    ]

    return {
        "scheduled_tasks": len(tasks),
        "task_ids": [task.id for task in tasks]
    }


def execute_daily_analytics_cycle():
    """
    Execute daily analytics processing cycle.
    """
    from app.tasks.analytics import (
        generate_daily_analytics,
        calculate_engagement_benchmarks,
        update_kol_performance_metrics
    )

    # Schedule analytics tasks
    tasks = [
        generate_daily_analytics.delay(),
        calculate_engagement_benchmarks.delay(),
        update_kol_performance_metrics.delay()
    ]

    return {
        "scheduled_tasks": len(tasks),
        "task_ids": [task.id for task in tasks]
    }


def execute_monitoring_cycle():
    """
    Execute comprehensive monitoring cycle.
    """
    from app.tasks.monitoring import (
        monitor_social_media_content,
        health_check,
        monitor_performance_alerts,
        generate_system_metrics
    )

    # Schedule monitoring tasks
    tasks = [
        monitor_social_media_content.delay(),
        health_check.delay(),
        monitor_performance_alerts.delay(),
        generate_system_metrics.delay()
    ]

    return {
        "scheduled_tasks": len(tasks),
        "task_ids": [task.id for task in tasks]
    }


# Queue management utilities
def purge_all_queues():
    """
    Purge all task queues (use with caution).
    """
    from app.tasks.celery_app import purge_queue

    queues = ["communication", "social_media", "campaigns", "analytics", "monitoring", "default"]
    results = {}

    for queue in queues:
        try:
            purged_count = purge_queue(queue)
            results[queue] = purged_count
        except Exception as e:
            results[queue] = f"Error: {str(e)}"

    return results


def get_queue_lengths():
    """
    Get current length of all task queues.
    """
    from app.tasks.celery_app import get_queue_length

    queues = ["communication", "social_media", "campaigns", "analytics", "monitoring", "default"]
    lengths = {}

    for queue in queues:
        try:
            length = get_queue_length(queue)
            lengths[queue] = length
        except Exception as e:
            lengths[queue] = f"Error: {str(e)}"

    return lengths


# Health check utilities
def check_task_system_health():
    """
    Check overall health of the task processing system.
    """
    from app.tasks.celery_app import get_celery_health

    try:
        celery_health = get_celery_health()
        queue_lengths = get_queue_lengths()
        task_status = get_task_status_summary()

        return {
            "celery_health": celery_health,
            "queue_lengths": queue_lengths,
            "task_status": task_status,
            "overall_status": "healthy" if celery_health.get("healthy", False) else "degraded"
        }

    except Exception as e:
        return {
            "error": str(e),
            "overall_status": "unhealthy"
        }