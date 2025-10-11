"""Rate limit monitoring and management API endpoints."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.rate_limit_manager import RateLimitManager

router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])


def check_admin_permission(current_user: User):
    """Check if user has admin permissions."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access rate limit management"
        )


@router.get("/status")
async def get_all_rate_limit_status(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get rate limit status for all platforms."""
    check_admin_permission(current_user)
    
    rate_limit_manager = RateLimitManager(db)
    status_data = await rate_limit_manager.get_all_rate_limits()
    
    return {
        "rate_limits": status_data,
        "timestamp": datetime.utcnow(),
        "total_platforms": len(set(data["platform"] for data in status_data.values()))
    }


@router.get("/health")
async def get_rate_limit_health(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get overall rate limit system health."""
    check_admin_permission(current_user)
    
    rate_limit_manager = RateLimitManager(db)
    
    # Get all rate limits
    all_limits = await rate_limit_manager.get_all_rate_limits()
    
    # Get queue status
    queue_status = await rate_limit_manager.get_queue_status()
    
    # Calculate health metrics
    total_platforms = len(set(data["platform"] for data in all_limits.values()))
    exceeded_limits = sum(1 for data in all_limits.values() if data["status"] == "exceeded")
    warning_limits = sum(1 for data in all_limits.values() if data["usage_percentage"] > 80)
    total_queued = sum(q["queue_length"] for q in queue_status.values())
    
    # Determine overall health
    if exceeded_limits > 0:
        health_status = "critical"
    elif warning_limits > total_platforms * 0.5:  # More than 50% in warning
        health_status = "warning"
    elif total_queued > 100:  # Too many queued requests
        health_status = "warning"
    else:
        health_status = "healthy"
    
    return {
        "health_status": health_status,
        "metrics": {
            "total_platforms": total_platforms,
            "exceeded_limits": exceeded_limits,
            "warning_limits": warning_limits,
            "total_queued_requests": total_queued,
            "active_queues": len(queue_status)
        },
        "platforms": {
            platform_data["platform"]: {
                "status": platform_data["status"],
                "usage_percentage": platform_data["usage_percentage"],
                "requests_remaining": platform_data["requests_remaining"]
            }
            for platform_data in all_limits.values()
        },
        "timestamp": datetime.utcnow()
    }