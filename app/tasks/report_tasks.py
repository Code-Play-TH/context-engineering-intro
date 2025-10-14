"""
Celery tasks for report generation.
"""
import asyncio
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.report_generation import GenerationStatus, ReportType
from app.services.report_generation_service import ReportGenerationService

# Create async engine for tasks
async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Create Celery app
celery_app = Celery(
    "report_generation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True, name='generate_report_task')
def generate_report_task(self, generation_id: int, campaign_id: int, template_id: int, report_type: str):
    """
    Background task to generate a report.
    
    Args:
        generation_id: Report generation ID
        campaign_id: Campaign ID
        template_id: Template ID
        report_type: Type of report ('powerpoint' or 'pdf')
    """
    return asyncio.run(_generate_report_async(
        self, generation_id, campaign_id, template_id, report_type
    ))


async def _generate_report_async(task, generation_id: int, campaign_id: int, template_id: int, report_type: str):
    """Async function to generate report."""
    async with AsyncSessionLocal() as session:
        service = ReportGenerationService(session)
        
        try:
            # Update status to processing
            await service.update_generation_status(
                generation_id, 
                GenerationStatus.PROCESSING
            )
            
            # Generate report
            report_type_enum = ReportType(report_type)
            file_path = await service.generate_report_sync(
                campaign_id, 
                template_id, 
                report_type_enum
            )
            
            # Generate download URL
            download_url = f"/api/v1/reports/{generation_id}/download"
            
            # Update status to completed
            await service.update_generation_status(
                generation_id,
                GenerationStatus.COMPLETED,
                file_path=file_path,
                download_url=download_url
            )
            
            return {
                'status': 'completed',
                'file_path': file_path,
                'download_url': download_url
            }
            
        except Exception as e:
            # Update status to failed
            await service.update_generation_status(
                generation_id,
                GenerationStatus.FAILED,
                error_message=str(e)
            )
            
            # Re-raise exception for Celery to handle
            raise


@celery_app.task(name='cleanup_expired_reports')
def cleanup_expired_reports_task():
    """Background task to clean up expired report files."""
    return asyncio.run(_cleanup_expired_reports_async())


async def _cleanup_expired_reports_async():
    """Async function to clean up expired reports."""
    from app.services.file_storage_service import file_storage_service
    
    async with AsyncSessionLocal() as session:
        service = ReportGenerationService(session)
        
        # Clean up expired reports from database
        cleaned_count = await service.cleanup_expired_reports()
        
        # Clean up old files from filesystem (older than 7 days)
        cleanup_result = file_storage_service.cleanup_old_files(
            directory_path="uploads/reports",
            max_age_days=7,
            file_patterns=['*.pdf', '*.pptx']
        )
        
        # Archive old files (older than 30 days) before cleanup
        archive_result = file_storage_service.archive_old_files(
            source_directory="uploads/reports",
            max_age_days=30,
            file_patterns=['*.pdf', '*.pptx']
        )
        
        return {
            'database_cleaned_files': cleaned_count,
            'filesystem_cleaned_files': cleanup_result.get('files_deleted', 0),
            'filesystem_space_freed_mb': cleanup_result.get('space_freed_mb', 0),
            'archived_files': archive_result.get('files_archived', 0)
        }


@celery_app.task(name='storage_maintenance')
def storage_maintenance_task():
    """Background task for storage maintenance and monitoring."""
    return asyncio.run(_storage_maintenance_async())


async def _storage_maintenance_async():
    """Async function for storage maintenance."""
    from app.services.file_storage_service import file_storage_service
    
    # Get storage statistics
    storage_stats = file_storage_service.get_storage_stats()
    
    # Get available disk space
    disk_space = file_storage_service.get_available_space()
    
    # Clean up very old archive files (older than 1 year)
    archive_cleanup = file_storage_service.cleanup_old_files(
        directory_path="uploads/archive",
        max_age_days=365
    )
    
    return {
        'storage_stats': storage_stats,
        'disk_space': disk_space,
        'archive_cleanup': archive_cleanup,
        'timestamp': datetime.utcnow().isoformat()
    }


# Periodic task configuration
celery_app.conf.beat_schedule = {
    'cleanup-expired-reports': {
        'task': 'cleanup_expired_reports',
        'schedule': 3600.0,  # Run every hour
    },
    'storage-maintenance': {
        'task': 'storage_maintenance',
        'schedule': 86400.0,  # Run daily
    },
}
celery_app.conf.timezone = 'UTC'