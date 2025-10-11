"""Celery tasks for KOL scraping operations."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import Task
from sqlmodel import Session, create_engine, select
import logging

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_session
from app.services.scraping_scheduler import ScrapingScheduler
from app.services.scraping_service import ScrapingService
from app.models.scraping_schedule import ScrapingSchedule
from app.models.kol_metrics import KOLMetrics
from app.models.performance_alert import PerformanceAlert

logger = logging.getLogger(__name__)

# Platform configurations for tasks
PLATFORM_CONFIGS = {
    "instagram": {
        "app_id": "test_app_id",
        "app_secret": "test_secret",
        "access_token": "test_token"
    },
    "tiktok": {
        "app_id": "test_app_id",
        "app_secret": "test_secret",
        "access_token": "test_token"
    },
    "youtube": {
        "api_key": "test_key",
        "client_id": "test_client_id",
        "client_secret": "test_secret"
    },
    "twitter": {
        "api_key": "test_key",
        "api_secret": "test_secret",
        "bearer_token": "test_token"
    },
    "facebook": {
        "app_id": "test_app_id",
        "app_secret": "test_secret",
        "access_token": "test_token"
    }
}


class DatabaseTask(Task):
    """Base task class that provides database session."""
    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(str(settings.DATABASE_URL))
        return self._engine

    def get_db(self) -> Session:
        """Get database session."""
        return Session(self.engine)


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.process_due_schedules")
def process_due_schedules(self) -> Dict[str, Any]:
    """Process all schedules that are due for scraping."""
    try:
        with self.get_db() as db:
            scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(scheduler.process_due_schedules())
                return result
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error in process_due_schedules task: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.scrape_single_kol")
def scrape_single_kol(self, kol_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    """Scrape metrics for a single KOL."""
    try:
        with self.get_db() as db:
            scraping_service = ScrapingService(db, PLATFORM_CONFIGS)
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    scraping_service.scrape_kol_metrics(kol_id, force_refresh)
                )
                return result
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error scraping KOL {kol_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "kol_id": kol_id,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.bulk_scrape_kols")
def bulk_scrape_kols(self, kol_ids: List[int], force_refresh: bool = False) -> Dict[str, Any]:
    """Scrape metrics for multiple KOLs."""
    try:
        with self.get_db() as db:
            scraping_service = ScrapingService(db, PLATFORM_CONFIGS)
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = []
                for kol_id in kol_ids:
                    result = loop.run_until_complete(
                        scraping_service.scrape_kol_metrics(kol_id, force_refresh)
                    )
                    results.append(result)
                
                successful = sum(1 for r in results if r.get("success", False))
                return {
                    "success": True,
                    "total": len(kol_ids),
                    "successful": successful,
                    "failed": len(kol_ids) - successful,
                    "results": results,
                    "timestamp": datetime.utcnow().isoformat()
                }
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error in bulk scrape: {e}")
        return {
            "success": False,
            "error": str(e),
            "total": len(kol_ids),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.create_scraping_schedule")
def create_scraping_schedule(
    self, 
    kol_id: int, 
    interval: str, 
    priority: int = 5,
    custom_cron: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new scraping schedule for a KOL."""
    try:
        with self.get_db() as db:
            scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from app.models.scraping_schedule import ScrapingInterval
                schedule = loop.run_until_complete(
                    scheduler.create_schedule(
                        kol_id=kol_id,
                        interval=ScrapingInterval(interval),
                        priority=priority,
                        custom_cron=custom_cron
                    )
                )
                return {
                    "success": True,
                    "schedule_id": schedule.id,
                    "kol_id": kol_id,
                    "interval": interval,
                    "next_scrape_at": schedule.next_scrape_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error creating schedule for KOL {kol_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "kol_id": kol_id,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.cleanup_old_data")
def cleanup_old_data(self, days: int = 90) -> Dict[str, Any]:
    """Clean up old metrics and alert data."""
    try:
        with self.get_db() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean up old metrics
            old_metrics = db.exec(
                select(KOLMetrics).where(KOLMetrics.scraped_at < cutoff_date)
            ).all()
            metrics_count = len(old_metrics)
            
            for metric in old_metrics:
                db.delete(metric)
            
            # Clean up old alerts
            old_alerts = db.exec(
                select(PerformanceAlert).where(PerformanceAlert.created_at < cutoff_date)
            ).all()
            alerts_count = len(old_alerts)
            
            for alert in old_alerts:
                db.delete(alert)
            
            db.commit()
            
            logger.info(f"Cleaned up {metrics_count} old metrics and {alerts_count} old alerts")
            
            return {
                "success": True,
                "metrics_cleaned": metrics_count,
                "alerts_cleaned": alerts_count,
                "cutoff_date": cutoff_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.health_check")
def health_check(self) -> Dict[str, Any]:
    """Health check task to monitor system status."""
    try:
        with self.get_db() as db:
            scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                status = loop.run_until_complete(scheduler.get_scheduler_status())
                
                # Add additional health metrics
                status.update({
                    "celery_worker_active": True,
                    "database_connected": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return status
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "celery_worker_active": True,
            "database_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.scraping_tasks.update_schedule_priorities")
def update_schedule_priorities(self) -> Dict[str, Any]:
    """Update schedule priorities based on campaign activity."""
    try:
        with self.get_db() as db:
            # Get active campaigns
            from app.models.campaign import Campaign
            from app.models.brief import Brief
            
            active_campaigns = db.exec(
                select(Campaign).where(
                    Campaign.status.in_(["active", "running"])
                )
            ).all()
            
            updated_count = 0
            
            # Increase priority for KOLs in active campaigns
            for campaign in active_campaigns:
                briefs = db.exec(
                    select(Brief).where(Brief.campaign_id == campaign.id)
                ).all()
                
                for brief in briefs:
                    schedule = db.exec(
                        select(ScrapingSchedule).where(
                            ScrapingSchedule.kol_id == brief.kol_id
                        )
                    ).first()
                    
                    if schedule and schedule.priority < 8:
                        schedule.priority = min(schedule.priority + 2, 10)
                        db.add(schedule)
                        updated_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "updated_schedules": updated_count,
                "active_campaigns": len(active_campaigns),
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error updating schedule priorities: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }