"""API endpoints for campaign performance analysis and KPI tracking."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.campaign_performance_service import CampaignPerformanceService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/campaign-performance", tags=["campaign-performance"])


class KPITargetsRequest(BaseModel):
    """Request model for KPI targets."""
    target_kpis: Dict[str, float] = Field(..., description="KPI targets as key-value pairs")


class KOLPerformanceRequest(BaseModel):
    """Request model for KOL performance within campaign."""
    sort_by: str = Field("engagement_rate", regex="^(engagement_rate|reach|posts)$")
    limit: int = Field(20, ge=1, le=100)


def check_campaign_permission(current_user: User, action: str = "read"):
    """Check if user has campaign permissions."""
    PermissionService.require_permission(current_user.role, "campaigns", action)


def get_campaign_performance_service(db: Session = Depends(get_session)) -> CampaignPerformanceService:
    """Get campaign performance service instance."""
    return CampaignPerformanceService(db)


@router.get("/campaigns/{campaign_id}/overview")
async def get_campaign_performance_overview(
    campaign_id: int,
    include_projections: bool = Query(True, description="Include performance projections"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    service: CampaignPerformanceService = Depends(get_campaign_performance_service)
):
    """Get comprehensive campaign performance overview."""
    check_campaign_permission(current_user, "read")
    
    try:
        overview = await service.get_campaign_performance_overview(
            campaign_id=campaign_id,
            include_projections=include_projections
        )
        
        return overview
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign overview: {str(e)}"
        )


@router.post("/campaigns/{campaign_id}/kpi-comparison")
async def compare_campaign_kpis(
    campaign_id: int,
    request: KPITargetsRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    service: CampaignPerformanceService = Depends(get_campaign_performance_service)
):
    """Compare actual campaign performance against target KPIs."""
    check_campaign_permission(current_user, "read")
    
    try:
        comparison = await service.compare_campaign_kpis(
            campaign_id=campaign_id,
            target_kpis=request.target_kpis
        )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare KPIs: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/completion-tracking")
async def get_campaign_completion_tracking(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    service: CampaignPerformanceService = Depends(get_campaign_performance_service)
):
    """Track campaign completion progress."""
    check_campaign_permission(current_user, "read")
    
    try:
        tracking = await service.get_campaign_completion_tracking(campaign_id)
        return tracking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get completion tracking: {str(e)}"
        )


@router.post("/campaigns/{campaign_id}/kol-performance")
async def get_kol_performance_within_campaign(
    campaign_id: int,
    request: KOLPerformanceRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    service: CampaignPerformanceService = Depends(get_campaign_performance_service)
):
    """Get KOL performance ranking within a campaign."""
    check_campaign_permission(current_user, "read")
    
    try:
        performance = await service.get_kol_performance_within_campaign(
            campaign_id=campaign_id,
            sort_by=request.sort_by,
            limit=request.limit
        )
        
        return performance
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get KOL performance: {str(e)}"
        )