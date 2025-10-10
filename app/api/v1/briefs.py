"""Brief API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.brief_service import BriefService
from app.schemas.brief import (
    BriefCreate, BriefUpdate, BriefStatusUpdate, BriefResponse, BriefWithRelations,
    BriefListResponse, BriefFilters, BriefStats, GenerateBriefFromTemplate,
    BulkBriefCreate, BriefTemplateCreate, BriefTemplateUpdate, BriefTemplateResponse,
    BriefTemplateListResponse
)

router = APIRouter(prefix="/briefs", tags=["briefs"])


# Brief Endpoints
@router.post("/", response_model=BriefResponse, status_code=status.HTTP_201_CREATED)
def create_brief(
    brief_data: BriefCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new brief."""
    brief_service = BriefService(db)
    brief = brief_service.create_brief(
        title=brief_data.title,
        content=brief_data.content,
        campaign_id=brief_data.campaign_id,
        kol_id=brief_data.kol_id,
        created_by=current_user.id,
        template_id=brief_data.template_id,
        brief_data=brief_data.brief_data,
        internal_notes=brief_data.internal_notes
    )
    return brief


@router.get("/", response_model=BriefListResponse)
def list_briefs(
    campaign_id: Optional[int] = Query(None),
    kol_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    approved_by: Optional[int] = Query(None),
    template_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List briefs with filtering and pagination."""
    filters = BriefFilters(
        campaign_id=campaign_id,
        kol_id=kol_id,
        status=status,
        created_by=created_by,
        approved_by=approved_by,
        template_id=template_id,
        search=search,
        date_from=date_from,
        date_to=date_to
    )
    
    brief_service = BriefService(db)
    skip = (page - 1) * page_size
    briefs, total = brief_service.list_briefs(
        skip=skip,
        limit=page_size,
        campaign_id=campaign_id,
        kol_id=kol_id,
        status=status,
        created_by=created_by,
        search=search
    )
    
    # Convert to response format with related data
    brief_responses = []
    for brief in briefs:
        brief_dict = {
            **brief.__dict__,
            "campaign_name": brief.campaign.name if brief.campaign else None,
            "kol_name": brief.kol.name if brief.kol else None,
            "template_name": brief.template.name if brief.template else None,
            "creator_name": brief.creator.full_name if brief.creator else None,
            "approver_name": brief.approver.full_name if brief.approver else None,
        }
        brief_responses.append(BriefWithRelations(**brief_dict))
    
    total_pages = (total + page_size - 1) // page_size
    
    return BriefListResponse(
        briefs=brief_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{brief_id}", response_model=BriefWithRelations)
def get_brief(
    brief_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific brief by ID."""
    brief_service = BriefService(db)
    brief = brief_service.get_brief(brief_id)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brief not found"
        )
    
    # Convert to response format with related data
    brief_dict = {
        **brief.__dict__,
        "campaign_name": brief.campaign.name if brief.campaign else None,
        "kol_name": brief.kol.name if brief.kol else None,
        "template_name": brief.template.name if brief.template else None,
        "creator_name": brief.creator.full_name if brief.creator else None,
        "approver_name": brief.approver.full_name if brief.approver else None,
    }
    
    return BriefWithRelations(**brief_dict)


@router.put("/{brief_id}", response_model=BriefResponse)
def update_brief(
    brief_id: int,
    brief_data: BriefUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a brief."""
    brief_service = BriefService(db)
    brief = brief_service.update_brief(
        brief_id=brief_id,
        title=brief_data.title,
        content=brief_data.content,
        brief_data=brief_data.brief_data,
        internal_notes=brief_data.internal_notes,
        status=brief_data.status
    )
    return brief


@router.patch("/{brief_id}/status", response_model=BriefResponse)
def update_brief_status(
    brief_id: int,
    status_data: BriefStatusUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update brief status."""
    brief_service = BriefService(db)
    brief = brief_service.update_brief_status(
        brief_id=brief_id,
        status=status_data.status,
        user_id=current_user.id,
        kol_feedback=status_data.kol_feedback
    )
    return brief


@router.delete("/{brief_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brief(
    brief_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a brief (only if in draft status)."""
    brief_service = BriefService(db)
    brief_service.delete_brief(brief_id)


@router.post("/generate-from-template", response_model=BriefResponse, status_code=status.HTTP_201_CREATED)
def generate_brief_from_template(
    generation_data: GenerateBriefFromTemplate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Generate a brief from a template."""
    brief_service = BriefService(db)
    brief = brief_service.generate_brief_from_template(
        template_id=generation_data.template_id,
        campaign_id=generation_data.campaign_id,
        kol_id=generation_data.kol_id,
        created_by=current_user.id,
        variables=generation_data.variables
    )
    return brief


@router.post("/bulk", response_model=List[BriefResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_briefs(
    bulk_data: BulkBriefCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create briefs for multiple KOLs."""
    brief_service = BriefService(db)
    briefs = brief_service.create_bulk_briefs(
        campaign_id=bulk_data.campaign_id,
        kol_ids=bulk_data.kol_ids,
        template_id=bulk_data.template_id,
        created_by=current_user.id,
        variables=bulk_data.variables
    )
    return briefs


@router.get("/stats/overview", response_model=BriefStats)
def get_brief_stats(
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get brief statistics."""
    brief_service = BriefService(db)
    stats = brief_service.get_brief_stats(campaign_id)
    return BriefStats(**stats)


# Brief Template Endpoints
@router.post("/templates", response_model=BriefTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_brief_template(
    template_data: BriefTemplateCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new brief template."""
    brief_service = BriefService(db)
    template = brief_service.create_brief_template(
        name=template_data.name,
        content=template_data.content,
        created_by=current_user.id,
        description=template_data.description,
        category=template_data.category,
        variables=template_data.variables,
        is_default=template_data.is_default
    )
    return template


@router.get("/templates", response_model=BriefTemplateListResponse)
def list_brief_templates(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List brief templates with filtering and pagination."""
    brief_service = BriefService(db)
    skip = (page - 1) * page_size
    templates, total = brief_service.list_brief_templates(
        skip=skip,
        limit=page_size,
        category=category,
        is_active=is_active
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return BriefTemplateListResponse(
        templates=templates,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/templates/{template_id}", response_model=BriefTemplateResponse)
def get_brief_template(
    template_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific brief template by ID."""
    brief_service = BriefService(db)
    template = brief_service.get_brief_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brief template not found"
        )
    return template


@router.put("/templates/{template_id}", response_model=BriefTemplateResponse)
def update_brief_template(
    template_id: int,
    template_data: BriefTemplateUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a brief template."""
    brief_service = BriefService(db)
    template = brief_service.update_brief_template(
        template_id=template_id,
        name=template_data.name,
        description=template_data.description,
        content=template_data.content,
        category=template_data.category,
        variables=template_data.variables,
        is_active=template_data.is_active,
        is_default=template_data.is_default
    )
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brief_template(
    template_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a brief template."""
    brief_service = BriefService(db)
    brief_service.delete_brief_template(template_id)
