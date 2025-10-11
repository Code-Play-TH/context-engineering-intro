"""Performance tracking and manual refresh API endpoints."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, WebSocket, WebSocketDisconnect, Body
from sqlmodel import Session
import json
import asyncio

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.performance_tracking_service import PerformanceTrackingService
from app.services.permission_service import PermissionService
from app.schemas.performance import (
    RefreshRequest, BulkRefreshRequest, RefreshStatusResponse, RefreshResponse,
    MetricsResponse, HistoricalMetricsResponse, GrowthAnalyticsResponse,
    PerformanceIssuesResponse, BulkRefreshResponse, ActiveRefreshOperationsResponse,
    SystemStatusResponse, CleanupResponse
)
from app.core.config import settings

router = APIRouter(prefix="/performance", tags=["performance"])

# Platform configurations (in production, this would come from settings/database)
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


def get_performance_service(db: Session = Depends(get_session)) -> PerformanceTrackingService:
    """Get performance tracking service instance."""
    return PerformanceTrackingService(db, PLATFORM_CONFIGS)


def check_kol_permission(current_user: User, action: str = "read"):
    """Check if user has KOL permissions."""
    PermissionService.require_permission(current_user.role, "kols", action)


def check_admin_permission(current_user: User):
    """Check if user has admin permissions."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access system management"
        )


@router.post("/kols/{kol_id}/refresh", response_model=RefreshResponse)
async def manual_refresh_kol(
    kol_id: int,
    request: RefreshRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Trigger manual refresh for a KOL's performance metrics."""
    check_kol_permission(current_user, "update")
    
    try:
        result = await performance_service.manual_refresh_kol(
            kol_id=kol_id,
            platforms=request.platforms,
            include_posts=request.include_posts,
            user_id=current_user.id
        )
        
        return RefreshResponse(
            **result,
            triggered_by=current_user.email,
            triggered_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger refresh: {str(e)}"
        )


@router.get("/kols/{kol_id}/refresh/{refresh_id}/status", response_model=RefreshStatusResponse)
async def get_refresh_status(
    kol_id: int,
    refresh_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Get status of a refresh operation."""
    check_kol_permission(current_user, "read")
    
    try:
        status_data = await performance_service.get_refresh_status(refresh_id)
        
        # Verify the refresh belongs to the specified KOL
        if status_data["kol_id"] != kol_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh operation not found for this KOL"
            )
        
        return RefreshStatusResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get refresh status: {str(e)}"
        )


@router.get("/kols/{kol_id}/metrics", response_model=MetricsResponse)
async def get_kol_metrics(
    kol_id: int,
    platforms: Optional[List[str]] = Query(None, description="Filter by specific platforms"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Get latest performance metrics for a KOL."""
    check_kol_permission(current_user, "read")
    
    try:
        metrics = await performance_service.get_latest_metrics(kol_id, platforms)
        return MetricsResponse(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/kols/{kol_id}/metrics/historical")
async def get_historical_metrics(
    kol_id: int,
    platform: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of historical data"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Get historical performance metrics for a KOL on a specific platform."""
    check_kol_permission(current_user, "read")
    
    try:
        historical_data = await performance_service.get_historical_metrics(kol_id, platform, days)
        return historical_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get historical metrics: {str(e)}"
        )


@router.get("/kols/{kol_id}/analytics/growth")
async def get_growth_analytics(
    kol_id: int,
    platforms: Optional[List[str]] = Query(None, description="Filter by specific platforms"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Get growth analytics for a KOL."""
    check_kol_permission(current_user, "read")
    
    try:
        analytics = await performance_service.get_growth_analytics(kol_id, platforms)
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get growth analytics: {str(e)}"
        )


@router.get("/kols/{kol_id}/issues")
async def detect_performance_issues(
    kol_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Detect performance issues for a KOL."""
    check_kol_permission(current_user, "read")
    
    try:
        issues = await performance_service.detect_performance_issues(kol_id)
        return {
            "kol_id": kol_id,
            "issues": issues,
            "total_issues": len(issues),
            "critical_issues": len([i for i in issues if i.get("severity") == "high"]),
            "detected_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect issues: {str(e)}"
        )


@router.post("/kols/bulk-refresh")
async def bulk_refresh_kols(
    kol_ids: List[int],
    platforms: Optional[List[str]] = Query(None, description="Specific platforms to refresh"),
    include_posts: bool = Query(False, description="Include recent posts in refresh"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Trigger bulk refresh for multiple KOLs."""
    check_kol_permission(current_user, "update")
    
    if len(kol_ids) > 50:  # Limit bulk operations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 KOLs allowed per bulk refresh"
        )
    
    try:
        results = []
        for kol_id in kol_ids:
            try:
                result = await performance_service.manual_refresh_kol(
                    kol_id=kol_id,
                    platforms=platforms,
                    include_posts=include_posts,
                    user_id=current_user.id
                )
                results.append({
                    "kol_id": kol_id,
                    "success": True,
                    **result
                })
            except Exception as e:
                results.append({
                    "kol_id": kol_id,
                    "success": False,
                    "error": str(e)
                })
        
        successful = len([r for r in results if r["success"]])
        
        return {
            "total_kols": len(kol_ids),
            "successful": successful,
            "failed": len(kol_ids) - successful,
            "results": results,
            "triggered_by": current_user.email,
            "triggered_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger bulk refresh: {str(e)}"
        )


@router.websocket("/kols/{kol_id}/refresh/{refresh_id}/ws")
async def refresh_status_websocket(
    websocket: WebSocket,
    kol_id: int,
    refresh_id: str,
    db: Session = Depends(get_session)
):
    """WebSocket endpoint for real-time refresh status updates."""
    await websocket.accept()
    
    try:
        performance_service = PerformanceTrackingService(db, PLATFORM_CONFIGS)
        
        while True:
            try:
                # Get current status
                status_data = await performance_service.get_refresh_status(refresh_id)
                
                # Verify the refresh belongs to the specified KOL
                if status_data["kol_id"] != kol_id:
                    await websocket.send_text(json.dumps({
                        "error": "Refresh operation not found for this KOL"
                    }))
                    break
                
                # Send status update
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "data": status_data
                }))
                
                # If completed or failed, send final update and close
                if status_data["status"] in ["completed", "failed", "rate_limited"]:
                    await websocket.send_text(json.dumps({
                        "type": "final_update",
                        "data": status_data
                    }))
                    break
                
                # Wait before next update
                await asyncio.sleep(2)
                
            except HTTPException as e:
                await websocket.send_text(json.dumps({
                    "error": e.detail
                }))
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "error": f"Unexpected error: {str(e)}"
                }))
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "error": f"WebSocket error: {str(e)}"
            }))
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("/refresh-operations")
async def list_active_refresh_operations(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """List all active refresh operations (admin only)."""
    check_admin_permission(current_user)
    
    try:
        # Get all active refresh operations
        active_operations = []
        for refresh_id, refresh_status in performance_service._refresh_operations.items():
            if refresh_status.status in ["in_progress", "scraping_metrics", "scraping_posts", "analyzing"]:
                active_operations.append({
                    "refresh_id": refresh_id,
                    "kol_id": refresh_status.kol_id,
                    "status": refresh_status.status,
                    "progress": refresh_status.progress,
                    "platforms": refresh_status.platforms,
                    "started_at": refresh_status.started_at,
                    "duration_seconds": (datetime.utcnow() - refresh_status.started_at).total_seconds()
                })
        
        return {
            "active_operations": active_operations,
            "total_active": len(active_operations),
            "retrieved_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list refresh operations: {str(e)}"
        )


@router.post("/refresh-operations/cleanup")
async def cleanup_old_refresh_operations(
    hours: int = Query(24, ge=1, le=168, description="Age in hours for cleanup"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Clean up old refresh operations from memory (admin only)."""
    check_admin_permission(current_user)
    
    try:
        cleaned_count = await performance_service.cleanup_old_refresh_operations(hours)
        
        return {
            "success": True,
            "cleaned_operations": cleaned_count,
            "cleanup_threshold_hours": hours,
            "cleaned_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup operations: {str(e)}"
        )


@router.get("/system/status")
async def get_system_status(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceTrackingService = Depends(get_performance_service)
):
    """Get overall performance tracking system status."""
    check_admin_permission(current_user)
    
    try:
        # Get scraping system status
        scraping_status = await performance_service.scraping_service.get_scraping_status()
        
        # Get active refresh operations count
        active_refreshes = len([
            op for op in performance_service._refresh_operations.values()
            if op.status in ["in_progress", "scraping_metrics", "scraping_posts", "analyzing"]
        ])
        
        return {
            "system_status": "operational",
            "timestamp": datetime.utcnow(),
            "scraping_system": scraping_status,
            "active_refresh_operations": active_refreshes,
            "platform_configs": list(PLATFORM_CONFIGS.keys()),
            "rate_limit_status": await performance_service.rate_limit_manager.get_all_limits()
        }
        
    except Exception as e:
        return {
            "system_status": "degraded",
            "timestamp": datetime.utcnow(),
            "error": str(e),
            "platform_configs": list(PLATFORM_CONFIGS.keys())
        }