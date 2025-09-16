"""
ATP Master Data API endpoints.

Handles ATP-specific Material Code and Color Code operations including Excel import.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.atp_master_data import ATPMaterialCode, ATPColorCode
from app.schemas.atp_master_data import (
    ATPMaterialCodeResponse,
    ATPMaterialCodeSummary,
    ATPMaterialCodeCreate,
    ATPMaterialCodeUpdate,
    ATPColorCodeResponse,
    ATPColorCodeSummary,
    ATPColorCodeCreate,
    ATPColorCodeUpdate,
    ATPExcelProcessingResult,
    ATPMasterDataImportResponse,
)
from app.services.atp_excel_import import atp_excel_import_service

router = APIRouter()


# ATP Material Code endpoints
@router.get("/material-codes", response_model=List[ATPMaterialCodeSummary])
async def list_atp_material_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ATPMaterialCodeSummary]:
    """
    Get list of ATP material codes with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for ATP code, material code, or Thai description
        active_only: Include only active records
        db: Database session
        current_user: Current user
        
    Returns:
        List[ATPMaterialCodeSummary]: List of ATP material codes
    """
    query = select(ATPMaterialCode)
    
    # Apply filters
    if active_only:
        query = query.where(ATPMaterialCode.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (ATPMaterialCode.atp_code.ilike(search_term)) |
            (ATPMaterialCode.material_code.ilike(search_term)) |
            (ATPMaterialCode.description_th.ilike(search_term))
        )
    
    query = query.offset(skip).limit(limit).order_by(ATPMaterialCode.atp_code)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/material-codes/{material_code_id}", response_model=ATPMaterialCodeResponse)
async def get_atp_material_code(
    material_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPMaterialCodeResponse:
    """Get ATP material code by ID."""
    result = await db.execute(
        select(ATPMaterialCode).where(ATPMaterialCode.id == material_code_id)
    )
    material_code = result.scalar_one_or_none()
    
    if not material_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP material code not found"
        )
    
    return material_code


@router.post("/material-codes", response_model=ATPMaterialCodeResponse)
async def create_atp_material_code(
    material_data: ATPMaterialCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPMaterialCodeResponse:
    """Create new ATP material code."""
    # Check if ATP code already exists
    existing = await db.execute(
        select(ATPMaterialCode).where(ATPMaterialCode.atp_code == material_data.atp_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ATP code already exists"
        )
    
    # Create material code
    material_code = ATPMaterialCode(**material_data.model_dump())
    db.add(material_code)
    await db.commit()
    await db.refresh(material_code)
    
    return material_code


@router.put("/material-codes/{material_code_id}", response_model=ATPMaterialCodeResponse)
async def update_atp_material_code(
    material_code_id: int,
    material_data: ATPMaterialCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPMaterialCodeResponse:
    """Update ATP material code."""
    result = await db.execute(
        select(ATPMaterialCode).where(ATPMaterialCode.id == material_code_id)
    )
    material_code = result.scalar_one_or_none()
    
    if not material_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP material code not found"
        )
    
    # Update fields
    update_data = material_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material_code, field, value)
    
    await db.commit()
    await db.refresh(material_code)
    
    return material_code


@router.delete("/material-codes/{material_code_id}")
async def delete_atp_material_code(
    material_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """Delete (deactivate) ATP material code."""
    result = await db.execute(
        select(ATPMaterialCode).where(ATPMaterialCode.id == material_code_id)
    )
    material_code = result.scalar_one_or_none()
    
    if not material_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP material code not found"
        )
    
    material_code.is_active = False
    await db.commit()
    
    return {"message": "ATP material code deleted successfully"}


# ATP Color Code endpoints
@router.get("/color-codes", response_model=List[ATPColorCodeSummary])
async def list_atp_color_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ATPColorCodeSummary]:
    """
    Get list of ATP color codes with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for color code or color name
        active_only: Include only active records
        db: Database session
        current_user: Current user
        
    Returns:
        List[ATPColorCodeSummary]: List of ATP color codes
    """
    query = select(ATPColorCode)
    
    # Apply filters
    if active_only:
        query = query.where(ATPColorCode.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (ATPColorCode.color_code.ilike(search_term)) |
            (ATPColorCode.color_name.ilike(search_term))
        )
    
    query = query.offset(skip).limit(limit).order_by(ATPColorCode.color_code)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/color-codes/{color_code_id}", response_model=ATPColorCodeResponse)
async def get_atp_color_code(
    color_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPColorCodeResponse:
    """Get ATP color code by ID."""
    result = await db.execute(
        select(ATPColorCode).where(ATPColorCode.id == color_code_id)
    )
    color_code = result.scalar_one_or_none()
    
    if not color_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP color code not found"
        )
    
    return color_code


@router.post("/color-codes", response_model=ATPColorCodeResponse)
async def create_atp_color_code(
    color_data: ATPColorCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPColorCodeResponse:
    """Create new ATP color code."""
    # Check if color code already exists
    existing = await db.execute(
        select(ATPColorCode).where(ATPColorCode.color_code == color_data.color_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Color code already exists"
        )
    
    # Create color code
    color_code = ATPColorCode(**color_data.model_dump())
    db.add(color_code)
    await db.commit()
    await db.refresh(color_code)
    
    return color_code


@router.put("/color-codes/{color_code_id}", response_model=ATPColorCodeResponse)
async def update_atp_color_code(
    color_code_id: int,
    color_data: ATPColorCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPColorCodeResponse:
    """Update ATP color code."""
    result = await db.execute(
        select(ATPColorCode).where(ATPColorCode.id == color_code_id)
    )
    color_code = result.scalar_one_or_none()
    
    if not color_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP color code not found"
        )
    
    # Update fields
    update_data = color_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(color_code, field, value)
    
    await db.commit()
    await db.refresh(color_code)
    
    return color_code


@router.delete("/color-codes/{color_code_id}")
async def delete_atp_color_code(
    color_code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """Delete (deactivate) ATP color code."""
    result = await db.execute(
        select(ATPColorCode).where(ATPColorCode.id == color_code_id)
    )
    color_code = result.scalar_one_or_none()
    
    if not color_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP color code not found"
        )
    
    color_code.is_active = False
    await db.commit()
    
    return {"message": "ATP color code deleted successfully"}


# Excel import endpoints
@router.post("/excel-import", response_model=ATPMasterDataImportResponse)
async def import_atp_excel_data(
    update_existing: bool = Query(False, description="Update existing records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPMasterDataImportResponse:
    """
    Import ATP master data from Excel file.
    
    Processes the 'Product Info Database.xlsx' file and imports Material Code
    and Color Code data into ATP-specific tables.
    
    Args:
        update_existing: Whether to update existing records
        db: Database session
        current_user: Current user
        
    Returns:
        ATPMasterDataImportResponse: Import results and statistics
    """
    try:
        # Process the Excel file
        excel_file_path = "examples/Product Info Database.xlsx"
        processing_result = atp_excel_import_service.process_excel_file(excel_file_path)
        
        if processing_result.processing_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excel processing errors: {', '.join(processing_result.processing_errors)}"
            )
        
        # Import material codes
        material_import_result = await atp_excel_import_service.import_material_codes(
            processing_result.material_codes, db, update_existing
        )
        
        # Import color codes  
        color_import_result = await atp_excel_import_service.import_color_codes(
            processing_result.color_codes, db, update_existing
        )
        
        # Combine results
        total_processed = material_import_result.total_processed + color_import_result.total_processed
        total_created = material_import_result.created + color_import_result.created
        total_updated = material_import_result.updated + color_import_result.updated
        all_errors = material_import_result.errors + color_import_result.errors
        
        success_rate = ((total_created + total_updated) / total_processed) * 100 if total_processed > 0 else 0
        
        return ATPMasterDataImportResponse(
            total_processed=total_processed,
            created=total_created,
            updated=total_updated,
            errors=all_errors,
            success_rate=success_rate
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/excel-preview", response_model=ATPExcelProcessingResult)
async def preview_atp_excel_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPExcelProcessingResult:
    """
    Preview ATP Excel data without importing.
    
    Processes the Excel file and returns what would be imported
    without actually saving to the database.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        ATPExcelProcessingResult: Processing results and data preview
    """
    try:
        # Process the Excel file
        excel_file_path = "examples/Product Info Database.xlsx"
        processing_result = atp_excel_import_service.process_excel_file(excel_file_path)
        
        return processing_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )