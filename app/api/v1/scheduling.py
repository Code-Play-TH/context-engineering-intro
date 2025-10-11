"""API endpoints for KOL scraping scheduling and distribution."""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from pydantic import BaseModel

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.scraping_scheduler import ScrapingScheduler
from app.services.smart_distribution import SmartDistributionAlgorithm, DistributionStrategy
from app.models.scraping_schedule import ScrapingInterval
from app.tasks.scraping_tasks import process_due_schedules, create_scraping_schedule

router = APIRouter(prefix="/scheduling", tags=["scheduling"])

# Platform configurations
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


class CreateScheduleRequest(BaseModel):
    """Request model for creating a scraping schedule."""
    kol_id: int
    interval: ScrapingInterval
    priority: int = 5
    custom_cron: Optional[str] = None
    is_active: bool = True


class UpdateScheduleRequest(BaseModel):
    """Request model for updating a scraping schedule."""
    interval: Optional[ScrapingInterval] = None
    priority: Optional[int] = None
    custom_cron: Optional[str] = None
    is_active: Optional[bool] = None


class BulkScheduleRequest(BaseModel):
    """Request model for bulk schedule creation."""
    kol_ids: List[int]
    interval: ScrapingInterval = ScrapingInterval.DAILY
    priority: int = 5


class DistributionRequest(BaseModel):
    """Request model for smart distribution."""
    strategy: DistributionStrategy = DistributionStrategy.CAMPAIGN_AWARE
    target_date: Optional[datetime] = None
    max_kols: Optional[int] = None


@router.post("/schedules", response_model=Dict[str, Any])
async def create_schedule(
    request: CreateScheduleRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new scraping schedule for a KOL."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    try:
        schedule = await scheduler.create_schedule(
            kol_id=request.kol_id,
            interval=request.interval,
            priority=request.priority,
            custom_cron=request.custom_cron,
            is_active=request.is_active
        )
        
        return {
            "success": True,
            "schedule": {
                "id": schedule.id,
                "kol_id": schedule.kol_id,
                "interval": schedule.interval,
                "priority": schedule.priority,
                "is_active": schedule.is_active,
                "next_scrape_at": schedule.next_scrape_at.isoformat(),
                "created_at": schedule.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/schedules", response_model=Dict[str, Any])
async def list_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    priority_min: Optional[int] = Query(None, ge=1, le=10),
    kol_id: Optional[int] = Query(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List scraping schedules with filters."""
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    schedules, total = await scheduler.list_schedules(
        skip=skip,
        limit=limit,
        is_active=is_active,
        priority_min=priority_min,
        kol_id=kol_id
    )
    
    return {
        "success": True,
        "total": total,
        "schedules": [
            {
                "id": schedule.id,
                "kol_id": schedule.kol_id,
                "interval": schedule.interval,
                "priority": schedule.priority,
                "is_active": schedule.is_active,
                "next_scrape_at": schedule.next_scrape_at.isoformat(),
                "consecutive_failures": schedule.consecutive_failures,
                "last_success_at": schedule.last_success_at.isoformat() if schedule.last_success_at else None,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]
    }


@router.get("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific scraping schedule."""
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    schedule = await scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return {
        "success": True,
        "schedule": {
            "id": schedule.id,
            "kol_id": schedule.kol_id,
            "interval": schedule.interval,
            "priority": schedule.priority,
            "custom_cron": schedule.custom_cron,
            "is_active": schedule.is_active,
            "next_scrape_at": schedule.next_scrape_at.isoformat(),
            "consecutive_failures": schedule.consecutive_failures,
            "max_failures": schedule.max_failures,
            "last_success_at": schedule.last_success_at.isoformat() if schedule.last_success_at else None,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat()
        }
    }


@router.put("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def update_schedule(
    schedule_id: int,
    request: UpdateScheduleRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a scraping schedule."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    try:
        schedule = await scheduler.update_schedule(
            schedule_id=schedule_id,
            interval=request.interval,
            priority=request.priority,
            custom_cron=request.custom_cron,
            is_active=request.is_active
        )
        
        return {
            "success": True,
            "schedule": {
                "id": schedule.id,
                "kol_id": schedule.kol_id,
                "interval": schedule.interval,
                "priority": schedule.priority,
                "is_active": schedule.is_active,
                "next_scrape_at": schedule.next_scrape_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a scraping schedule."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    try:
        await scheduler.delete_schedule(schedule_id)
        return {"success": True, "message": "Schedule deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/schedules/bulk", response_model=Dict[str, Any])
async def bulk_create_schedules(
    request: BulkScheduleRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create schedules for multiple KOLs."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    result = await scheduler.bulk_create_schedules(
        kol_ids=request.kol_ids,
        interval=request.interval,
        priority=request.priority
    )
    
    return {
        "success": True,
        "created": result["created"],
        "failed": result["failed"],
        "total": result["total"],
        "errors": result["errors"]
    }


@router.post("/schedules/{schedule_id}/pause", response_model=Dict[str, Any])
async def pause_schedule(
    schedule_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Pause a scraping schedule."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    try:
        schedule = await scheduler.pause_schedule(schedule_id)
        return {
            "success": True,
            "message": "Schedule paused",
            "schedule": {
                "id": schedule.id,
                "is_active": schedule.is_active,
                "updated_at": schedule.updated_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/schedules/{schedule_id}/resume", response_model=Dict[str, Any])
async def resume_schedule(
    schedule_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Resume a paused scraping schedule."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    try:
        schedule = await scheduler.resume_schedule(schedule_id)
        return {
            "success": True,
            "message": "Schedule resumed",
            "schedule": {
                "id": schedule.id,
                "is_active": schedule.is_active,
                "next_scrape_at": schedule.next_scrape_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_scheduler_status(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get current scheduler status and statistics."""
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    status = await scheduler.get_scheduler_status()
    return {
        "success": True,
        "status": status
    }


@router.post("/process", response_model=Dict[str, Any])
async def trigger_processing(
    current_user: User = Depends(get_current_user)
):
    """Manually trigger processing of due schedules."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Trigger Celery task
    task = process_due_schedules.delay()
    
    return {
        "success": True,
        "message": "Processing triggered",
        "task_id": task.id
    }


@router.post("/distribution/preview", response_model=Dict[str, Any])
async def preview_distribution(
    request: DistributionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Preview smart distribution without applying changes."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    algorithm = SmartDistributionAlgorithm(db)
    
    preview = algorithm.get_distribution_preview(
        strategy=request.strategy,
        target_date=request.target_date,
        max_kols=request.max_kols
    )
    
    return preview


@router.post("/distribution/apply", response_model=Dict[str, Any])
async def apply_distribution(
    request: DistributionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Apply smart distribution to KOL schedules."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    algorithm = SmartDistributionAlgorithm(db)
    
    result = algorithm.distribute_kols(
        strategy=request.strategy,
        target_date=request.target_date,
        max_kols=request.max_kols
    )
    
    return result


@router.get("/distribution/strategies", response_model=Dict[str, Any])
async def get_distribution_strategies(
    current_user: User = Depends(get_current_user)
):
    """Get available distribution strategies."""
    return {
        "success": True,
        "strategies": [
            {
                "value": DistributionStrategy.EVEN,
                "label": "Even Distribution",
                "description": "Distribute KOLs evenly across all time slots"
            },
            {
                "value": DistributionStrategy.PRIORITY_FIRST,
                "label": "Priority First",
                "description": "Process highest priority KOLs first"
            },
            {
                "value": DistributionStrategy.CAMPAIGN_AWARE,
                "label": "Campaign Aware",
                "description": "Prioritize KOLs in active campaigns"
            },
            {
                "value": DistributionStrategy.LOAD_BALANCED,
                "label": "Load Balanced",
                "description": "Balance load across worker capacity"
            }
        ]
    }


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_schedules(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Clean up orphaned schedules."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    scheduler = ScrapingScheduler(db, PLATFORM_CONFIGS)
    
    cleaned_count = await scheduler.cleanup_old_schedules(days)
    
    return {
        "success": True,
        "cleaned_schedules": cleaned_count,
        "message": f"Cleaned up {cleaned_count} orphaned schedules"
    }