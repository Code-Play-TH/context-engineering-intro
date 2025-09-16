"""
Master Data API endpoints.

Handles CRUD operations for Material Code and Color Code master data.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.master_data import MaterialCode, ColorCode
from app.models.atp_master_data import ATPMaterialCode, ATPColorCode
from app.schemas.master_data import (
    MaterialCodeCreate,
    MaterialCodeUpdate,
    MaterialCodeResponse,
    MaterialCodeSummary,
    ColorCodeCreate,
    ColorCodeUpdate,
    ColorCodeResponse,
    ColorCodeSummary,
    MaterialCodeBulkImportRequest,
    ColorCodeBulkImportRequest,
    MasterDataImportResponse,
)
from app.schemas.atp_master_data import (
    ATPMaterialCodeResponse,
    ATPMaterialCodeSummary,
    ATPColorCodeResponse,
    ATPColorCodeSummary,
    ATPExcelProcessingResult,
    ATPMasterDataImportResponse,
)
from app.services.atp_excel_import import atp_excel_import_service

router = APIRouter()


# Material Code endpoints
@router.get("/material-codes", response_model=List[MaterialCodeSummary])
async def list_material_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[MaterialCodeSummary]:
    """
    Get list of material codes with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for material code or name
        category: Filter by material category
        active_only: Include only active records
        db: Database session
        current_user: Current user
        
    Returns:
        List[MaterialCodeSummary]: List of material codes
    """
    query = select(MaterialCode)
    
    # Apply filters
    if active_only:
        query = query.where(MaterialCode.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (MaterialCode.material_code.ilike(search_term)) |
            (MaterialCode.material_name.ilike(search_term))
        )
    
    if category:
        query = query.where(MaterialCode.material_category == category)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/material-codes/{material_code_id}", response_model=MaterialCodeResponse)
async def get_material_code(
    material_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MaterialCodeResponse:
    """Get material code by ID."""
    result = await db.execute(
        select(MaterialCode).where(MaterialCode.id == material_code_id)
    )
    material_code = result.scalar_one_or_none()
    
    if not material_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material code not found"
        )
    
    return material_code


@router.post("/material-codes", response_model=MaterialCodeResponse)
async def create_material_code(
    material_data: MaterialCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MaterialCodeResponse:
    """Create new material code."""
    # Check if material code already exists
    existing = await db.execute(
        select(MaterialCode).where(MaterialCode.material_code == material_data.material_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material code already exists"
        )
    
    material_code = MaterialCode(**material_data.model_dump())
    db.add(material_code)
    await db.commit()
    await db.refresh(material_code)
    
    return material_code


@router.put("/material-codes/{material_code_id}", response_model=MaterialCodeResponse)
async def update_material_code(
    material_code_id: int,
    material_data: MaterialCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MaterialCodeResponse:
    """Update material code."""
    result = await db.execute(
        select(MaterialCode).where(MaterialCode.id == material_code_id)
    )
    material_code = result.scalar_one_or_none()
    
    if not material_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material code not found"
        )
    
    update_data = material_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material_code, field, value)
    
    material_code.touch()
    await db.commit()
    await db.refresh(material_code)
    
    return material_code


@router.delete("/material-codes/{material_code_id}")
async def delete_material_code(
    material_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """Delete (deactivate) material code."""
    result = await db.execute(
        select(MaterialCode).where(MaterialCode.id == material_code_id)
    )
    material_code = result.scalar_one_or_none()
    
    if not material_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material code not found"
        )
    
    material_code.is_active = False
    material_code.touch()
    await db.commit()
    
    return {"message": "Material code deleted successfully"}


# Color Code endpoints
@router.get("/color-codes", response_model=List[ColorCodeSummary])
async def list_color_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    color_family: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ColorCodeSummary]:
    """Get list of color codes with optional filtering."""
    query = select(ColorCode)
    
    # Apply filters
    if active_only:
        query = query.where(ColorCode.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (ColorCode.color_code.ilike(search_term)) |
            (ColorCode.color_name.ilike(search_term))
        )
    
    if color_family:
        query = query.where(ColorCode.color_family == color_family)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/color-codes/{color_code_id}", response_model=ColorCodeResponse)
async def get_color_code(
    color_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ColorCodeResponse:
    """Get color code by ID."""
    result = await db.execute(
        select(ColorCode).where(ColorCode.id == color_code_id)
    )
    color_code = result.scalar_one_or_none()
    
    if not color_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color code not found"
        )
    
    return color_code


@router.post("/color-codes", response_model=ColorCodeResponse)
async def create_color_code(
    color_data: ColorCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ColorCodeResponse:
    """Create new color code."""
    # Check if color code already exists
    existing = await db.execute(
        select(ColorCode).where(ColorCode.color_code == color_data.color_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Color code already exists"
        )
    
    color_code = ColorCode(**color_data.model_dump())
    db.add(color_code)
    await db.commit()
    await db.refresh(color_code)
    
    return color_code


@router.put("/color-codes/{color_code_id}", response_model=ColorCodeResponse)
async def update_color_code(
    color_code_id: int,
    color_data: ColorCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ColorCodeResponse:
    """Update color code."""
    result = await db.execute(
        select(ColorCode).where(ColorCode.id == color_code_id)
    )
    color_code = result.scalar_one_or_none()
    
    if not color_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color code not found"
        )
    
    update_data = color_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(color_code, field, value)
    
    color_code.touch()
    await db.commit()
    await db.refresh(color_code)
    
    return color_code


@router.delete("/color-codes/{color_code_id}")
async def delete_color_code(
    color_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """Delete (deactivate) color code."""
    result = await db.execute(
        select(ColorCode).where(ColorCode.id == color_code_id)
    )
    color_code = result.scalar_one_or_none()
    
    if not color_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color code not found"
        )
    
    color_code.is_active = False
    color_code.touch()
    await db.commit()
    
    return {"message": "Color code deleted successfully"}


# Bulk import endpoints
@router.post("/material-codes/bulk-import", response_model=MasterDataImportResponse)
async def bulk_import_material_codes(
    import_data: MaterialCodeBulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MasterDataImportResponse:
    """Bulk import material codes."""
    total_processed = len(import_data.material_codes)
    created = 0
    updated = 0
    errors = []
    
    for i, material_data in enumerate(import_data.material_codes):
        try:
            # Check if exists
            existing = await db.execute(
                select(MaterialCode).where(MaterialCode.material_code == material_data.material_code)
            )
            existing_material = existing.scalar_one_or_none()
            
            if existing_material:
                if import_data.update_existing:
                    # Update existing
                    update_data = material_data.model_dump(exclude={"material_code"})
                    for field, value in update_data.items():
                        setattr(existing_material, field, value)
                    existing_material.touch()
                    updated += 1
                else:
                    errors.append({
                        "row": i + 1,
                        "material_code": material_data.material_code,
                        "error": "Material code already exists"
                    })
            else:
                # Create new
                material_code = MaterialCode(**material_data.model_dump())
                db.add(material_code)
                created += 1
                
        except Exception as e:
            errors.append({
                "row": i + 1,
                "material_code": material_data.material_code,
                "error": str(e)
            })
    
    await db.commit()
    
    success_rate = ((created + updated) / total_processed) * 100 if total_processed > 0 else 0
    
    return MasterDataImportResponse(
        total_processed=total_processed,
        created=created,
        updated=updated,
        errors=errors,
        success_rate=success_rate
    )


@router.post("/color-codes/bulk-import", response_model=MasterDataImportResponse)
async def bulk_import_color_codes(
    import_data: ColorCodeBulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MasterDataImportResponse:
    """Bulk import color codes."""
    total_processed = len(import_data.color_codes)
    created = 0
    updated = 0
    errors = []
    
    for i, color_data in enumerate(import_data.color_codes):
        try:
            # Check if exists
            existing = await db.execute(
                select(ColorCode).where(ColorCode.color_code == color_data.color_code)
            )
            existing_color = existing.scalar_one_or_none()
            
            if existing_color:
                if import_data.update_existing:
                    # Update existing
                    update_data = color_data.model_dump(exclude={"color_code"})
                    for field, value in update_data.items():
                        setattr(existing_color, field, value)
                    existing_color.touch()
                    updated += 1
                else:
                    errors.append({
                        "row": i + 1,
                        "color_code": color_data.color_code,
                        "error": "Color code already exists"
                    })
            else:
                # Create new
                color_code = ColorCode(**color_data.model_dump())
                db.add(color_code)
                created += 1
                
        except Exception as e:
            errors.append({
                "row": i + 1,
                "color_code": color_data.color_code,
                "error": str(e)
            })
    
    await db.commit()
    
    success_rate = ((created + updated) / total_processed) * 100 if total_processed > 0 else 0
    
    return MasterDataImportResponse(
        total_processed=total_processed,
        created=created,
        updated=updated,
        errors=errors,
        success_rate=success_rate
    )