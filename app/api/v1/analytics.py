"""API endpoints for historical analytics and anomaly detection."""
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.historical_analytics_service import HistoricalAnalyticsService
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/analytics", tags=["analytics"])


class HistoricalMetricsRequest(BaseModel):
    """Request model for historical metrics."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: Optional[int] = Field(None, ge=1, le=365)
    granularity: str = Field("daily", regex="^(raw|daily|weekly|monthly)$")


class GrowthAnalysisRequest(BaseModel):
    """Request model for growth analysis."""
    platforms: Optional[List[str]] = None
    period_days: int = Field(30, ge=7, le=365)


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection."""
    platforms: Optional[List[str]] = None
    detection_window_days: int = Field(7, ge=1, le=30)
    auto_create_alerts: bool = Field(True)


class ComparativeAnalysisRequest(BaseModel):
    """Request model for comparative analysis."""
    kol_ids: List[int] = Field(..., min_items=2, max_items=20)
    platform: str
    metric: str = Field("follower_count", regex="^(follower_count|engagement_rate|post_count)$")
    days: int = Field(30, ge=7, le=365)


def check_analytics_permission(current_user: User, action: str = "read"):
    """Check if user has analytics permissions."""
    PermissionService.require_permission(current_user.role, "analytics", action)


def get_historical_service(db: Session = Depends(get_session)) -> HistoricalAnalyticsService:
    """Get historical analytics service instance."""
    return HistoricalAnalyticsService(db)


def get_anomaly_service(db: Session = Depends(get_session)) -> AnomalyDetectionService:
    """Get anomaly detection service instance."""
    return AnomalyDetectionService(db)


@router.get("/kols/{kol_id}/historical/{platform}")
async def get_historical_metrics(
    kol_id: int,
    platform: str,
    request: HistoricalMetricsRequest = Depends(),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    analytics_service: HistoricalAnalyticsService = Depends(get_historical_service)
):
    """Get historical metrics for a KOL on a specific platform."""
    check_analytics_permission(current_user, "read")
    
    try:
        result = await analytics_service.get_historical_metrics(
            kol_id=kol_id,
            platform=platform,
            start_date=request.start_date,
            end_date=request.end_date,
            days=request.days,
            granularity=request.granularity
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get historical metrics: {str(e)}"
        )


@router.post("/kols/{kol_id}/growth-analysis")
async def get_growth_analysis(
    kol_id: int,
    request: GrowthAnalysisRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    analytics_service: HistoricalAnalyticsService = Depends(get_historical_service)
):
    """Get comprehensive growth analysis for a KOL."""
    check_analytics_permission(current_user, "read")
    
    try:
        result = await analytics_service.get_growth_analysis(
            kol_id=kol_id,
            platforms=request.platforms,
            period_days=request.period_days
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get growth analysis: {str(e)}"
        )


@router.post("/kols/{kol_id}/anomaly-detection")
async def detect_anomalies(
    kol_id: int,
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service)
):
    """Detect anomalies in KOL performance metrics."""
    check_analytics_permission(current_user, "read")
    
    try:
        anomalies = await anomaly_service.detect_all_anomalies(
            kol_id=kol_id,
            platforms=request.platforms,
            detection_window_days=request.detection_window_days
        )
        
        # Create alerts if requested
        alerts = []
        if request.auto_create_alerts:
            alerts = await anomaly_service.create_performance_alerts(anomalies)
        
        return {
            "kol_id": kol_id,
            "detection_window_days": request.detection_window_days,
            "anomalies_detected": len(anomalies),
            "alerts_created": len(alerts),
            "anomalies": [
                {
                    "anomaly_type": a.anomaly_type,
                    "category": a.category.value,
                    "severity": a.severity.value,
                    "confidence": a.confidence,
                    "description": a.description,
                    "platform": a.platform,
                    "detected_at": a.detected_at.isoformat(),
                    "current_value": a.current_value,
                    "expected_value": a.expected_value,
                    "deviation_score": a.deviation_score,
                    "context_data": a.context_data
                }
                for a in anomalies
            ],
            "detected_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect anomalies: {str(e)}"
        )


@router.get("/kols/{kol_id}/statistical-outliers/{platform}")
async def detect_statistical_outliers(
    kol_id: int,
    platform: str,
    metric: str = Query("follower_count", regex="^(follower_count|engagement_rate|post_count)$"),
    window_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service)
):
    """Detect statistical outliers using Z-score analysis."""
    check_analytics_permission(current_user, "read")
    
    try:
        outliers = await anomaly_service.detect_statistical_outliers(
            kol_id=kol_id,
            platform=platform,
            metric_name=metric,
            window_days=window_days
        )
        
        return {
            "kol_id": kol_id,
            "platform": platform,
            "metric": metric,
            "window_days": window_days,
            "outliers_detected": len(outliers),
            "outliers": [
                {
                    "anomaly_type": o.anomaly_type,
                    "severity": o.severity.value,
                    "confidence": o.confidence,
                    "description": o.description,
                    "detected_at": o.detected_at.isoformat(),
                    "current_value": o.current_value,
                    "expected_value": o.expected_value,
                    "z_score": o.deviation_score,
                    "context_data": o.context_data
                }
                for o in outliers
            ],
            "analyzed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect outliers: {str(e)}"
        )


@router.get("/kols/{kol_id}/trend-anomalies/{platform}")
async def detect_trend_anomalies(
    kol_id: int,
    platform: str,
    metric: str = Query("follower_count", regex="^(follower_count|engagement_rate)$"),
    trend_window_days: int = Query(14, ge=7, le=30),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service)
):
    """Detect anomalies in trend patterns."""
    check_analytics_permission(current_user, "read")
    
    try:
        trend_anomalies = await anomaly_service.detect_trend_anomalies(
            kol_id=kol_id,
            platform=platform,
            metric_name=metric,
            trend_window_days=trend_window_days
        )
        
        return {
            "kol_id": kol_id,
            "platform": platform,
            "metric": metric,
            "trend_window_days": trend_window_days,
            "trend_anomalies_detected": len(trend_anomalies),
            "trend_anomalies": [
                {
                    "anomaly_type": ta.anomaly_type,
                    "severity": ta.severity.value,
                    "confidence": ta.confidence,
                    "description": ta.description,
                    "detected_at": ta.detected_at.isoformat(),
                    "current_trend": ta.current_value,
                    "baseline_trend": ta.expected_value,
                    "trend_change": ta.deviation_score,
                    "context_data": ta.context_data
                }
                for ta in trend_anomalies
            ],
            "analyzed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect trend anomalies: {str(e)}"
        )


@router.post("/comparative-analysis")
async def get_comparative_analysis(
    request: ComparativeAnalysisRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    analytics_service: HistoricalAnalyticsService = Depends(get_historical_service)
):
    """Compare multiple KOLs on a specific metric."""
    check_analytics_permission(current_user, "read")
    
    try:
        result = await analytics_service.get_comparative_analysis(
            kol_ids=request.kol_ids,
            platform=request.platform,
            metric=request.metric,
            days=request.days
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparative analysis: {str(e)}"
        )


@router.get("/trends/summary")
async def get_trends_summary(
    platforms: Optional[List[str]] = Query(None),
    days: int = Query(30, ge=7, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    analytics_service: HistoricalAnalyticsService = Depends(get_historical_service)
):
    """Get trends summary across multiple KOLs."""
    check_analytics_permission(current_user, "read")
    
    try:
        # This would be implemented to get trending KOLs, top performers, etc.
        # For now, return a placeholder structure
        
        return {
            "summary_period_days": days,
            "platforms_analyzed": platforms or ["instagram", "tiktok", "youtube", "twitter", "facebook"],
            "top_performers": [],  # Would be populated with actual data
            "trending_up": [],     # KOLs with positive trends
            "trending_down": [],   # KOLs with negative trends
            "anomalies_detected": 0,
            "generated_at": datetime.utcnow(),
            "note": "Trends summary implementation pending - placeholder response"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trends summary: {str(e)}"
        )


@router.post("/archive-old-data")
async def archive_old_data(
    days_to_keep: int = Query(365, ge=90, le=1095, description="Days of data to keep"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    analytics_service: HistoricalAnalyticsService = Depends(get_historical_service)
):
    """Archive old metrics data (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await analytics_service.archive_old_metrics(days_to_keep)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive data: {str(e)}"
        )


@router.get("/system/analytics-status")
async def get_analytics_system_status(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get analytics system status (admin only)."""
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        from sqlmodel import func
        from app.models.kol_metrics import KOLMetrics
        from app.models.performance_alert import PerformanceAlert
        
        # Get metrics counts
        total_metrics = db.exec(select(func.count(KOLMetrics.id))).first()
        
        # Get recent metrics (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_metrics = db.exec(
            select(func.count(KOLMetrics.id)).where(
                KOLMetrics.scraped_at >= recent_cutoff
            )
        ).first()
        
        # Get alert counts
        total_alerts = db.exec(select(func.count(PerformanceAlert.id))).first()
        unread_alerts = db.exec(
            select(func.count(PerformanceAlert.id)).where(
                PerformanceAlert.is_acknowledged == False
            )
        ).first()
        
        return {
            "system_status": "operational",
            "metrics_data": {
                "total_metrics": total_metrics,
                "recent_metrics_24h": recent_metrics,
                "data_coverage": "good" if recent_metrics > 0 else "limited"
            },
            "alerts_data": {
                "total_alerts": total_alerts,
                "unread_alerts": unread_alerts,
                "alert_rate": "normal"
            },
            "analytics_features": {
                "historical_analysis": "available",
                "anomaly_detection": "available",
                "comparative_analysis": "available",
                "trend_analysis": "available"
            },
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "system_status": "degraded",
            "error": str(e),
            "last_updated": datetime.utcnow()
        }