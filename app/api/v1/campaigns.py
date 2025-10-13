"""Campaign management endpoints."""
from typing import Optional
from datetime import date
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
