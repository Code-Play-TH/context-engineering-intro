"""
Excel processing API endpoints.

Handles Excel file uploads, downloads, and template generation.
"""

from typing import List, Optional
from datetime import datetime
import io

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_

from app.api.deps import (
    get_db,
    get_current_active_user,
    require_admin_access,
)
from app.models.sales import CustomerRequirement, Customer
from app.models.production import ProductionOrder
from app.models.product import Product
from app.models.user import User
from app.services.excel_service import excel_service, ExcelProcessingError
from app.schemas.sales import CustomerRequirementBulkImportRequest, CustomerRequirementBulkImportResponse
from app.schemas.product import ProductBulkImportRequest, ProductBulkImportResponse

router = APIRouter()


@router.post("/upload/customer-requirements", response_model=CustomerRequirementBulkImportResponse)
async def upload_customer_requirements_excel(
    file: UploadFile = File(...),
    validate_only: bool = Query(False, description="Only validate data without importing"),
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> CustomerRequirementBulkImportResponse:
    """
    Upload and process Excel file containing customer requirements.
    
    Args:
        file: Excel file to upload
        validate_only: If True, only validate data without importing
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        CustomerRequirementBulkImportResponse: Import results
        
    Raises:
        HTTPException: If file processing fails
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    try:
        # Process Excel file
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        
        result = await excel_service.process_customer_requirements_upload(
            file=file_stream,
            filename=file.filename,
            validate_only=validate_only
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel processing failed"
            )
        
        if validate_only:
            return CustomerRequirementBulkImportResponse(
                total_processed=result["total_rows"],
                created=0,
                updated=0,
                errors=result["errors"],
                success_rate=(result["valid_rows"] / result["total_rows"] * 100) if result["total_rows"] > 0 else 0
            )
        
        # Import valid customer requirements
        created_count = 0
        updated_count = 0
        import_errors = []
        
        for req_data in result["customer_requirements"]:
            try:
                # Check if customer requirement already exists
                existing_req = await db.execute(
                    select(CustomerRequirement).where(CustomerRequirement.sale_no == req_data.sale_no)
                )
                existing = existing_req.scalar_one_or_none()
                
                if existing:
                    # Update existing requirement
                    for field, value in req_data.model_dump(exclude_unset=True).items():
                        if field != "sales_person_id":  # Don't update sales person
                            setattr(existing, field, value)
                    existing.touch()
                    updated_count += 1
                else:
                    # Create new requirement
                    req_dict = req_data.model_dump()
                    req_dict["sales_person_id"] = current_user.id
                    
                    db_requirement = CustomerRequirement(**req_dict)
                    db.add(db_requirement)
                    created_count += 1
                    
            except Exception as e:
                import_errors.append({
                    "sale_no": req_data.sale_no,
                    "error": str(e)
                })
        
        await db.commit()
        
        # Combine validation and import errors
        all_errors = result["errors"] + import_errors
        success_rate = ((created_count + updated_count) / result["total_rows"] * 100) if result["total_rows"] > 0 else 0
        
        return CustomerRequirementBulkImportResponse(
            total_processed=result["total_rows"],
            created=created_count,
            updated=updated_count,
            errors=all_errors,
            success_rate=success_rate
        )
        
    except ExcelProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file processing: {str(e)}"
        )


@router.post("/upload/products", response_model=ProductBulkImportResponse)
async def upload_products_excel(
    file: UploadFile = File(...),
    validate_only: bool = Query(False, description="Only validate data without importing"),
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> ProductBulkImportResponse:
    """
    Upload and process Excel file containing product data.
    
    Args:
        file: Excel file to upload
        validate_only: If True, only validate data without importing
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ProductBulkImportResponse: Import results
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    try:
        # Process Excel file
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        
        result = await excel_service.process_product_upload(
            file=file_stream,
            filename=file.filename,
            validate_only=validate_only
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel processing failed"
            )
        
        if validate_only:
            return ProductBulkImportResponse(
                total_processed=result["total_rows"],
                created=0,
                updated=0,
                errors=result["errors"],
                success_rate=(result["valid_rows"] / result["total_rows"] * 100) if result["total_rows"] > 0 else 0
            )
        
        # Import valid products
        created_count = 0
        updated_count = 0
        import_errors = []
        
        for product_data in result["products"]:
            try:
                # Check if product already exists
                existing_product = await db.execute(
                    select(Product).where(Product.part_no == product_data.part_no)
                )
                existing = existing_product.scalar_one_or_none()
                
                if existing:
                    # Update existing product
                    for field, value in product_data.model_dump(exclude_unset=True).items():
                        if field != "production_steps":  # Handle separately
                            setattr(existing, field, value)
                    existing.touch()
                    updated_count += 1
                else:
                    # Create new product
                    product_dict = product_data.model_dump(exclude={"production_steps"})
                    db_product = Product(**product_dict)
                    db.add(db_product)
                    created_count += 1
                    
            except Exception as e:
                import_errors.append({
                    "part_no": product_data.part_no,
                    "error": str(e)
                })
        
        await db.commit()
        
        # Combine validation and import errors
        all_errors = result["errors"] + import_errors
        success_rate = ((created_count + updated_count) / result["total_rows"] * 100) if result["total_rows"] > 0 else 0
        
        return ProductBulkImportResponse(
            total_processed=result["total_rows"],
            created=created_count,
            updated=updated_count,
            errors=all_errors,
            success_rate=success_rate
        )
        
    except ExcelProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file processing: {str(e)}"
        )


@router.get("/download/customer-requirements")
async def download_customer_requirements_excel(
    include_formulas: bool = Query(True, description="Include Excel formulas"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter by date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by date to"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download customer requirements as Excel file.
    
    Args:
        include_formulas: Whether to include Excel formulas
        status_filter: Filter by requirement status
        date_from: Filter by date from
        date_to: Filter by date to
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Excel file download
    """
    try:
        # Build query with filters
        statement = (
            select(CustomerRequirement, Product, Customer)
            .join(Product, CustomerRequirement.product_id == Product.id)
            .outerjoin(Customer, CustomerRequirement.customer_id == Customer.id)
            .where(CustomerRequirement.is_active == True)
        )
        
        # Apply filters
        filters = []
        if status_filter:
            filters.append(CustomerRequirement.status == status_filter)
        if date_from:
            filters.append(CustomerRequirement.due_date >= date_from)
        if date_to:
            filters.append(CustomerRequirement.due_date <= date_to)
        
        # Department access control
        if current_user.department.name == "Sales":
            filters.append(CustomerRequirement.sales_person_id == current_user.id)
        
        if filters:
            statement = statement.where(and_(*filters))
        
        result = await db.execute(statement)
        rows = result.all()
        
        # Prepare data for Excel export
        requirements_data = []
        for req, product, customer in rows:
            req_data = {
                "sale_no": req.sale_no,
                "po_no": req.po_no,
                "customer_name": req.customer_name,
                "product_part_no": product.part_no,
                "product_part_name": product.part_name,
                "due_date": req.due_date,
                "po_quantity": req.po_quantity,
                "delivered_quantity": req.delivered_quantity,
                "shortage_surplus": req.shortage_surplus,
                "summary_status": req.summary_status,
                "unit_price": req.unit_price,
                "total_value": req.total_value,
                "status": req.status
            }
            requirements_data.append(req_data)
        
        # Generate Excel file
        excel_data = await excel_service.export_customer_requirements(
            requirements=requirements_data,
            include_formulas=include_formulas
        )
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"customer_requirements_{timestamp}.xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel file: {str(e)}"
        )


@router.get("/download/production-orders")
async def download_production_orders_excel(
    production_status: Optional[str] = Query(None, description="Filter by production status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    date_from: Optional[datetime] = Query(None, description="Filter by target date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by target date to"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download production orders as Excel file.
    
    Args:
        production_status: Filter by production status
        priority: Filter by priority
        date_from: Filter by target date from
        date_to: Filter by target date to
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Excel file download
    """
    try:
        # Build query with filters
        statement = (
            select(ProductionOrder, Product, CustomerRequirement, User)
            .join(Product, ProductionOrder.product_id == Product.id)
            .join(CustomerRequirement, ProductionOrder.customer_requirement_id == CustomerRequirement.id)
            .join(User, ProductionOrder.assigned_to_id == User.id)
            .where(ProductionOrder.is_active == True)
        )
        
        # Apply filters
        filters = []
        if production_status:
            filters.append(ProductionOrder.production_status == production_status)
        if priority:
            filters.append(ProductionOrder.priority == priority)
        if date_from:
            filters.append(ProductionOrder.target_completion_date >= date_from)
        if date_to:
            filters.append(ProductionOrder.target_completion_date <= date_to)
        
        # Department access control
        if current_user.department.name == "Production":
            filters.append(ProductionOrder.assigned_to_id == current_user.id)
        
        if filters:
            statement = statement.where(and_(*filters))
        
        result = await db.execute(statement)
        rows = result.all()
        
        # Prepare data for Excel export
        orders_data = []
        for order, product, req, user in rows:
            order_data = {
                "production_order_no": order.production_order_no,
                "customer_name": req.customer_name,
                "product_part_no": product.part_no,
                "product_part_name": product.part_name,
                "planned_quantity": order.planned_quantity,
                "produced_quantity": order.produced_quantity,
                "completion_percentage": order.completion_percentage,
                "target_completion_date": order.target_completion_date,
                "production_status": order.production_status,
                "priority": order.priority,
                "assigned_to_name": f"{user.first_name} {user.last_name}".strip() or user.username
            }
            orders_data.append(order_data)
        
        # Generate Excel file
        excel_data = await excel_service.export_production_orders(orders=orders_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"production_orders_{timestamp}.xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel file: {str(e)}"
        )


@router.get("/templates/vlookup")
async def download_vlookup_template(
    current_user: User = Depends(get_current_active_user)
):
    """
    Download Excel template with VLOOKUP formulas.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Excel template file download
    """
    try:
        # Generate VLOOKUP template
        excel_data = await excel_service.create_vlookup_template()
        
        # Create filename
        filename = "vlookup_template.xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}"
        )


@router.get("/templates/customer-requirements")
async def download_customer_requirements_template(
    current_user: User = Depends(get_current_active_user)
):
    """
    Download empty customer requirements template.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Excel template file download
    """
    try:
        # Create empty template with headers only
        template_data = []
        
        excel_data = await excel_service.export_customer_requirements(
            requirements=template_data,
            include_formulas=True
        )
        
        filename = "customer_requirements_template.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}"
        )


@router.get("/validate")
async def validate_excel_file(
    file: UploadFile = File(...),
    file_type: str = Query(..., description="Type of file: 'customer-requirements' or 'products'"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate Excel file without importing data.
    
    Args:
        file: Excel file to validate
        file_type: Type of file being validated
        current_user: Current authenticated user
        
    Returns:
        Validation results
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    try:
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        
        if file_type == "customer-requirements":
            result = await excel_service.process_customer_requirements_upload(
                file=file_stream,
                filename=file.filename,
                validate_only=True
            )
        elif file_type == "products":
            result = await excel_service.process_product_upload(
                file=file_stream,
                filename=file.filename,
                validate_only=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_type. Must be 'customer-requirements' or 'products'"
            )
        
        return {
            "filename": file.filename,
            "file_type": file_type,
            "validation_results": result,
            "is_valid": result["error_rows"] == 0,
            "can_import": result["valid_rows"] > 0
        }
        
    except ExcelProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during validation: {str(e)}"
        )