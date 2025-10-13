"""KOL management endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
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
    
    # Validate deletion is allowed
    try:
        kol_service.validate_kol_deletion(kol_id)
        kol_service.soft_delete_kol(kol_id)
    except HTTPException as e:
        # Re-raise with more specific error message
        if "active campaigns" in str(e.detail):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=e.detail
            )
        raise e
    
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


# Import endpoints
@router.post("/import", status_code=status.HTTP_201_CREATED)
async def upload_import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Upload CSV/Excel file for KOL import.
    """
    PermissionService.require_permission(current_user.role, "kols", "create")
    
    from app.services.import_service import ImportService
    import_service = ImportService(db)
    
    job = await import_service.upload_import_file(file, current_user.id)
    return {
        "job_id": job.id,
        "filename": job.filename,
        "total_rows": job.total_rows,
        "status": job.status,
        "message": "File uploaded successfully. Use job_id to check status and validate."
    }


@router.get("/import/{job_id}")
def get_import_status(
    job_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get import job status and details.
    """
    PermissionService.require_permission(current_user.role, "kols", "read")
    
    from app.services.import_service import ImportService
    import_service = ImportService(db)
    
    job = import_service.get_import_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found"
        )
    
    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "total_rows": job.total_rows,
        "processed_rows": job.processed_rows,
        "success_count": job.success_count,
        "error_count": job.error_count,
        "errors": job.errors,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }


@router.post("/import/{job_id}/validate")
def validate_import(
    job_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Validate import data before processing.
    """
    PermissionService.require_permission(current_user.role, "kols", "create")
    
    from app.services.import_service import ImportService
    import_service = ImportService(db)
    
    job = import_service.validate_import_data(job_id)
    
    return {
        "job_id": job.id,
        "status": job.status,
        "error_count": job.error_count,
        "errors": job.errors,
        "message": "Validation completed" if job.error_count == 0 else f"Validation failed with {job.error_count} errors"
    }


@router.post("/import/{job_id}/process")
def process_import(
    job_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Process validated import data and create KOL records.
    """
    PermissionService.require_permission(current_user.role, "kols", "create")
    
    from app.services.import_service import ImportService
    import_service = ImportService(db)
    
    job = import_service.process_import(job_id)
    
    return {
        "job_id": job.id,
        "status": job.status,
        "success_count": job.success_count,
        "error_count": job.error_count,
        "message": f"Import completed. {job.success_count} KOLs created successfully" if job.status == "completed" else f"Import failed with {job.error_count} errors"
    }


@router.get("/{kol_id}/duplicates")
def find_duplicates(
    kol_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Find potential duplicate KOLs with match confidence and reasons.
    """
    PermissionService.require_permission(current_user.role, "kols", "read")
    
    kol_service = KOLService(db)
    duplicates = kol_service.find_duplicates(kol_id)
    
    return {
        "kol_id": kol_id,
        "duplicate_count": len(duplicates),
        "duplicates": [
            {
                "id": dup_data['kol'].id,
                "name": dup_data['kol'].name,
                "email": dup_data['kol'].email,
                "created_at": dup_data['kol'].created_at,
                "confidence": dup_data['confidence'],
                "match_reasons": dup_data['match_reasons']
            }
            for dup_data in duplicates
        ]
    }


@router.post("/{kol_id}/validate")
def validate_kol(
    kol_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Validate KOL data and check for issues.
    """
    PermissionService.require_permission(current_user.role, "kols", "read")
    
    kol_service = KOLService(db)
    kol = kol_service.get_kol(kol_id)
    
    if not kol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KOL not found"
        )
    
    validation_results = {
        "kol_id": kol_id,
        "is_valid": True,
        "warnings": [],
        "errors": []
    }
    
    # Check for missing email
    if not kol.email:
        validation_results["warnings"].append("Email address is missing")
    
    # Check for missing phone
    if not kol.phone:
        validation_results["warnings"].append("Phone number is missing")
    
    # Check for social handles
    if not kol.social_handles:
        validation_results["errors"].append("No social media handles found")
        validation_results["is_valid"] = False
    
    # Check for duplicates
    duplicates = kol_service.find_duplicates(kol_id)
    if duplicates:
        validation_results["warnings"].append(f"Found {len(duplicates)} potential duplicates")
    
    # Check if can be deleted
    try:
        kol_service.validate_kol_deletion(kol_id)
        validation_results["can_delete"] = True
    except HTTPException:
        validation_results["can_delete"] = False
        validation_results["warnings"].append("Cannot delete KOL due to active campaigns")
    
    return validation_results


@router.get("/duplicates/scan")
def scan_all_duplicates(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Scan all KOLs for potential duplicates (Admin only).
    """
    PermissionService.require_permission(current_user.role, "kols", "read")
    
    # Only allow admins to run full scan
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can run full duplicate scan"
        )
    
    kol_service = KOLService(db)
    scan_results = kol_service.scan_all_duplicates()
    
    return scan_results


@router.post("/{primary_kol_id}/merge/{duplicate_kol_id}", response_model=KOLResponse)
def merge_kols(
    primary_kol_id: int,
    duplicate_kol_id: int,
    merge_data: Optional[KOLUpdate] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Merge duplicate KOL into primary KOL.
    """
    PermissionService.require_permission(current_user.role, "kols", "update")
    
    # Only allow admins and campaign managers to merge
    if current_user.role not in ["admin", "campaign_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and campaign managers can merge KOLs"
        )
    
    kol_service = KOLService(db)
    
    merge_dict = merge_data.dict(exclude_unset=True) if merge_data else {}
    merged_kol = kol_service.merge_kols(primary_kol_id, duplicate_kol_id, merge_dict)
    
    return merged_kol