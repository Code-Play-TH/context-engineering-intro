"""
ATP Product API endpoints.

Handles ATP-specific product operations including Excel import from
Product Info Database sheet.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.atp_product import ATPProduct, ATPProductionStep
from app.models.atp_master_data import ATPMaterialCode, ATPColorCode
from app.schemas.atp_product import (
    ATPProductResponse,
    ATPProductSummary,
    ATPProductDetailResponse,
    ATPProductCreate,
    ATPProductUpdate,
    ATPProductSearchResult,
    ATPProductProcessingResult,
    ATPProductImportResponse,
    ATPProductionAnalytics,
    ATPMaterialUsageReport,
    ATPProductionStepResponse,
)
from app.services.atp_product_import import atp_product_import_service

router = APIRouter()


# Product listing and search
@router.get("/products", response_model=ATPProductSearchResult)
async def search_atp_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    material_code: Optional[str] = Query(None),
    complexity_level: Optional[str] = Query(None),
    color_code: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductSearchResult:
    """
    Search ATP products with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for part number, name, or drawing number
        material_code: Filter by material code
        complexity_level: Filter by complexity (Simple, Medium, Complex)
        color_code: Filter by color code
        active_only: Include only active records
        db: Database session
        current_user: Current user
        
    Returns:
        ATPProductSearchResult: Search results with pagination info
    """
    # Build base query
    query = select(ATPProduct)
    count_query = select(func.count(ATPProduct.id))
    
    # Apply filters
    if active_only:
        query = query.where(ATPProduct.is_active == True)
        count_query = count_query.where(ATPProduct.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        search_condition = (
            (ATPProduct.part_no.ilike(search_term)) |
            (ATPProduct.part_name.ilike(search_term)) |
            (ATPProduct.drawing_no.ilike(search_term))
        )
        query = query.where(search_condition)
        count_query = count_query.where(search_condition)
    
    if material_code:
        query = query.where(ATPProduct.material_code == material_code)
        count_query = count_query.where(ATPProduct.material_code == material_code)
    
    if complexity_level:
        query = query.where(ATPProduct.complexity_level == complexity_level)
        count_query = count_query.where(ATPProduct.complexity_level == complexity_level)
    
    if color_code:
        query = query.where(ATPProduct.color_code == color_code)
        count_query = count_query.where(ATPProduct.color_code == color_code)
    
    # Get total count
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(ATPProduct.part_no)
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Convert to summary format
    product_summaries = [
        ATPProductSummary(
            id=p.id,
            part_no=p.part_no,
            part_name=p.part_name or "",
            material_code=p.material_code,
            total_steps=p.total_steps,
            complexity_level=p.complexity_level,
            color_description=p.color_description,
            is_active=p.is_active
        )
        for p in products
    ]
    
    page = (skip // limit) + 1 if limit > 0 else 1
    has_more = (skip + limit) < total_count
    
    return ATPProductSearchResult(
        products=product_summaries,
        total_count=total_count,
        page=page,
        per_page=limit,
        has_more=has_more
    )


@router.get("/products/{product_id}", response_model=ATPProductDetailResponse)
async def get_atp_product_detail(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductDetailResponse:
    """Get detailed ATP product information with relationships."""
    # Get product with relationships
    query = select(ATPProduct).where(ATPProduct.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP product not found"
        )
    
    # Get material code details
    material_info = None
    if product.atp_material_code_id:
        material_result = await db.execute(
            select(ATPMaterialCode).where(ATPMaterialCode.id == product.atp_material_code_id)
        )
        material = material_result.scalar_one_or_none()
        if material:
            material_info = {
                "id": material.id,
                "atp_code": material.atp_code,
                "material_code": material.material_code,
                "description_th": material.description_th,
                "grade": material.grade,
                "weight_per_line": material.weight_per_line
            }
    
    # Get color code details
    color_info = None
    if product.atp_color_code_id:
        color_result = await db.execute(
            select(ATPColorCode).where(ATPColorCode.id == product.atp_color_code_id)
        )
        color = color_result.scalar_one_or_none()
        if color:
            color_info = {
                "id": color.id,
                "color_code": color.color_code,
                "color_name": color.color_name,
                "color_type": color.color_type,
                "is_raw_material": color.is_raw_material
            }
    
    # Get production steps
    steps_result = await db.execute(
        select(ATPProductionStep)
        .where(ATPProductionStep.atp_product_id == product.id)
        .order_by(ATPProductionStep.step_number)
    )
    production_steps = [
        ATPProductionStepResponse.model_validate(step)
        for step in steps_result.scalars().all()
    ]
    
    # Create detailed response
    response_data = ATPProductResponse.model_validate(product).model_dump()
    response_data.update({
        "atp_material_code": material_info,
        "atp_color_code": color_info,
        "production_steps": production_steps,
        "production_summary": product.get_production_summary()
    })
    
    return ATPProductDetailResponse(**response_data)


@router.post("/products", response_model=ATPProductResponse)
async def create_atp_product(
    product_data: ATPProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductResponse:
    """Create new ATP product."""
    # Check if part number already exists
    existing = await db.execute(
        select(ATPProduct).where(ATPProduct.part_no == product_data.part_no)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Part number already exists"
        )
    
    # Create product
    product_dict = product_data.model_dump(exclude={"process_steps", "specifications"})
    product = ATPProduct(**product_dict)
    
    # Set process steps and specifications
    if product_data.process_steps:
        product.process_steps = product_data.process_steps
    if product_data.specifications:
        product.specifications = product_data.specifications
    
    # Set complexity level
    product.update_complexity_level()
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    return ATPProductResponse.model_validate(product)


@router.put("/products/{product_id}", response_model=ATPProductResponse)
async def update_atp_product(
    product_id: int,
    product_data: ATPProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductResponse:
    """Update ATP product."""
    result = await db.execute(
        select(ATPProduct).where(ATPProduct.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP product not found"
        )
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    process_steps = update_data.pop("process_steps", None)
    specifications = update_data.pop("specifications", None)
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    # Update process steps and specifications if provided
    if process_steps is not None:
        product.process_steps = process_steps
    if specifications is not None:
        product.specifications = specifications
    
    # Update complexity level if steps changed
    if product_data.total_steps is not None:
        product.update_complexity_level()
    
    product.touch()
    await db.commit()
    await db.refresh(product)
    
    return ATPProductResponse.model_validate(product)


@router.delete("/products/{product_id}")
async def delete_atp_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """Delete (deactivate) ATP product."""
    result = await db.execute(
        select(ATPProduct).where(ATPProduct.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATP product not found"
        )
    
    product.is_active = False
    product.touch()
    await db.commit()
    
    return {"message": "ATP product deleted successfully"}


# Excel import endpoints
@router.post("/excel-import", response_model=ATPProductImportResponse)
async def import_atp_products_from_excel(
    update_existing: bool = Query(False, description="Update existing records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductImportResponse:
    """
    Import ATP products from Product Info Database Excel sheet.
    
    Processes the complete product data including material relationships
    and production process information.
    """
    try:
        # Process the Excel file
        excel_file_path = "examples/Product Info Database.xlsx"
        processing_result = atp_product_import_service.process_excel_file(excel_file_path)
        
        if processing_result.processing_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excel processing errors: {', '.join(processing_result.processing_errors)}"
            )
        
        # Import products
        import_result = await atp_product_import_service.import_products(
            processing_result.products, db, update_existing
        )
        
        return import_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/excel-preview", response_model=ATPProductProcessingResult)
async def preview_atp_products_from_excel(
    limit: int = Query(10, ge=1, le=100, description="Number of products to preview"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductProcessingResult:
    """
    Preview ATP products from Excel without importing.
    
    Shows sample data from Product Info Database sheet for review
    before actual import.
    """
    try:
        # Process the Excel file
        excel_file_path = "examples/Product Info Database.xlsx"
        processing_result = atp_product_import_service.process_excel_file(excel_file_path)
        
        # Limit results for preview
        if processing_result.products:
            processing_result.products = processing_result.products[:limit]
            processing_result.products_found = len(processing_result.products)
        
        return processing_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


# Analytics endpoints
@router.get("/analytics", response_model=ATPProductionAnalytics)
async def get_atp_production_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ATPProductionAnalytics:
    """Get ATP production analytics and statistics."""
    # Get total products
    total_result = await db.execute(
        select(func.count(ATPProduct.id)).where(ATPProduct.is_active == True)
    )
    total_products = total_result.scalar() or 0
    
    # Get complexity breakdown
    complexity_result = await db.execute(
        select(ATPProduct.complexity_level, func.count(ATPProduct.id))
        .where(ATPProduct.is_active == True)
        .group_by(ATPProduct.complexity_level)
    )
    by_complexity = {
        complexity or "Unknown": count 
        for complexity, count in complexity_result.fetchall()
    }
    
    # Get material type breakdown (simplified)
    material_result = await db.execute(
        select(ATPProduct.material_code, func.count(ATPProduct.id))
        .where(ATPProduct.is_active == True)
        .where(ATPProduct.material_code.isnot(None))
        .group_by(ATPProduct.material_code)
        .limit(10)
    )
    by_material_type = {
        material: count 
        for material, count in material_result.fetchall()
    }
    
    # Get color breakdown
    color_result = await db.execute(
        select(ATPProduct.color_code, func.count(ATPProduct.id))
        .where(ATPProduct.is_active == True)
        .where(ATPProduct.color_code.isnot(None))
        .group_by(ATPProduct.color_code)
    )
    by_color = {
        color: count 
        for color, count in color_result.fetchall()
    }
    
    # Get average steps
    avg_steps_result = await db.execute(
        select(func.avg(ATPProduct.total_steps))
        .where(ATPProduct.is_active == True)
        .where(ATPProduct.total_steps.isnot(None))
    )
    avg_steps = avg_steps_result.scalar() or 0.0
    
    return ATPProductionAnalytics(
        total_products=total_products,
        by_complexity=by_complexity,
        by_material_type=by_material_type,
        by_color=by_color,
        avg_steps_per_product=round(avg_steps, 2),
        total_production_time_minutes=0  # Would need step time data
    )