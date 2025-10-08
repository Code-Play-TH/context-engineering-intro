"""Campaign management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.core.database import get_session
from app.core.auth import get_current_user
from app.services.campaign_service import CampaignService
from app.services.permission_service import PermissionService
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    KPICreate,
    KPIResponse,
    DeliverableCreate,
    DeliverableResponse
)
from app.models.user import User


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign."""
    PermissionService.require_permission(current_user.role, "campaigns", "create")
    
    campaign_service = CampaignService(db)
    campaign = campaign_service.create_campaign(
        name=campaign_data.name,
        user_id=current_user.id,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        total_budget=campaign_data.total_budget,
        currency=campaign_data.currency,
        objectives=campaign_data.objectives,
        target_audience=campaign_data.target_audience,
        kpis=[kpi.dict() for kpi in campaign_data.kpis],
        deliverables=[d.dict() for d in campaign_data.deliverables]
    )
    
    return campaign


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List campaigns with pagination and filters."""
    PermissionService.require_permission(current_user.role, "campaigns", "read")
    
    campaign_service = CampaignService(db)
    skip = (page - 1) * page_size
    
    campaigns, total = campaign_service.list_campaigns(
        skip=skip,
        limit=page_size,
        status=status
    )
    
    return CampaignListResponse(
        campaigns=campaigns,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get campaign details."""
    PermissionService.require_permission(current_user.role, "campaigns", "read")
    
    campaign_service = CampaignService(db)
    campaign = campaign_service.get_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update campaign information."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    campaign = campaign_service.update_campaign(
        campaign_id=campaign_id,
        name=campaign_data.name,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        total_budget=campaign_data.total_budget,
        currency=campaign_data.currency,
        objectives=campaign_data.objectives,
        target_audience=campaign_data.target_audience,
        status=campaign_data.status
    )
    
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete campaign (soft delete)."""
    PermissionService.require_permission(current_user.role, "campaigns", "delete")
    
    campaign_service = CampaignService(db)
    campaign_service.delete_campaign(campaign_id)
    
    return None


@router.put("/{campaign_id}/status", response_model=CampaignResponse)
def change_campaign_status(
    campaign_id: int,
    new_status: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Change campaign status."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    campaign = campaign_service.change_status(campaign_id, new_status)
    
    return campaign


@router.post("/{campaign_id}/kpis", response_model=KPIResponse, status_code=status.HTTP_201_CREATED)
def add_kpi(
    campaign_id: int,
    kpi_data: KPICreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add KPI to campaign."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    kpi = campaign_service.add_kpi(
        campaign_id=campaign_id,
        kpi_type=kpi_data.kpi_type,
        target_value=kpi_data.target_value,
        unit=kpi_data.unit
    )
    
    return kpi


@router.post("/{campaign_id}/deliverables", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED)
def add_deliverable(
    campaign_id: int,
    deliverable_data: DeliverableCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add deliverable to campaign."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    deliverable = campaign_service.add_deliverable(
        campaign_id=campaign_id,
        deliverable_type=deliverable_data.deliverable_type,
        quantity=deliverable_data.quantity,
        deadline=deliverable_data.deadline
    )
    
    return deliverable


@router.post("/{campaign_id}/duplicate", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def duplicate_campaign(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Duplicate campaign."""
    PermissionService.require_permission(current_user.role, "campaigns", "create")
    
    campaign_service = CampaignService(db)
    campaign = campaign_service.duplicate_campaign(campaign_id)
    
    return campaign
