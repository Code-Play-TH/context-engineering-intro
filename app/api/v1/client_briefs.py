"""Client Brief management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.core.database import get_session
from app.core.auth import get_current_user
from app.services.client_brief_service import ClientBriefService
from app.services.permission_service import PermissionService
from app.schemas.client_brief import (
    ClientBriefCreate,
    ClientBriefUpdate,
    ClientBriefResponse,
    ClientBriefListResponse,
    ClientBriefApproval
)
from app.models.user import User


router = APIRouter(prefix="/client-briefs", tags=["Client Briefs"])


@router.post("", response_model=ClientBriefResponse, status_code=status.HTTP_201_CREATED)
def create_client_brief(
    brief_data: ClientBriefCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new client brief.
    """
    PermissionService.require_permission(current_user.role, "client_briefs", "create")
    
    brief_service = ClientBriefService(db)
    brief = brief_service.create_brief(
        client_name=brief_data.client_name,
        campaign_objective=brief_data.campaign_objective,
        target_audience=brief_data.target_audience,
        budget=brief_data.budget,
        currency=brief_data.currency,
        brand_guidelines=brief_data.brand_guidelines,
        content_requirements=brief_data.content_requirements,
        campaign_start_date=brief_data.campaign_start_date,
        campaign_end_date=brief_data.campaign_end_date,
        content_deadline=brief_data.content_deadline,
        platform_requirements=brief_data.platform_requirements,
        kol_requirements=brief_data.kol_requirements,
        deliverable_requirements=brief_data.deliverable_requirements,
        created_by=current_user.id
    )
    
    return brief


@router.get("", response_model=ClientBriefListResponse)
def list_client_briefs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    client_name: Optional[str] = None,
    status: Optional[str] = None,
    created_by: Optional[int] = None,
    sort_by: str = Query("created_at", regex="^(client_name|created_at|updated_at|status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List client briefs with pagination, filters, and sorting.
    """
    PermissionService.require_permission(current_user.role, "client_briefs", "read")
    
    brief_service = ClientBriefService(db)
    skip = (page - 1) * page_size
    
    # Account Executives can only see their own briefs
    if current_user.role == "account_executive":
        created_by = current_user.id
    
    briefs, total = brief_service.list_briefs(
        skip=skip,
        limit=page_size,
        search=search,
        client_name=client_name,
        status=status,
        created_by=created_by,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return ClientBriefListResponse(
        briefs=briefs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{brief_id}", response_model=ClientBriefResponse)
def get_client_brief(
    brief_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get client brief details.
    """
    PermissionService.require_permission(current_user.role, "client_briefs", "read")
    
    brief_service = ClientBriefService(db)
    brief = brief_service.get_brief(brief_id)
    
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client brief not found"
        )
    
    # Account Executives can only see their own briefs
    if current_user.role == "account_executive" and brief.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return brief


@router.put("/{brief_id}", response_model=ClientBriefResponse)
def update_client_brief(
    brief_id: int,
    brief_data: ClientBriefUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update client brief information.
    """
    PermissionService.require_permission(current_user.role, "client_briefs", "update")
    
    brief_service = ClientBriefService(db)
    
    # Check if brief exists and user has permission
    brief = brief_service.get_brief(brief_id)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client brief not found"
        )
    
    # Account Executives can only update their own briefs
    if current_user.role == "account_executive" and brief.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Only allow status updates by Campaign Managers and Admins
    if brief_data.status and current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Campaign Managers and Admins can update brief status"
        )
    
    brief = brief_service.update_brief(
        brief_id=brief_id,
        client_name=brief_data.client_name,
        campaign_objective=brief_data.campaign_objective,
        target_audience=brief_data.target_audience,
        budget=brief_data.budget,
        currency=brief_data.currency,
        brand_guidelines=brief_data.brand_guidelines,
        content_requirements=brief_data.content_requirements,
        campaign_start_date=brief_data.campaign_start_date,
        campaign_end_date=brief_data.campaign_end_date,
        content_deadline=brief_data.content_deadline,
        platform_requirements=brief_data.platform_requirements,
        kol_requirements=brief_data.kol_requirements,
        deliverable_requirements=brief_data.deliverable_requirements,
        status=brief_data.status
    )
    
    return brief


@router.post("/{brief_id}/approve", response_model=ClientBriefResponse)
def approve_client_brief(
    brief_id: int,
    approval_data: ClientBriefApproval,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject a client brief.
    """
    # Only Campaign Managers and Admins can approve briefs
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Campaign Managers and Admins can approve briefs"
        )
    
    brief_service = ClientBriefService(db)
    
    if approval_data.approved:
        brief = brief_service.approve_brief(brief_id, current_user.id)
    else:
        brief = brief_service.reject_brief(brief_id, approval_data.rejection_reason)
    
    return brief


@router.post("/{brief_id}/submit", response_model=ClientBriefResponse)
def submit_client_brief(
    brief_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Submit client brief for approval.
    """
    PermissionService.require_permission(current_user.role, "client_briefs", "update")
    
    brief_service = ClientBriefService(db)
    brief = brief_service.get_brief(brief_id)
    
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client brief not found"
        )
    
    # Account Executives can only submit their own briefs
    if current_user.role == "account_executive" and brief.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if brief.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft briefs can be submitted"
        )
    
    brief = brief_service.update_brief(brief_id, status="submitted")
    
    return brief