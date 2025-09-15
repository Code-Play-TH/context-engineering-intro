"""
Sales management API endpoints.

Handles customer requirements, customer management, and sales dashboard.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, or_, func, desc

from app.api.deps import (
    get_db,
    get_current_active_user,
    require_sales_access,
    require_admin_access,
)
from app.models.sales import Customer, CustomerRequirement
from app.models.product import Product
from app.models.user import User
from app.schemas.sales import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerSummary,
    CustomerRequirementCreate,
    CustomerRequirementUpdate,
    CustomerRequirementResponse,
    CustomerRequirementSummary,
    CustomerRequirementSearchRequest,
    CustomerRequirementBulkImportRequest,
    CustomerRequirementBulkImportResponse,
    DeliveryUpdate,
    SalesDashboardData,
)
from app.schemas.product import ProductLookup

router = APIRouter()


# Customer management endpoints
@router.get("/customers/", response_model=List[CustomerSummary])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    customer_name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[CustomerSummary]:
    """
    Get list of customers with filtering options.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        customer_name: Filter by customer name (partial match)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CustomerSummary]: List of customers
    """
    statement = select(Customer)
    
    # Apply filters
    filters = []
    if is_active is not None:
        filters.append(Customer.is_active == is_active)
    if customer_name:
        filters.append(Customer.customer_name.ilike(f"%{customer_name}%"))
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.offset(skip).limit(limit)
    
    result = await db.execute(statement)
    customers = result.scalars().all()
    
    return [CustomerSummary.model_validate(customer) for customer in customers]


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """
    Get customer by ID.
    
    Args:
        customer_id: Customer ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CustomerResponse: Customer data
        
    Raises:
        HTTPException: If customer not found
    """
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return CustomerResponse.model_validate(customer)


@router.post("/customers/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(require_sales_access),
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """
    Create new customer.
    
    Args:
        customer_data: Customer creation data
        current_user: Current authenticated sales user
        db: Database session
        
    Returns:
        CustomerResponse: Created customer
        
    Raises:
        HTTPException: If customer code already exists
    """
    # Check if customer code already exists
    existing_customer = await db.execute(
        select(Customer).where(Customer.customer_code == customer_data.customer_code)
    )
    if existing_customer.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer code already exists"
        )
    
    # Create customer
    db_customer = Customer(**customer_data.model_dump())
    
    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)
    
    return CustomerResponse.model_validate(db_customer)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    current_user: User = Depends(require_sales_access),
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """
    Update customer information.
    
    Args:
        customer_id: Customer ID to update
        customer_data: Customer update data
        current_user: Current authenticated sales user
        db: Database session
        
    Returns:
        CustomerResponse: Updated customer
        
    Raises:
        HTTPException: If customer not found
    """
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Update fields
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.touch()
    await db.commit()
    
    return CustomerResponse.model_validate(customer)


# Customer requirement endpoints
@router.get("/requirements/", response_model=List[CustomerRequirementSummary])
async def get_customer_requirements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    shortage_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[CustomerRequirementSummary]:
    """
    Get list of customer requirements with filtering options.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        overdue_only: Show only overdue requirements
        shortage_only: Show only requirements with shortage
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CustomerRequirementSummary]: List of customer requirements
    """
    # Base query with joins
    statement = (
        select(CustomerRequirement, Product)
        .join(Product, CustomerRequirement.product_id == Product.id)
        .where(CustomerRequirement.is_active == True)
    )
    
    # Apply filters
    filters = []
    if status:
        filters.append(CustomerRequirement.status == status)
    if overdue_only:
        filters.append(CustomerRequirement.due_date < datetime.utcnow())
    if shortage_only:
        filters.append(CustomerRequirement.delivered_quantity < CustomerRequirement.po_quantity)
    
    # Department access control
    if current_user.department.name != "Admin":
        if current_user.department.name == "Sales":
            filters.append(CustomerRequirement.sales_person_id == current_user.id)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.order_by(desc(CustomerRequirement.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(statement)
    rows = result.all()
    
    # Create summary responses
    summaries = []
    for req, product in rows:
        summary = CustomerRequirementSummary(
            id=req.id,
            sale_no=req.sale_no,
            po_no=req.po_no,
            customer_name=req.customer_name,
            product_part_no=product.part_no,
            product_part_name=product.part_name,
            due_date=req.due_date,
            po_quantity=req.po_quantity,
            delivered_quantity=req.delivered_quantity,
            shortage_surplus=req.shortage_surplus,
            summary_status=req.summary_status,
            status=req.status,
            is_overdue=req.is_overdue
        )
        summaries.append(summary)
    
    return summaries


@router.get("/requirements/{requirement_id}", response_model=CustomerRequirementResponse)
async def get_customer_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerRequirementResponse:
    """
    Get customer requirement by ID with product and customer data.
    
    Args:
        requirement_id: Customer requirement ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CustomerRequirementResponse: Customer requirement data
        
    Raises:
        HTTPException: If requirement not found or access denied
    """
    # Get requirement with product
    statement = (
        select(CustomerRequirement, Product, Customer)
        .join(Product, CustomerRequirement.product_id == Product.id)
        .outerjoin(Customer, CustomerRequirement.customer_id == Customer.id)
        .where(CustomerRequirement.id == requirement_id)
    )
    
    result = await db.execute(statement)
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer requirement not found"
        )
    
    req, product, customer = row
    
    # Access control
    if current_user.department.name == "Sales" and req.sales_person_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this requirement"
        )
    
    # Create response with calculated fields
    response = CustomerRequirementResponse.model_validate(req)
    response.shortage_surplus = req.shortage_surplus
    response.summary_status = req.summary_status
    response.total_value = req.total_value
    response.delivery_percentage = req.delivery_percentage
    response.is_overdue = req.is_overdue
    
    # Add related data
    response.product = ProductLookup.model_validate(product)
    response.product.total_production_time = product.get_total_production_time()
    
    if customer:
        response.customer_data = CustomerSummary.model_validate(customer)
    
    return response


@router.post("/requirements/", response_model=CustomerRequirementResponse)
async def create_customer_requirement(
    requirement_data: CustomerRequirementCreate,
    current_user: User = Depends(require_sales_access),
    db: AsyncSession = Depends(get_db)
) -> CustomerRequirementResponse:
    """
    Create new customer requirement.
    
    Args:
        requirement_data: Customer requirement creation data
        current_user: Current authenticated sales user
        db: Database session
        
    Returns:
        CustomerRequirementResponse: Created customer requirement
        
    Raises:
        HTTPException: If product not found or sale_no already exists
    """
    # Verify product exists
    product = await db.get(Product, requirement_data.product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found or inactive"
        )
    
    # Check if sale number already exists
    existing_req = await db.execute(
        select(CustomerRequirement).where(CustomerRequirement.sale_no == requirement_data.sale_no)
    )
    if existing_req.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale number already exists"
        )
    
    # Create requirement
    req_dict = requirement_data.model_dump()
    req_dict["sales_person_id"] = current_user.id
    
    db_requirement = CustomerRequirement(**req_dict)
    
    db.add(db_requirement)
    await db.commit()
    await db.refresh(db_requirement)
    
    # Return full requirement data
    return await get_customer_requirement(db_requirement.id, current_user, db)


@router.put("/requirements/{requirement_id}", response_model=CustomerRequirementResponse)
async def update_customer_requirement(
    requirement_id: int,
    requirement_data: CustomerRequirementUpdate,
    current_user: User = Depends(require_sales_access),
    db: AsyncSession = Depends(get_db)
) -> CustomerRequirementResponse:
    """
    Update customer requirement.
    
    Args:
        requirement_id: Customer requirement ID to update
        requirement_data: Customer requirement update data
        current_user: Current authenticated sales user
        db: Database session
        
    Returns:
        CustomerRequirementResponse: Updated customer requirement
        
    Raises:
        HTTPException: If requirement not found or access denied
    """
    requirement = await db.get(CustomerRequirement, requirement_id)
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer requirement not found"
        )
    
    # Access control
    if current_user.department.name == "Sales" and requirement.sales_person_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this requirement"
        )
    
    # Update fields
    update_data = requirement_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement, field, value)
    
    requirement.touch()
    await db.commit()
    
    return await get_customer_requirement(requirement_id, current_user, db)


@router.patch("/requirements/{requirement_id}/delivery", response_model=CustomerRequirementResponse)
async def update_delivery_quantity(
    requirement_id: int,
    delivery_data: DeliveryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerRequirementResponse:
    """
    Update delivered quantity for customer requirement.
    
    Args:
        requirement_id: Customer requirement ID
        delivery_data: Delivery update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CustomerRequirementResponse: Updated customer requirement
        
    Raises:
        HTTPException: If requirement not found or invalid quantity
    """
    requirement = await db.get(CustomerRequirement, requirement_id)
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer requirement not found"
        )
    
    # Validate delivered quantity
    if delivery_data.delivered_quantity > requirement.po_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivered quantity cannot exceed PO quantity"
        )
    
    # Update delivery
    requirement.delivered_quantity = delivery_data.delivered_quantity
    
    if delivery_data.delivery_note:
        current_notes = requirement.notes or ""
        requirement.notes = f"{current_notes}\nDelivery: {delivery_data.delivery_note}".strip()
    
    # Auto-update status
    if requirement.delivered_quantity >= requirement.po_quantity:
        requirement.status = "completed"
    elif requirement.delivered_quantity > 0:
        requirement.status = "partial"
    
    requirement.touch()
    await db.commit()
    
    return await get_customer_requirement(requirement_id, current_user, db)


@router.post("/requirements/search", response_model=List[CustomerRequirementSummary])
async def search_customer_requirements(
    search_request: CustomerRequirementSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[CustomerRequirementSummary]:
    """
    Search customer requirements with advanced filters.
    
    Args:
        search_request: Search parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CustomerRequirementSummary]: Matching customer requirements
    """
    # Base query
    statement = (
        select(CustomerRequirement, Product)
        .join(Product, CustomerRequirement.product_id == Product.id)
        .where(CustomerRequirement.is_active == True)
    )
    
    # Apply search filters
    filters = []
    
    if search_request.customer_name:
        filters.append(CustomerRequirement.customer_name.ilike(f"%{search_request.customer_name}%"))
    
    if search_request.sale_no:
        filters.append(CustomerRequirement.sale_no.ilike(f"%{search_request.sale_no}%"))
    
    if search_request.po_no:
        filters.append(CustomerRequirement.po_no.ilike(f"%{search_request.po_no}%"))
    
    if search_request.status:
        filters.append(CustomerRequirement.status == search_request.status)
    
    if search_request.date_from:
        filters.append(CustomerRequirement.due_date >= search_request.date_from)
    
    if search_request.date_to:
        filters.append(CustomerRequirement.due_date <= search_request.date_to)
    
    if search_request.overdue_only:
        filters.append(CustomerRequirement.due_date < datetime.utcnow())
    
    if search_request.shortage_only:
        filters.append(CustomerRequirement.delivered_quantity < CustomerRequirement.po_quantity)
    
    # Department access control
    if current_user.department.name == "Sales":
        filters.append(CustomerRequirement.sales_person_id == current_user.id)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.order_by(desc(CustomerRequirement.created_at)).limit(100)
    
    result = await db.execute(statement)
    rows = result.all()
    
    # Create summary responses
    summaries = []
    for req, product in rows:
        summary = CustomerRequirementSummary(
            id=req.id,
            sale_no=req.sale_no,
            po_no=req.po_no,
            customer_name=req.customer_name,
            product_part_no=product.part_no,
            product_part_name=product.part_name,
            due_date=req.due_date,
            po_quantity=req.po_quantity,
            delivered_quantity=req.delivered_quantity,
            shortage_surplus=req.shortage_surplus,
            summary_status=req.summary_status,
            status=req.status,
            is_overdue=req.is_overdue
        )
        summaries.append(summary)
    
    return summaries


@router.get("/dashboard/", response_model=SalesDashboardData)
async def get_sales_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> SalesDashboardData:
    """
    Get sales dashboard data.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SalesDashboardData: Dashboard metrics and data
    """
    # Base query with department filtering
    base_query = select(CustomerRequirement).where(CustomerRequirement.is_active == True)
    
    if current_user.department.name == "Sales":
        base_query = base_query.where(CustomerRequirement.sales_person_id == current_user.id)
    
    # Get basic counts
    total_result = await db.execute(base_query)
    all_requirements = total_result.scalars().all()
    
    total_orders = len(all_requirements)
    pending_orders = len([r for r in all_requirements if r.status in ["pending", "partial"]])
    completed_orders = len([r for r in all_requirements if r.status == "completed"])
    overdue_orders = len([r for r in all_requirements if r.is_overdue])
    
    # Calculate values
    total_value = sum([r.total_value for r in all_requirements if r.total_value])
    pending_value = sum([r.total_value for r in all_requirements if r.status in ["pending", "partial"] and r.total_value])
    
    # Status breakdown
    status_breakdown = {}
    for requirement in all_requirements:
        status = requirement.status
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    # Recent orders (last 10)
    recent_statement = (
        base_query
        .join(Product, CustomerRequirement.product_id == Product.id)
        .order_by(desc(CustomerRequirement.created_at))
        .limit(10)
    )
    
    recent_result = await db.execute(recent_statement)
    recent_rows = recent_result.all()
    
    recent_orders = []
    for req, product in recent_rows:
        summary = CustomerRequirementSummary(
            id=req.id,
            sale_no=req.sale_no,
            po_no=req.po_no,
            customer_name=req.customer_name,
            product_part_no=product.part_no,
            product_part_name=product.part_name,
            due_date=req.due_date,
            po_quantity=req.po_quantity,
            delivered_quantity=req.delivered_quantity,
            shortage_surplus=req.shortage_surplus,
            summary_status=req.summary_status,
            status=req.status,
            is_overdue=req.is_overdue
        )
        recent_orders.append(summary)
    
    # Monthly trends (simplified for now)
    monthly_trends = []  # TODO: Implement monthly trend calculations
    
    return SalesDashboardData(
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        overdue_orders=overdue_orders,
        total_value=total_value,
        pending_value=pending_value,
        recent_orders=recent_orders,
        status_breakdown=status_breakdown,
        monthly_trends=monthly_trends
    )


@router.post("/requirements/bulk-import", response_model=CustomerRequirementBulkImportResponse)
async def bulk_import_customer_requirements(
    import_request: CustomerRequirementBulkImportRequest,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> CustomerRequirementBulkImportResponse:
    """
    Bulk import customer requirements from Excel data.
    
    Args:
        import_request: Bulk import request data
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        CustomerRequirementBulkImportResponse: Import results
    """
    total_processed = len(import_request.requirements)
    created = 0
    updated = 0
    errors = []
    
    for i, req_data in enumerate(import_request.requirements):
        try:
            # Check if requirement exists
            existing_req = await db.execute(
                select(CustomerRequirement).where(CustomerRequirement.sale_no == req_data.sale_no)
            )
            existing = existing_req.scalar_one_or_none()
            
            if existing and import_request.update_existing:
                # Update existing
                for field, value in req_data.model_dump(exclude_unset=True).items():
                    if field != "sales_person_id":  # Don't update sales person
                        setattr(existing, field, value)
                existing.touch()
                updated += 1
            elif not existing:
                # Create new
                req_dict = req_data.model_dump()
                req_dict["sales_person_id"] = current_user.id
                
                db_requirement = CustomerRequirement(**req_dict)
                db.add(db_requirement)
                created += 1
            else:
                errors.append({
                    "index": i,
                    "sale_no": req_data.sale_no,
                    "error": "Sale number already exists and update_existing is False"
                })
                
        except Exception as e:
            errors.append({
                "index": i,
                "sale_no": req_data.sale_no,
                "error": str(e)
            })
    
    await db.commit()
    
    success_rate = ((created + updated) / total_processed) * 100 if total_processed > 0 else 0
    
    return CustomerRequirementBulkImportResponse(
        total_processed=total_processed,
        created=created,
        updated=updated,
        errors=errors,
        success_rate=success_rate
    )