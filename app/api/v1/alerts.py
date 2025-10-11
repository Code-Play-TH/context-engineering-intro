"""API endpoints for performance alert management."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.performance_alert import AlertType, AlertSeverity
from app.services.performance_alert_service import PerformanceAlertService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/alerts", tags=["alerts"])


class CreateAlertRequest(BaseModel):
    """Request model for creating alerts."""
    kol_id: int
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    actual_value: Optional[float] = None
    previous_value: Optional[float] = None
    threshold_value: Optional[float] = None
    context_data: Optional[Dict[str, Any]] = None
    auto_notify: bool = True


class AcknowledgeAlertRequest(BaseModel):
    """Request model for acknowledging alerts."""
    acknowledgment_note: Optional[str] = None


class BulkAcknowledgeRequest(BaseModel):
    """Request model for bulk acknowledging alerts."""
    alert_ids: List[int] = Field(..., min_items=1, max_items=100)
    acknowledgment_note: Optional[str] = None


class AlertThresholdsRequest(BaseModel):
    """Request model for configuring alert thresholds."""
    kol_id: Optional[int] = None
    campaign_id: Optional[int] = None
    thresholds: Dict[str, float]


def check_alert_permission(current_user: User, action: str = "read"):
    """Check if user has alert permissions."""
    PermissionService.require_permission(current_user.role, "alerts", action)


def get_alert_service(db: Session = Depends(get_session)) -> PerformanceAlertService:
    """Get performance alert service instance."""
    return PerformanceAlertService(db)


@router.post("/")
async def create_alert(
    request: CreateAlertRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Create a new performance alert."""
    check_alert_permission(current_user, "create")
    
    try:
        alert = await alert_service.create_alert(
            kol_id=request.kol_id,
            alert_type=request.alert_type,
            severity=request.severity,
            title=request.title,
            message=request.message,
            actual_value=request.actual_value,
            previous_value=request.previous_value,
            threshold_value=request.threshold_value,
            context_data=request.context_data,
            auto_notify=request.auto_notify
        )
        
        return {
            "success": True,
            "alert_id": alert.id,
            "created_at": alert.created_at.isoformat(),
            "alert": {
                "id": alert.id,
                "kol_id": alert.kol_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "is_acknowledged": alert.is_acknowledged,
                "is_notified": alert.is_notified
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )


@router.get("/")
async def get_alerts(
    kol_id: Optional[int] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    alert_type: Optional[AlertType] = Query(None),
    is_acknowledged: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Get alerts with filtering options."""
    check_alert_permission(current_user, "read")
    
    try:
        alerts, total = await alert_service.get_alerts(
            kol_id=kol_id,
            severity=severity,
            alert_type=alert_type,
            is_acknowledged=is_acknowledged,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        return {
            "success": True,
            "total": total,
            "alerts": [
                {
                    "id": alert.id,
                    "kol_id": alert.kol_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "actual_value": alert.actual_value,
                    "previous_value": alert.previous_value,
                    "threshold_value": alert.threshold_value,
                    "is_acknowledged": alert.is_acknowledged,
                    "is_notified": alert.is_notified,
                    "created_at": alert.created_at.isoformat(),
                    "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    "acknowledged_by": alert.acknowledged_by,
                    "acknowledgment_note": alert.acknowledgment_note,
                    "context_data": alert.context_data
                }
                for alert in alerts
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    request: AcknowledgeAlertRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Acknowledge a performance alert."""
    check_alert_permission(current_user, "update")
    
    try:
        alert = await alert_service.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id,
            acknowledgment_note=request.acknowledgment_note
        )
        
        return {
            "success": True,
            "alert_id": alert.id,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "acknowledged_by": alert.acknowledged_by,
            "acknowledgment_note": alert.acknowledgment_note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.post("/bulk-acknowledge")
async def bulk_acknowledge_alerts(
    request: BulkAcknowledgeRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Acknowledge multiple alerts at once."""
    check_alert_permission(current_user, "update")
    
    try:
        result = await alert_service.bulk_acknowledge_alerts(
            alert_ids=request.alert_ids,
            user_id=current_user.id,
            acknowledgment_note=request.acknowledgment_note
        )
        
        return {
            "success": True,
            **result,
            "acknowledged_by": current_user.id,
            "acknowledged_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk acknowledge alerts: {str(e)}"
        )


@router.get("/summary")
async def get_alert_summary(
    kol_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Get alert summary statistics."""
    check_alert_permission(current_user, "read")
    
    try:
        summary = await alert_service.get_alert_summary(
            kol_id=kol_id,
            days=days
        )
        
        return {
            "success": True,
            **summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert summary: {str(e)}"
        )


@router.post("/configure-thresholds")
async def configure_alert_thresholds(
    request: AlertThresholdsRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Configure custom alert thresholds for KOL or campaign."""
    check_alert_permission(current_user, "update")
    
    try:
        config = await alert_service.configure_alert_thresholds(
            kol_id=request.kol_id,
            campaign_id=request.campaign_id,
            thresholds=request.thresholds
        )
        
        return {
            "success": True,
            "configuration": config,
            "configured_by": current_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure thresholds: {str(e)}"
        )


@router.get("/escalation-queue")
async def get_escalation_queue(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Get alerts that need escalation (admin only)."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        escalation_queue = await alert_service.get_escalation_queue()
        
        return {
            "success": True,
            "escalation_queue": escalation_queue,
            "total_escalations": len(escalation_queue),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get escalation queue: {str(e)}"
        )


@router.post("/auto-acknowledge")
async def auto_acknowledge_old_alerts(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Automatically acknowledge old alerts (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await alert_service.auto_acknowledge_old_alerts()
        
        return {
            "success": True,
            **result,
            "triggered_by": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-acknowledge alerts: {str(e)}"
        )


@router.delete("/cleanup")
async def cleanup_old_alerts(
    days_to_keep: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    alert_service: PerformanceAlertService = Depends(get_alert_service)
):
    """Clean up old acknowledged alerts (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await alert_service.cleanup_old_alerts(days_to_keep)
        
        return {
            "success": True,
            **result,
            "triggered_by": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup alerts: {str(e)}"
        )