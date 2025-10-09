"""KOL management endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.core.database import get_session
from app.core.auth import get_current_user
from app.services.kol_service import KOLService
from app.services.permission_service import PermissionService
from app.schemas.kol import (
    KOLCreate,
    KOLUpdate,
    KOLResponse,
    KOLListResponse,
    SocialHandleCreate,
    SocialHandleUpdate,
    SocialHandleResponse
)
from app.models.user import User


router = APIRouter(prefix="/kols", tags=["KOLs"])


@router.post("", response_model=KOLResponse, status_code=status.HTTP_201_CREATED)
def create_kol(
    kol_data: KOLCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new KOL.
    """
    PermissionService.require_permission(current_user.role, "kols", "create")
    
    kol_service = KOLService(db)
    kol = kol_service.create_kol(
        name=kol_data.name,
        email=kol_data.email,
        phone=kol_data.phone,
        location=kol_data.location,
        niche=kol_data.niche,
        tags=kol_data.tags,
        notes=kol_data.notes,
        social_handles=[handle.dict() for handle in kol_data.social_handles]
    )
    
    return kol


@router.get("", response_model=KOLListResponse)
def list_kols(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    niche: Optional[str] = None,
    location: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: str = Query("created_at", regex="^(name|created_at|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List KOLs with pagination, filters, and sorting.
    """
    PermissionService.require_permission(current_user.role, "kols", "read")
    
    kol_service = KOLService(db)
    skip = (page - 1) * page_size
    
    kols, total = kol_service.list_kols(
        skip=skip,
        limit=page_size,
        search=search,
        niche=niche,
        location=location,
        tier=tier,
        status=status,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return KOLListResponse(
        kols=kols,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{kol_id}", response_model=KOLResponse)
def get_kol(
    kol_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get KOL details.
    """
    PermissionService.require_permission(current_user.role, "kols", "read")
    
    kol_service = KOLService(db)
    kol = kol_service.get_kol(kol_id)
    
    if not kol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KOL not found"
        )
    
    return kol


@router.put("/{kol_id}", response_model=KOLResponse)
def update_kol(
    kol_id: int,
    kol_data: KOLUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update KOL information.
    """
    PermissionService.require_permission(current_user.role, "kols", "update")
    
    kol_service = KOLService(db)
    kol = kol_service.update_kol(
        kol_id=kol_id,
        name=kol_data.name,
        email=kol_data.email,
        phone=kol_data.phone,
        location=kol_data.location,
        niche=kol_data.niche,
        tags=kol_data.tags,
        notes=kol_data.notes,
        status=kol_data.status
    )
    
    return kol


@router.delete("/{kol_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kol(
    kol_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete KOL.
    """
    PermissionService.require_permission(current_user.role, "kols", "delete")
    
    kol_service = KOLService(db)
    kol_service.soft_delete_kol(kol_id)
    
    return None


@router.post("/{kol_id}/social-handles", response_model=SocialHandleResponse, status_code=status.HTTP_201_CREATED)
def add_social_handle(
    kol_id: int,
    handle_data: SocialHandleCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Add social media handle to KOL.
    """
    PermissionService.require_permission(current_user.role, "kols", "update")
    
    kol_service = KOLService(db)
    handle = kol_service.add_social_handle(
        kol_id=kol_id,
        platform=handle_data.platform,
        handle=handle_data.handle,
        url=handle_data.url,
        follower_count=handle_data.follower_count,
        is_verified=handle_data.is_verified
    )
    
    return handle


@router.post("/{kol_id}/tags/{tag}", response_model=KOLResponse)
def add_tag(
    kol_id: int,
    tag: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Add tag to KOL.
    """
    PermissionService.require_permission(current_user.role, "kols", "update")
    
    kol_service = KOLService(db)
    kol = kol_service.add_tag(kol_id, tag)
    
    return kol


@router.delete("/{kol_id}/tags/{tag}", response_model=KOLResponse)
def remove_tag(
    kol_id: int,
    tag: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Remove tag from KOL.
    """
    PermissionService.require_permission(current_user.role, "kols", "update")
    
    kol_service = KOLService(db)
    kol = kol_service.remove_tag(kol_id, tag)
    
    return kol

@router.put("/{kol_id}/social-handles/{handle_id}", response_model=SocialHandleResponse)
def update_social_handle(
    kol_id: int,
    handle_id: int,
    handle_data: SocialHandleUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update social media handle.
    """
    PermissionService.require_permission(current_user.role, "kols", "update")
    
    kol_service = KOLService(db)
    handle = kol_service.update_social_handle(
        handle_id=handle_id,
        platform=handle_data.platform,
        handle=handle_data.handle,
        url=handle_data.url,
        follower_count=handle_data.follower_count,
        is_verified=handle_data.is_verified,
        is_active=handle_data.is_active
    )
    
    return handle


@router.delete("/{kol_id}/social-handles/{handle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_handle(
    kol_id: int,
    handle_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete social media handle.
    """
    PermissionService.require_permission(current_user.role, "kols", "delete")
    
    kol_service = KOLService(db)
    kol_service.delete_social_handle(handle_id)
    
    return None