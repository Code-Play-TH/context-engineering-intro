"""
Report Template API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.services.report_template_service import ReportTemplateService
from app.schemas.report_template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateFilters,
    TemplateDuplicateRequest
)
from app.models.report_template import TemplateType

router = APIRouter(prefix="/report-templates", tags=["report-templates"])


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new report template.
    
    - **name**: Template name (required)
    - **description**: Optional template description
    - **template_type**: Template type (powerpoint or pdf)
    - **is_shared**: Whether template is shared with organization
    - **structure**: Template layout definition (JSON)
    - **variables**: List of template variables in {{variable}} format
    """
    service = ReportTemplateService(session)
    
    try:
        template = await service.create_template(template_data, current_user.id)
        return TemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    search: str = Query(None, description="Search in name and description"),
    template_type: TemplateType = Query(None, description="Filter by template type"),
    is_shared: bool = Query(None, description="Filter by shared status"),
    created_by: int = Query(None, description="Filter by creator"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List report templates with filtering and pagination.
    
    Users can see:
    - Templates they created
    - Shared templates from other users
    
    Supports filtering by:
    - **search**: Search in name and description
    - **template_type**: Filter by powerpoint or pdf
    - **is_shared**: Filter by shared status
    - **created_by**: Filter by creator user ID
    """
    service = ReportTemplateService(session)
    
    filters = TemplateFilters(
        search=search,
        template_type=template_type,
        is_shared=is_shared,
        created_by=created_by,
        limit=limit,
        offset=offset
    )
    
    templates, total = await service.list_templates(filters, current_user.id)
    
    return TemplateListResponse(
        templates=[TemplateResponse.from_orm(t) for t in templates],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/popular", response_model=List[TemplateResponse])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="Number of templates to return"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get popular templates based on usage count.
    
    Returns templates ordered by usage count (most used first).
    Users can only see templates they have access to.
    """
    service = ReportTemplateService(session)
    templates = await service.get_popular_templates(limit, current_user.id)
    
    return [TemplateResponse.from_orm(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific template by ID.
    
    Users can only access:
    - Templates they created
    - Shared templates from other users
    """
    service = ReportTemplateService(session)
    template = await service.get_template(template_id, current_user.id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )
    
    return TemplateResponse.from_orm(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a template.
    
    Only the template creator can update their templates.
    
    - **name**: Template name
    - **description**: Template description
    - **is_shared**: Whether template is shared with organization
    - **structure**: Template layout definition (JSON)
    - **variables**: List of template variables in {{variable}} format
    """
    service = ReportTemplateService(session)
    template = await service.update_template(template_id, template_data, current_user.id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )
    
    return TemplateResponse.from_orm(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a template.
    
    Only the template creator can delete their templates.
    
    Note: This will fail if the template is used in scheduled reports.
    """
    service = ReportTemplateService(session)
    success = await service.delete_template(template_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )


@router.post("/{template_id}/duplicate", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_template(
    template_id: int,
    duplicate_data: TemplateDuplicateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Duplicate a template.
    
    Creates a copy of an existing template with a new name.
    Users can duplicate any template they have access to.
    
    - **name**: Name for the duplicated template (required)
    - **description**: Optional description for the duplicated template
    - **is_shared**: Whether the duplicated template should be shared
    """
    service = ReportTemplateService(session)
    template = await service.duplicate_template(template_id, duplicate_data, current_user.id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )
    
    return TemplateResponse.from_orm(template)