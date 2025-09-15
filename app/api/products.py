"""
Product management API endpoints.

Handles product CRUD operations, production steps, and product lookups.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, or_

from app.api.deps import (
    get_db,
    get_current_active_user,
    require_admin_access,
)
from app.models.product import Product, ProductionStep
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductSummary,
    ProductLookup,
    ProductSearchRequest,
    ProductionStepCreate,
    ProductionStepUpdate,
    ProductionStepResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ProductSummary])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    part_no: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductSummary]:
    """
    Get list of products with filtering options.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        part_no: Filter by part number (partial match)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ProductSummary]: List of products
    """
    statement = select(Product)
    
    # Apply filters
    filters = []
    if is_active is not None:
        filters.append(Product.is_active == is_active)
    if part_no:
        filters.append(Product.part_no.ilike(f"%{part_no}%"))
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.offset(skip).limit(limit)
    
    result = await db.execute(statement)
    products = result.scalars().all()
    
    return [ProductSummary.model_validate(product) for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """
    Get product by ID with production steps.
    
    Args:
        product_id: Product ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductResponse: Product data with production steps
        
    Raises:
        HTTPException: If product not found
    """
    # Get product with production steps
    product_statement = select(Product).where(Product.id == product_id)
    result = await db.execute(product_statement)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get production steps
    steps_statement = (
        select(ProductionStep)
        .where(ProductionStep.product_id == product_id, ProductionStep.is_active == True)
        .order_by(ProductionStep.step_number)
    )
    steps_result = await db.execute(steps_statement)
    production_steps = steps_result.scalars().all()
    
    # Create response with calculated fields
    response_data = ProductResponse.model_validate(product)
    response_data.total_production_time = product.get_total_production_time()
    response_data.production_steps = [
        ProductionStepResponse.model_validate(step) for step in production_steps
    ]
    
    return response_data


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """
    Create new product with optional production steps.
    
    Args:
        product_data: Product creation data
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ProductResponse: Created product
        
    Raises:
        HTTPException: If part number already exists
    """
    # Check if part number already exists
    existing_product = await db.execute(
        select(Product).where(Product.part_no == product_data.part_no)
    )
    if existing_product.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Part number already exists"
        )
    
    # Create product
    product_dict = product_data.model_dump(exclude={"production_steps", "specifications"})
    db_product = Product(**product_dict)
    
    # Set specifications
    if product_data.specifications:
        db_product.specifications = product_data.specifications
    
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Create production steps if provided
    for step_data in product_data.production_steps:
        db_step = ProductionStep(
            product_id=db_product.id,
            **step_data.model_dump()
        )
        db.add(db_step)
    
    await db.commit()
    
    # Return product with steps
    return await get_product(db_product.id, current_user, db)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """
    Update product information.
    
    Args:
        product_id: Product ID to update
        product_data: Product update data
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ProductResponse: Updated product
        
    Raises:
        HTTPException: If product not found
    """
    # Get product
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True, exclude={"specifications"})
    for field, value in update_data.items():
        setattr(product, field, value)
    
    # Update specifications if provided
    if product_data.specifications is not None:
        product.specifications = product_data.specifications
    
    product.touch()
    await db.commit()
    
    # Return updated product
    return await get_product(product_id, current_user, db)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Soft delete product.
    
    Args:
        product_id: Product ID to delete
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If product not found
    """
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.soft_delete()
    await db.commit()
    
    return {"message": f"Product {product.part_no} deleted successfully"}


@router.post("/search", response_model=List[ProductLookup])
async def search_products(
    search_request: ProductSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductLookup]:
    """
    Search products for VLOOKUP functionality.
    
    Args:
        search_request: Search parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ProductLookup]: Matching products
    """
    query = search_request.query.lower()
    
    # Build search conditions
    search_conditions = []
    for field in search_request.search_fields:
        if hasattr(Product, field):
            column = getattr(Product, field)
            search_conditions.append(column.ilike(f"%{query}%"))
    
    if not search_conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid search fields specified"
        )
    
    statement = (
        select(Product)
        .where(
            and_(
                Product.is_active == True,
                or_(*search_conditions)
            )
        )
        .limit(search_request.limit)
    )
    
    result = await db.execute(statement)
    products = result.scalars().all()
    
    # Create lookup responses with calculated fields
    lookups = []
    for product in products:
        lookup = ProductLookup.model_validate(product)
        lookup.total_production_time = product.get_total_production_time()
        lookups.append(lookup)
    
    return lookups


@router.get("/{product_id}/lookup", response_model=ProductLookup)
async def get_product_lookup(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductLookup:
    """
    Get product lookup data by ID (for VLOOKUP functionality).
    
    Args:
        product_id: Product ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductLookup: Product lookup data
        
    Raises:
        HTTPException: If product not found
    """
    product = await db.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    lookup = ProductLookup.model_validate(product)
    lookup.total_production_time = product.get_total_production_time()
    
    return lookup


@router.get("/by-part-no/{part_no}/lookup", response_model=ProductLookup)
async def get_product_lookup_by_part_no(
    part_no: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductLookup:
    """
    Get product lookup data by part number (primary VLOOKUP functionality).
    
    Args:
        part_no: Product part number
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductLookup: Product lookup data
        
    Raises:
        HTTPException: If product not found
    """
    statement = select(Product).where(
        Product.part_no == part_no,
        Product.is_active == True
    )
    result = await db.execute(statement)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    lookup = ProductLookup.model_validate(product)
    lookup.total_production_time = product.get_total_production_time()
    
    return lookup


# Production step endpoints
@router.post("/{product_id}/steps/", response_model=ProductionStepResponse)
async def create_production_step(
    product_id: int,
    step_data: ProductionStepCreate,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> ProductionStepResponse:
    """
    Add production step to product.
    
    Args:
        product_id: Product ID
        step_data: Production step data
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ProductionStepResponse: Created production step
        
    Raises:
        HTTPException: If product not found
    """
    # Verify product exists
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Create production step
    step_data.product_id = product_id
    db_step = ProductionStep(**step_data.model_dump())
    
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)
    
    return ProductionStepResponse.model_validate(db_step)


@router.get("/{product_id}/steps/", response_model=List[ProductionStepResponse])
async def get_production_steps(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductionStepResponse]:
    """
    Get production steps for a product.
    
    Args:
        product_id: Product ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ProductionStepResponse]: Production steps
    """
    statement = (
        select(ProductionStep)
        .where(
            ProductionStep.product_id == product_id,
            ProductionStep.is_active == True
        )
        .order_by(ProductionStep.step_number)
    )
    
    result = await db.execute(statement)
    steps = result.scalars().all()
    
    return [ProductionStepResponse.model_validate(step) for step in steps]