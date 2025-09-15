"""
Production management API endpoints.

Handles production orders, production tracking, and production dashboard.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, or_, func, desc

from app.api.deps import (
    get_db,
    get_current_active_user,
    require_production_access,
    require_admin_access,
)
from app.models.production import ProductionOrder, ProductionTracking
from app.models.sales import CustomerRequirement
from app.models.product import Product
from app.models.user import User
from app.schemas.production import (
    ProductionOrderCreate,
    ProductionOrderUpdate,
    ProductionOrderResponse,
    ProductionOrderSummary,
    ProductionOrderSearchRequest,
    ProductionQuantityUpdate,
    ProductionStartRequest,
    ProductionCompletionRequest,
    ProductionTrackingCreate,
    ProductionTrackingUpdate,
    ProductionTrackingResponse,
    ProductionTrackingSummary,
    ProductionDashboardData,
    ProductionReportRequest,
    ProductionEfficiencyReport,
)
from app.schemas.product import ProductLookup
from app.schemas.sales import CustomerRequirementSummary

router = APIRouter()


# Production order endpoints
@router.get("/orders/", response_model=List[ProductionOrderSummary])
async def get_production_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    production_status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductionOrderSummary]:
    """
    Get list of production orders with filtering options.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        production_status: Filter by production status
        priority: Filter by priority
        overdue_only: Show only overdue orders
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ProductionOrderSummary]: List of production orders
    """
    # Base query with joins
    statement = (
        select(ProductionOrder, Product, CustomerRequirement)
        .join(Product, ProductionOrder.product_id == Product.id)
        .join(CustomerRequirement, ProductionOrder.customer_requirement_id == CustomerRequirement.id)
        .where(ProductionOrder.is_active == True)
    )
    
    # Apply filters
    filters = []
    if production_status:
        filters.append(ProductionOrder.production_status == production_status)
    if priority:
        filters.append(ProductionOrder.priority == priority)
    if overdue_only:
        filters.append(
            and_(
                ProductionOrder.target_completion_date < datetime.utcnow(),
                ProductionOrder.production_status != "completed"
            )
        )
    
    # Department access control
    if current_user.department.name == "Production":
        filters.append(ProductionOrder.assigned_to_id == current_user.id)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.order_by(desc(ProductionOrder.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(statement)
    rows = result.all()
    
    # Create summary responses
    summaries = []
    for order, product, req in rows:
        summary = ProductionOrderSummary(
            id=order.id,
            production_order_no=order.production_order_no,
            product_part_no=product.part_no,
            product_part_name=product.part_name,
            customer_name=req.customer_name,
            planned_quantity=order.planned_quantity,
            produced_quantity=order.produced_quantity,
            completion_percentage=order.completion_percentage,
            target_completion_date=order.target_completion_date,
            production_status=order.production_status,
            priority=order.priority,
            is_overdue=order.is_overdue
        )
        summaries.append(summary)
    
    return summaries


@router.get("/orders/{order_id}", response_model=ProductionOrderResponse)
async def get_production_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductionOrderResponse:
    """
    Get production order by ID with product and customer requirement data.
    
    Args:
        order_id: Production order ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductionOrderResponse: Production order data
        
    Raises:
        HTTPException: If order not found or access denied
    """
    # Get order with related data
    statement = (
        select(ProductionOrder, Product, CustomerRequirement)
        .join(Product, ProductionOrder.product_id == Product.id)
        .join(CustomerRequirement, ProductionOrder.customer_requirement_id == CustomerRequirement.id)
        .where(ProductionOrder.id == order_id)
    )
    
    result = await db.execute(statement)
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    
    order, product, req = row
    
    # Access control
    if current_user.department.name == "Production" and order.assigned_to_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this production order"
        )
    
    # Create response with calculated fields
    response = ProductionOrderResponse.model_validate(order)
    response.completion_percentage = order.completion_percentage
    response.remaining_quantity = order.remaining_quantity
    response.is_completed = order.is_completed
    response.is_overdue = order.is_overdue
    response.days_until_due = order.days_until_due
    
    # Add related data
    response.product = ProductLookup.model_validate(product)
    response.product.total_production_time = product.get_total_production_time()
    
    response.customer_requirement = CustomerRequirementSummary(
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
    
    return response


@router.post("/orders/", response_model=ProductionOrderResponse)
async def create_production_order(
    order_data: ProductionOrderCreate,
    current_user: User = Depends(require_production_access),
    db: AsyncSession = Depends(get_db)
) -> ProductionOrderResponse:
    """
    Create new production order.
    
    Args:
        order_data: Production order creation data
        current_user: Current authenticated production user
        db: Database session
        
    Returns:
        ProductionOrderResponse: Created production order
        
    Raises:
        HTTPException: If customer requirement or product not found, or order number exists
    """
    # Verify customer requirement exists
    customer_req = await db.get(CustomerRequirement, order_data.customer_requirement_id)
    if not customer_req or not customer_req.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer requirement not found or inactive"
        )
    
    # Verify product exists
    product = await db.get(Product, order_data.product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found or inactive"
        )
    
    # Check if production order number already exists
    existing_order = await db.execute(
        select(ProductionOrder).where(ProductionOrder.production_order_no == order_data.production_order_no)
    )
    if existing_order.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Production order number already exists"
        )
    
    # Create production order
    order_dict = order_data.model_dump()
    
    # Set assigned_to_id if not provided
    if not order_dict.get("assigned_to_id"):
        order_dict["assigned_to_id"] = current_user.id
    
    db_order = ProductionOrder(**order_dict)
    
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    
    # Return full order data
    return await get_production_order(db_order.id, current_user, db)


@router.put("/orders/{order_id}", response_model=ProductionOrderResponse)
async def update_production_order(
    order_id: int,
    order_data: ProductionOrderUpdate,
    current_user: User = Depends(require_production_access),
    db: AsyncSession = Depends(get_db)
) -> ProductionOrderResponse:
    """
    Update production order.
    
    Args:
        order_id: Production order ID to update
        order_data: Production order update data
        current_user: Current authenticated production user
        db: Database session
        
    Returns:
        ProductionOrderResponse: Updated production order
        
    Raises:
        HTTPException: If order not found or access denied
    """
    order = await db.get(ProductionOrder, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    
    # Access control
    if current_user.department.name == "Production" and order.assigned_to_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this production order"
        )
    
    # Update fields
    update_data = order_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    order.touch()
    await db.commit()
    
    return await get_production_order(order_id, current_user, db)


@router.patch("/orders/{order_id}/quantity", response_model=ProductionOrderResponse)
async def update_production_quantity(
    order_id: int,
    quantity_data: ProductionQuantityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductionOrderResponse:
    """
    Update produced quantity for production order.
    
    Args:
        order_id: Production order ID
        quantity_data: Quantity update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductionOrderResponse: Updated production order
        
    Raises:
        HTTPException: If order not found or invalid quantity
    """
    order = await db.get(ProductionOrder, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    
    # Validate produced quantity
    if quantity_data.produced_quantity > order.planned_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produced quantity cannot exceed planned quantity"
        )
    
    # Update quantity
    order.produced_quantity = quantity_data.produced_quantity
    
    if quantity_data.production_note:
        current_notes = order.production_notes or ""
        order.production_notes = f"{current_notes}\n{quantity_data.production_note}".strip()
    
    # Auto-update status based on completion
    if order.produced_quantity >= order.planned_quantity:
        order.production_status = "completed"
        if not order.actual_completion_date:
            order.actual_completion_date = datetime.utcnow()
    elif order.produced_quantity > 0:
        order.production_status = "in_progress"
        if not order.start_date:
            order.start_date = datetime.utcnow()
    
    order.touch()
    await db.commit()
    
    return await get_production_order(order_id, current_user, db)


@router.patch("/orders/{order_id}/start", response_model=ProductionOrderResponse)
async def start_production(
    order_id: int,
    start_data: ProductionStartRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductionOrderResponse:
    """
    Start production for an order.
    
    Args:
        order_id: Production order ID
        start_data: Production start data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductionOrderResponse: Updated production order
        
    Raises:
        HTTPException: If order not found or already started
    """
    order = await db.get(ProductionOrder, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    
    if order.production_status not in ["pending", "planned"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Production order cannot be started in current status"
        )
    
    # Start production
    order.start_date = start_data.start_date or datetime.utcnow()
    order.production_status = "in_progress"
    
    if start_data.production_note:
        current_notes = order.production_notes or ""
        order.production_notes = f"{current_notes}\nStarted: {start_data.production_note}".strip()
    
    order.touch()
    await db.commit()
    
    return await get_production_order(order_id, current_user, db)


@router.patch("/orders/{order_id}/complete", response_model=ProductionOrderResponse)
async def complete_production(
    order_id: int,
    completion_data: ProductionCompletionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductionOrderResponse:
    """
    Complete production for an order.
    
    Args:
        order_id: Production order ID
        completion_data: Production completion data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductionOrderResponse: Updated production order
        
    Raises:
        HTTPException: If order not found or not in progress
    """
    order = await db.get(ProductionOrder, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    
    if order.production_status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Production order is not in progress"
        )
    
    # Complete production
    order.actual_completion_date = completion_data.completion_date or datetime.utcnow()
    order.production_status = "completed"
    
    if completion_data.final_quantity is not None:
        order.produced_quantity = completion_data.final_quantity
    
    if completion_data.completion_note:
        current_notes = order.production_notes or ""
        order.production_notes = f"{current_notes}\nCompleted: {completion_data.completion_note}".strip()
    
    order.touch()
    await db.commit()
    
    return await get_production_order(order_id, current_user, db)


@router.post("/orders/search", response_model=List[ProductionOrderSummary])
async def search_production_orders(
    search_request: ProductionOrderSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductionOrderSummary]:
    """
    Search production orders with advanced filters.
    
    Args:
        search_request: Search parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ProductionOrderSummary]: Matching production orders
    """
    # Base query
    statement = (
        select(ProductionOrder, Product, CustomerRequirement)
        .join(Product, ProductionOrder.product_id == Product.id)
        .join(CustomerRequirement, ProductionOrder.customer_requirement_id == CustomerRequirement.id)
        .where(ProductionOrder.is_active == True)
    )
    
    # Apply search filters
    filters = []
    
    if search_request.production_status:
        filters.append(ProductionOrder.production_status == search_request.production_status)
    
    if search_request.priority:
        filters.append(ProductionOrder.priority == search_request.priority)
    
    if search_request.assigned_to_id:
        filters.append(ProductionOrder.assigned_to_id == search_request.assigned_to_id)
    
    if search_request.customer_name:
        filters.append(CustomerRequirement.customer_name.ilike(f"%{search_request.customer_name}%"))
    
    if search_request.product_part_no:
        filters.append(Product.part_no.ilike(f"%{search_request.product_part_no}%"))
    
    if search_request.date_from:
        filters.append(ProductionOrder.target_completion_date >= search_request.date_from)
    
    if search_request.date_to:
        filters.append(ProductionOrder.target_completion_date <= search_request.date_to)
    
    if search_request.overdue_only:
        filters.append(
            and_(
                ProductionOrder.target_completion_date < datetime.utcnow(),
                ProductionOrder.production_status != "completed"
            )
        )
    
    if search_request.completed_only:
        filters.append(ProductionOrder.production_status == "completed")
    
    # Department access control
    if current_user.department.name == "Production":
        filters.append(ProductionOrder.assigned_to_id == current_user.id)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.order_by(desc(ProductionOrder.created_at)).limit(100)
    
    result = await db.execute(statement)
    rows = result.all()
    
    # Create summary responses
    summaries = []
    for order, product, req in rows:
        summary = ProductionOrderSummary(
            id=order.id,
            production_order_no=order.production_order_no,
            product_part_no=product.part_no,
            product_part_name=product.part_name,
            customer_name=req.customer_name,
            planned_quantity=order.planned_quantity,
            produced_quantity=order.produced_quantity,
            completion_percentage=order.completion_percentage,
            target_completion_date=order.target_completion_date,
            production_status=order.production_status,
            priority=order.priority,
            is_overdue=order.is_overdue
        )
        summaries.append(summary)
    
    return summaries


# Production tracking endpoints
@router.get("/tracking/", response_model=List[ProductionTrackingSummary])
async def get_production_tracking(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    production_order_id: Optional[int] = Query(None),
    operator_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProductionTrackingSummary]:
    """
    Get production tracking entries.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        production_order_id: Filter by production order
        operator_id: Filter by operator
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ProductionTrackingSummary]: List of tracking entries
    """
    # Base query with joins
    statement = (
        select(ProductionTracking, ProductionOrder, User)
        .join(ProductionOrder, ProductionTracking.production_order_id == ProductionOrder.id)
        .join(User, ProductionTracking.operator_id == User.id)
        .where(ProductionTracking.is_active == True)
    )
    
    # Apply filters
    filters = []
    if production_order_id:
        filters.append(ProductionTracking.production_order_id == production_order_id)
    if operator_id:
        filters.append(ProductionTracking.operator_id == operator_id)
    
    # Department access control
    if current_user.department.name == "Production":
        filters.append(ProductionTracking.operator_id == current_user.id)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.order_by(desc(ProductionTracking.start_time)).offset(skip).limit(limit)
    
    result = await db.execute(statement)
    rows = result.all()
    
    # Create summary responses
    summaries = []
    for tracking, order, operator in rows:
        summary = ProductionTrackingSummary(
            id=tracking.id,
            production_order_no=order.production_order_no,
            step_name=None,  # TODO: Add step name if step_id exists
            operator_name=f"{operator.first_name} {operator.last_name}".strip() or operator.username,
            start_time=tracking.start_time,
            end_time=tracking.end_time,
            quantity_produced=tracking.quantity_produced,
            duration_minutes=tracking.duration_minutes,
            quality_check_passed=tracking.quality_check_passed
        )
        summaries.append(summary)
    
    return summaries


@router.post("/tracking/", response_model=ProductionTrackingResponse)
async def create_production_tracking(
    tracking_data: ProductionTrackingCreate,
    current_user: User = Depends(require_production_access),
    db: AsyncSession = Depends(get_db)
) -> ProductionTrackingResponse:
    """
    Create new production tracking entry.
    
    Args:
        tracking_data: Production tracking creation data
        current_user: Current authenticated production user
        db: Database session
        
    Returns:
        ProductionTrackingResponse: Created tracking entry
        
    Raises:
        HTTPException: If production order not found
    """
    # Verify production order exists
    order = await db.get(ProductionOrder, tracking_data.production_order_id)
    if not order or not order.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Production order not found or inactive"
        )
    
    # Create tracking entry
    tracking_dict = tracking_data.model_dump()
    tracking_dict["operator_id"] = current_user.id
    tracking_dict["start_time"] = tracking_data.start_time or datetime.utcnow()
    
    db_tracking = ProductionTracking(**tracking_dict)
    
    db.add(db_tracking)
    await db.commit()
    await db.refresh(db_tracking)
    
    # Create response with calculated fields
    response = ProductionTrackingResponse.model_validate(db_tracking)
    response.duration_minutes = db_tracking.duration_minutes
    response.is_completed = db_tracking.is_completed
    
    return response


@router.put("/tracking/{tracking_id}", response_model=ProductionTrackingResponse)
async def update_production_tracking(
    tracking_id: int,
    tracking_data: ProductionTrackingUpdate,
    current_user: User = Depends(require_production_access),
    db: AsyncSession = Depends(get_db)
) -> ProductionTrackingResponse:
    """
    Update production tracking entry.
    
    Args:
        tracking_id: Tracking entry ID to update
        tracking_data: Tracking update data
        current_user: Current authenticated production user
        db: Database session
        
    Returns:
        ProductionTrackingResponse: Updated tracking entry
        
    Raises:
        HTTPException: If tracking not found or access denied
    """
    tracking = await db.get(ProductionTracking, tracking_id)
    if not tracking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production tracking not found"
        )
    
    # Access control
    if current_user.department.name == "Production" and tracking.operator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tracking entry"
        )
    
    # Update fields
    update_data = tracking_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tracking, field, value)
    
    tracking.touch()
    await db.commit()
    
    # Create response with calculated fields
    response = ProductionTrackingResponse.model_validate(tracking)
    response.duration_minutes = tracking.duration_minutes
    response.is_completed = tracking.is_completed
    
    return response


@router.get("/dashboard/", response_model=ProductionDashboardData)
async def get_production_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ProductionDashboardData:
    """
    Get production dashboard data.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProductionDashboardData: Dashboard metrics and data
    """
    # Base query with department filtering
    base_query = select(ProductionOrder).where(ProductionOrder.is_active == True)
    
    if current_user.department.name == "Production":
        base_query = base_query.where(ProductionOrder.assigned_to_id == current_user.id)
    
    # Get basic counts
    total_result = await db.execute(base_query)
    all_orders = total_result.scalars().all()
    
    total_orders = len(all_orders)
    active_orders = len([o for o in all_orders if o.production_status in ["pending", "in_progress"]])
    completed_orders = len([o for o in all_orders if o.production_status == "completed"])
    overdue_orders = len([o for o in all_orders if o.is_overdue])
    
    # Quantity metrics
    total_planned_quantity = sum([o.planned_quantity for o in all_orders])
    total_produced_quantity = sum([o.produced_quantity for o in all_orders])
    overall_completion_percentage = (total_produced_quantity / total_planned_quantity * 100) if total_planned_quantity > 0 else 0
    
    # Status and priority breakdowns
    orders_by_status = {}
    orders_by_priority = {}
    for order in all_orders:
        status = order.production_status
        priority = order.priority
        orders_by_status[status] = orders_by_status.get(status, 0) + 1
        orders_by_priority[priority] = orders_by_priority.get(priority, 0) + 1
    
    # Recent completions and tracking
    recent_completions = []  # TODO: Implement recent completions
    recent_tracking = []     # TODO: Implement recent tracking
    
    # Capacity utilization (simplified)
    capacity_utilization = {
        "machine_utilization": 75.0,  # TODO: Calculate from actual data
        "operator_efficiency": 82.0,  # TODO: Calculate from actual data
        "overall_efficiency": 78.5    # TODO: Calculate from actual data
    }
    
    return ProductionDashboardData(
        total_orders=total_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        overdue_orders=overdue_orders,
        total_planned_quantity=total_planned_quantity,
        total_produced_quantity=total_produced_quantity,
        overall_completion_percentage=overall_completion_percentage,
        orders_by_status=orders_by_status,
        orders_by_priority=orders_by_priority,
        recent_completions=recent_completions,
        recent_tracking=recent_tracking,
        capacity_utilization=capacity_utilization
    )


@router.post("/reports/efficiency", response_model=ProductionEfficiencyReport)
async def generate_efficiency_report(
    report_request: ProductionReportRequest,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> ProductionEfficiencyReport:
    """
    Generate production efficiency report.
    
    Args:
        report_request: Report parameters
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ProductionEfficiencyReport: Efficiency report data
    """
    # Base query for the report period
    statement = (
        select(ProductionOrder)
        .where(
            and_(
                ProductionOrder.is_active == True,
                ProductionOrder.created_at >= report_request.date_from,
                ProductionOrder.created_at <= report_request.date_to
            )
        )
    )
    
    # Apply filters
    if report_request.department_id:
        statement = statement.join(User, ProductionOrder.assigned_to_id == User.id).where(
            User.department_id == report_request.department_id
        )
    
    if report_request.product_ids:
        statement = statement.where(ProductionOrder.product_id.in_(report_request.product_ids))
    
    result = await db.execute(statement)
    orders = result.scalars().all()
    
    # Calculate metrics
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.production_status == "completed"])
    on_time_completions = len([o for o in orders if o.production_status == "completed" and not o.is_overdue])
    
    # Calculate averages
    if completed_orders > 0:
        completion_times = []
        for order in orders:
            if order.production_status == "completed" and order.start_date and order.actual_completion_date:
                duration = (order.actual_completion_date - order.start_date).total_seconds() / 3600  # hours
                completion_times.append(duration)
        
        average_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        efficiency_percentage = (on_time_completions / completed_orders) * 100
    else:
        average_completion_time = 0
        efficiency_percentage = 0
    
    # Quality rate (simplified)
    quality_rate = 95.0  # TODO: Calculate from actual quality data
    
    # Detailed breakdowns (simplified for now)
    by_product = []     # TODO: Implement product breakdown
    by_operator = []    # TODO: Implement operator breakdown
    by_machine = []     # TODO: Implement machine breakdown
    
    return ProductionEfficiencyReport(
        period=f"{report_request.date_from.strftime('%Y-%m-%d')} to {report_request.date_to.strftime('%Y-%m-%d')}",
        total_orders=total_orders,
        completed_orders=completed_orders,
        on_time_completions=on_time_completions,
        average_completion_time=average_completion_time,
        efficiency_percentage=efficiency_percentage,
        quality_rate=quality_rate,
        by_product=by_product,
        by_operator=by_operator,
        by_machine=by_machine
    )