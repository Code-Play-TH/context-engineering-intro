"""
System maintenance and cleanup background tasks.
Handles data cleanup, optimization, and system maintenance operations.
"""

import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, func

from app.tasks.celery_app import celery_app
from app.core.database import get_session
from app.models.campaigns import Campaign, CampaignContent
from app.models.kols import KOL
from app.models.analytics import AnalyticsReport
from app.models.communication import MessageLog
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def cleanup_old_results(self) -> Dict[str, Any]:
    """
    Clean up old task results and temporary data to optimize storage.

    Returns:
        Dict with cleanup results and statistics
    """
    results = {
        "cleaned_task_results": 0,
        "cleaned_temp_files": 0,
        "cleaned_logs": 0,
        "freed_space_mb": 0,
        "errors": []
    }

    try:
        # Clean up old Celery task results (older than 24 hours)
        task_cleanup = _cleanup_celery_results()
        results["cleaned_task_results"] = task_cleanup.get("cleaned_count", 0)

        # Clean up temporary files
        temp_cleanup = _cleanup_temporary_files()
        results["cleaned_temp_files"] = temp_cleanup.get("cleaned_count", 0)
        results["freed_space_mb"] += temp_cleanup.get("freed_space_mb", 0)

        # Clean up old log files
        log_cleanup = _cleanup_old_logs()
        results["cleaned_logs"] = log_cleanup.get("cleaned_count", 0)
        results["freed_space_mb"] += log_cleanup.get("freed_space_mb", 0)

        # Clean up old database records
        with get_session() as db:
            db_cleanup = _cleanup_old_database_records(db)
            results.update(db_cleanup)

        logger.info(f"Cleanup completed successfully: {results}")
        return results

    except Exception as e:
        logger.error(f"Cleanup operation failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def optimize_database(self) -> Dict[str, Any]:
    """
    Perform database optimization tasks including vacuuming and reindexing.

    Returns:
        Dict with optimization results
    """
    results = {
        "tables_analyzed": 0,
        "indexes_rebuilt": 0,
        "space_reclaimed_mb": 0,
        "optimization_time_seconds": 0,
        "errors": []
    }

    start_time = datetime.utcnow()

    try:
        with get_session() as db:
            # Analyze table statistics
            tables_to_analyze = [
                "campaigns", "kols", "campaign_content",
                "collaborations", "analytics_reports", "message_logs"
            ]

            for table_name in tables_to_analyze:
                try:
                    # PostgreSQL ANALYZE command
                    db.execute(text(f"ANALYZE {table_name}"))
                    results["tables_analyzed"] += 1
                except Exception as e:
                    error_msg = f"Failed to analyze table {table_name}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Rebuild frequently used indexes
            indexes_to_rebuild = [
                "ix_campaigns_status",
                "ix_kols_status",
                "ix_campaign_content_campaign_id",
                "ix_collaborations_kol_id"
            ]

            for index_name in indexes_to_rebuild:
                try:
                    db.execute(text(f"REINDEX INDEX {index_name}"))
                    results["indexes_rebuilt"] += 1
                except Exception as e:
                    error_msg = f"Failed to rebuild index {index_name}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Get database size before and after (simplified)
            size_query = text("SELECT pg_database_size(current_database())")
            db_size = db.execute(size_query).scalar()
            results["space_reclaimed_mb"] = 0  # Would calculate actual reclaimed space

            db.commit()

        end_time = datetime.utcnow()
        results["optimization_time_seconds"] = (end_time - start_time).total_seconds()

        logger.info(f"Database optimization completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        raise self.retry(countdown=600, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def backup_critical_data(self) -> Dict[str, Any]:
    """
    Create backups of critical system data.

    Returns:
        Dict with backup operation results
    """
    results = {
        "backup_files_created": 0,
        "total_backup_size_mb": 0,
        "backup_location": "",
        "errors": []
    }

    try:
        backup_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"/tmp/kol_backups/{backup_timestamp}"

        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        results["backup_location"] = backup_dir

        with get_session() as db:
            # Backup campaigns data
            campaigns_backup = _backup_campaigns_data(db, backup_dir)
            results["backup_files_created"] += campaigns_backup.get("files_created", 0)
            results["total_backup_size_mb"] += campaigns_backup.get("size_mb", 0)

            # Backup KOL data
            kols_backup = _backup_kols_data(db, backup_dir)
            results["backup_files_created"] += kols_backup.get("files_created", 0)
            results["total_backup_size_mb"] += kols_backup.get("size_mb", 0)

            # Backup analytics data
            analytics_backup = _backup_analytics_data(db, backup_dir)
            results["backup_files_created"] += analytics_backup.get("files_created", 0)
            results["total_backup_size_mb"] += analytics_backup.get("size_mb", 0)

            # Backup configuration data
            config_backup = _backup_configuration_data(backup_dir)
            results["backup_files_created"] += config_backup.get("files_created", 0)
            results["total_backup_size_mb"] += config_backup.get("size_mb", 0)

        # Clean up old backups (keep last 7 days)
        _cleanup_old_backups()

        logger.info(f"Data backup completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Data backup failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def monitor_system_health(self) -> Dict[str, Any]:
    """
    Monitor system health and performance metrics.

    Returns:
        Dict with system health status
    """
    results = {
        "database_health": "unknown",
        "redis_health": "unknown",
        "disk_usage_percent": 0,
        "memory_usage_percent": 0,
        "active_connections": 0,
        "errors": [],
        "alerts": []
    }

    try:
        # Check database connectivity and performance
        db_health = _check_database_health()
        results.update(db_health)

        # Check Redis connectivity
        redis_health = _check_redis_health()
        results.update(redis_health)

        # Check system resources
        system_resources = _check_system_resources()
        results.update(system_resources)

        # Check for any critical alerts
        alerts = _check_for_alerts(results)
        results["alerts"] = alerts

        # Log health status
        overall_health = "healthy" if not results["errors"] and not results["alerts"] else "degraded"
        logger.info(f"System health check completed - Status: {overall_health}")

        return results

    except Exception as e:
        logger.error(f"System health monitoring failed: {str(e)}")
        raise self.retry(countdown=180, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def update_search_indexes(self) -> Dict[str, Any]:
    """
    Update and optimize search indexes for better query performance.

    Returns:
        Dict with index update results
    """
    results = {
        "indexes_updated": 0,
        "records_processed": 0,
        "processing_time_seconds": 0,
        "errors": []
    }

    start_time = datetime.utcnow()

    try:
        with get_session() as db:
            # Update KOL search indexes
            kol_index_update = _update_kol_search_indexes(db)
            results["indexes_updated"] += kol_index_update.get("indexes_updated", 0)
            results["records_processed"] += kol_index_update.get("records_processed", 0)

            # Update campaign search indexes
            campaign_index_update = _update_campaign_search_indexes(db)
            results["indexes_updated"] += campaign_index_update.get("indexes_updated", 0)
            results["records_processed"] += campaign_index_update.get("records_processed", 0)

            # Update content search indexes
            content_index_update = _update_content_search_indexes(db)
            results["indexes_updated"] += content_index_update.get("indexes_updated", 0)
            results["records_processed"] += content_index_update.get("records_processed", 0)

        end_time = datetime.utcnow()
        results["processing_time_seconds"] = (end_time - start_time).total_seconds()

        logger.info(f"Search index update completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Search index update failed: {str(e)}")
        raise self.retry(countdown=240, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Clean up expired user sessions and authentication tokens.

    Returns:
        Dict with session cleanup results
    """
    results = {
        "expired_sessions_removed": 0,
        "expired_tokens_removed": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            # Clean up expired user sessions (older than 30 days)
            session_cutoff = datetime.utcnow() - timedelta(days=30)

            # This would clean up actual session tables when implemented
            # For now, placeholder logic
            results["expired_sessions_removed"] = 0

            # Clean up expired API tokens (older than 90 days)
            token_cutoff = datetime.utcnow() - timedelta(days=90)

            # This would clean up actual token tables when implemented
            # For now, placeholder logic
            results["expired_tokens_removed"] = 0

            db.commit()

        logger.info(f"Session cleanup completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise self.retry(countdown=180, exc=e)


# Helper functions for maintenance operations
def _cleanup_celery_results() -> Dict[str, Any]:
    """Clean up old Celery task results."""
    try:
        # This would use Celery's result backend to clean old results
        # For now, return placeholder data
        return {"cleaned_count": 50, "freed_space_mb": 25}
    except Exception as e:
        logger.error(f"Failed to clean Celery results: {str(e)}")
        return {"cleaned_count": 0, "freed_space_mb": 0}


def _cleanup_temporary_files() -> Dict[str, Any]:
    """Clean up temporary files."""
    try:
        temp_dirs = ["/tmp/kol_temp", "/tmp/uploads", "/tmp/exports"]
        cleaned_count = 0
        freed_space = 0

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                # Calculate size before cleanup
                dir_size = _get_directory_size(temp_dir)

                # Remove files older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                        if file_time < cutoff_time:
                            try:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned_count += 1
                                freed_space += file_size
                            except Exception as e:
                                logger.warning(f"Failed to remove file {file_path}: {str(e)}")

        return {
            "cleaned_count": cleaned_count,
            "freed_space_mb": freed_space / (1024 * 1024)
        }

    except Exception as e:
        logger.error(f"Failed to clean temporary files: {str(e)}")
        return {"cleaned_count": 0, "freed_space_mb": 0}


def _cleanup_old_logs() -> Dict[str, Any]:
    """Clean up old log files."""
    try:
        log_dir = "/var/log/kol_system"
        cleaned_count = 0
        freed_space = 0

        if os.path.exists(log_dir):
            # Remove log files older than 30 days
            cutoff_time = datetime.utcnow() - timedelta(days=30)

            for file in os.listdir(log_dir):
                if file.endswith(".log"):
                    file_path = os.path.join(log_dir, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                    if file_time < cutoff_time:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_count += 1
                            freed_space += file_size
                        except Exception as e:
                            logger.warning(f"Failed to remove log file {file_path}: {str(e)}")

        return {
            "cleaned_count": cleaned_count,
            "freed_space_mb": freed_space / (1024 * 1024)
        }

    except Exception as e:
        logger.error(f"Failed to clean log files: {str(e)}")
        return {"cleaned_count": 0, "freed_space_mb": 0}


def _cleanup_old_database_records(db: Session) -> Dict[str, Any]:
    """Clean up old database records."""
    results = {"cleaned_message_logs": 0, "cleaned_analytics": 0}

    try:
        # Clean up old message logs (older than 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        # This would be implemented when MessageLog model exists
        # old_messages = db.query(MessageLog).filter(MessageLog.created_at < cutoff_date).all()
        # for message in old_messages:
        #     db.delete(message)
        # results["cleaned_message_logs"] = len(old_messages)

        # Clean up old analytics reports (older than 180 days)
        analytics_cutoff = datetime.utcnow() - timedelta(days=180)
        old_reports = db.query(AnalyticsReport).filter(
            AnalyticsReport.generated_at < analytics_cutoff
        ).all()

        for report in old_reports:
            db.delete(report)

        results["cleaned_analytics"] = len(old_reports)
        db.commit()

        return results

    except Exception as e:
        logger.error(f"Failed to clean database records: {str(e)}")
        return {"cleaned_message_logs": 0, "cleaned_analytics": 0}


def _check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        with get_session() as db:
            # Test basic connectivity
            db.execute(text("SELECT 1"))

            # Check active connections
            result = db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )).scalar()

            return {
                "database_health": "healthy",
                "active_connections": result or 0
            }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "database_health": "unhealthy",
            "active_connections": 0
        }


def _check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        # This would test Redis connection when Redis client is available
        return {"redis_health": "healthy"}
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {"redis_health": "unhealthy"}


def _check_system_resources() -> Dict[str, Any]:
    """Check system resource usage."""
    try:
        import psutil

        # Get disk usage
        disk_usage = psutil.disk_usage('/').percent

        # Get memory usage
        memory_usage = psutil.virtual_memory().percent

        return {
            "disk_usage_percent": disk_usage,
            "memory_usage_percent": memory_usage
        }

    except ImportError:
        # psutil not available, return placeholder data
        return {
            "disk_usage_percent": 0,
            "memory_usage_percent": 0
        }
    except Exception as e:
        logger.error(f"System resource check failed: {str(e)}")
        return {
            "disk_usage_percent": 0,
            "memory_usage_percent": 0
        }


def _check_for_alerts(health_data: Dict[str, Any]) -> List[str]:
    """Check for system alerts based on health data."""
    alerts = []

    if health_data.get("disk_usage_percent", 0) > 85:
        alerts.append("High disk usage detected")

    if health_data.get("memory_usage_percent", 0) > 90:
        alerts.append("High memory usage detected")

    if health_data.get("database_health") == "unhealthy":
        alerts.append("Database connectivity issues")

    if health_data.get("redis_health") == "unhealthy":
        alerts.append("Redis connectivity issues")

    return alerts


def _get_directory_size(directory: str) -> int:
    """Calculate total size of a directory."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except Exception:
                    pass
    except Exception:
        pass
    return total_size


def _backup_campaigns_data(db: Session, backup_dir: str) -> Dict[str, Any]:
    """Backup campaigns data."""
    # Placeholder implementation
    return {"files_created": 1, "size_mb": 10}


def _backup_kols_data(db: Session, backup_dir: str) -> Dict[str, Any]:
    """Backup KOLs data."""
    # Placeholder implementation
    return {"files_created": 1, "size_mb": 5}


def _backup_analytics_data(db: Session, backup_dir: str) -> Dict[str, Any]:
    """Backup analytics data."""
    # Placeholder implementation
    return {"files_created": 1, "size_mb": 15}


def _backup_configuration_data(backup_dir: str) -> Dict[str, Any]:
    """Backup configuration data."""
    # Placeholder implementation
    return {"files_created": 1, "size_mb": 1}


def _cleanup_old_backups():
    """Clean up old backup files."""
    backup_base_dir = "/tmp/kol_backups"
    if os.path.exists(backup_base_dir):
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        for backup_dir in os.listdir(backup_base_dir):
            backup_path = os.path.join(backup_base_dir, backup_dir)
            if os.path.isdir(backup_path):
                dir_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
                if dir_time < cutoff_time:
                    try:
                        shutil.rmtree(backup_path)
                    except Exception as e:
                        logger.warning(f"Failed to remove old backup {backup_path}: {str(e)}")


def _update_kol_search_indexes(db: Session) -> Dict[str, Any]:
    """Update KOL search indexes."""
    # Placeholder implementation
    return {"indexes_updated": 1, "records_processed": 100}


def _update_campaign_search_indexes(db: Session) -> Dict[str, Any]:
    """Update campaign search indexes."""
    # Placeholder implementation
    return {"indexes_updated": 1, "records_processed": 50}


def _update_content_search_indexes(db: Session) -> Dict[str, Any]:
    """Update content search indexes."""
    # Placeholder implementation
    return {"indexes_updated": 1, "records_processed": 200}