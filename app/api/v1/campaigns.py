"""Campaign management endpoints."""
from typing import Optional
from datetime import date, datetime
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
    CampaignStatusChange,
    CampaignSummaryResponse
)
from app.schemas.campaign_kpi import (
    CampaignKPICreate,
    CampaignKPIUpdate,
    CampaignKPIResponse
)
from app.schemas.deliverable import (
    DeliverableCreate,
    DeliverableUpdate,
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
        objectives=campaign_data.objectives,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        total_budget=campaign_data.total_budget,
        currency=campaign_data.currency,
        target_audience=campaign_data.target_audience,
        brief_deadline=campaign_data.brief_deadline,
        content_deadline=campaign_data.content_deadline,
        posting_start_date=campaign_data.posting_start_date,
        posting_end_date=campaign_data.posting_end_date,
        report_due_date=campaign_data.report_due_date,
        created_by=current_user.id
    )
    
    return campaign


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    created_by: Optional[int] = None,
    start_date_from: Optional[date] = None,
    start_date_to: Optional[date] = None,
    sort_by: str = Query("created_at", regex="^(name|created_at|updated_at|start_date)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List campaigns with pagination, filters, and sorting."""
    PermissionService.require_permission(current_user.role, "campaigns", "read")
    
    campaign_service = CampaignService(db)
    skip = (page - 1) * page_size
    
    campaigns, total = campaign_service.list_campaigns(
        skip=skip,
        limit=page_size,
        search=search,
        status=status,
        created_by=created_by,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        sort_by=sort_by,
        sort_order=sort_order
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
        objectives=campaign_data.objectives,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        total_budget=campaign_data.total_budget,
        currency=campaign_data.currency,
        target_audience=campaign_data.target_audience,
        brief_deadline=campaign_data.brief_deadline,
        content_deadline=campaign_data.content_deadline,
        posting_start_date=campaign_data.posting_start_date,
        posting_end_date=campaign_data.posting_end_date,
        report_due_date=campaign_data.report_due_date,
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
    status_data: CampaignStatusChange,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Change campaign status."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    campaign = campaign_service.change_status(campaign_id, status_data.status, current_user.id)
    
    return campaign


@router.get("/{campaign_id}/summary", response_model=CampaignSummaryResponse)
def get_campaign_summary(
    campaign_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get campaign summary with statistics."""
    PermissionService.require_permission(current_user.role, "campaigns", "read")
    
    campaign_service = CampaignService(db)
    summary = campaign_service.get_campaign_summary(campaign_id)
    
    return summary


# KPI Management Endpoints
@router.post("/{campaign_id}/kpis", response_model=CampaignKPIResponse, status_code=status.HTTP_201_CREATED)
def add_campaign_kpi(
    campaign_id: int,
    kpi_data: CampaignKPICreate,
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
        unit=kpi_data.unit,
        description=kpi_data.description,
        priority=kpi_data.priority
    )
    
    return kpi


@router.put("/{campaign_id}/kpis/{kpi_id}", response_model=CampaignKPIResponse)
def update_campaign_kpi(
    campaign_id: int,
    kpi_id: int,
    kpi_data: CampaignKPIUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update campaign KPI."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    kpi = campaign_service.update_kpi(
        kpi_id=kpi_id,
        target_value=kpi_data.target_value,
        actual_value=kpi_data.actual_value,
        unit=kpi_data.unit,
        description=kpi_data.description,
        priority=kpi_data.priority
    )
    
    return kpi


@router.delete("/{campaign_id}/kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign_kpi(
    campaign_id: int,
    kpi_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete campaign KPI."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    campaign_service.delete_kpi(kpi_id)
    
    return None


# Deliverable Management Endpoints
@router.post("/{campaign_id}/deliverables", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED)
def add_campaign_deliverable(
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
        deadline=deliverable_data.deadline,
        title=deliverable_data.title,
        description=deliverable_data.description,
        platform_specific_requirements=deliverable_data.platform_specific_requirements,
        hashtags=deliverable_data.hashtags,
        mentions=deliverable_data.mentions,
        priority=deliverable_data.priority
    )
    
    return deliverable


@router.put("/{campaign_id}/deliverables/{deliverable_id}", response_model=DeliverableResponse)
def update_campaign_deliverable(
    campaign_id: int,
    deliverable_id: int,
    deliverable_data: DeliverableUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update campaign deliverable."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    deliverable = campaign_service.update_deliverable(
        deliverable_id=deliverable_id,
        quantity=deliverable_data.quantity,
        deadline=deliverable_data.deadline,
        title=deliverable_data.title,
        description=deliverable_data.description,
        platform_specific_requirements=deliverable_data.platform_specific_requirements,
        hashtags=deliverable_data.hashtags,
        mentions=deliverable_data.mentions,
        priority=deliverable_data.priority,
        status=deliverable_data.status,
        submitted_count=deliverable_data.submitted_count,
        approved_count=deliverable_data.approved_count,
        published_count=deliverable_data.published_count,
        reviewer_notes=deliverable_data.reviewer_notes,
        rejection_reason=deliverable_data.rejection_reason
    )
    
    return deliverable


@router.delete("/{campaign_id}/deliverables/{deliverable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign_deliverable(
    campaign_id: int,
    deliverable_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete campaign deliverable."""
    PermissionService.require_permission(current_user.role, "campaigns", "update")
    
    campaign_service = CampaignService(db)
    campaign_service.delete_deliverable(deliverable_id)
    
    return None
