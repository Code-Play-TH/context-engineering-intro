"""
ERPNext integration API endpoints.

Handles synchronization between the factory ERP and ERPNext system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_

from app.api.deps import (
    get_db,
    get_current_active_user,
    require_admin_access,
)
from app.models.sales import Customer, CustomerRequirement
from app.models.product import Product
from app.models.production import ProductionOrder
from app.models.user import User
from app.services.erpnext_service import erpnext_service, ERPNextError, ERPNextAuthError
from pydantic import BaseModel

router = APIRouter()


class ERPNextSyncRequest(BaseModel):
    """Request schema for ERPNext synchronization."""
    sync_customers: bool = False
    sync_products: bool = False
    sync_sales_orders: bool = False
    sync_work_orders: bool = False
    customer_ids: Optional[List[int]] = None
    product_ids: Optional[List[int]] = None
    requirement_ids: Optional[List[int]] = None
    production_order_ids: Optional[List[int]] = None


class ERPNextSyncResponse(BaseModel):
    """Response schema for ERPNext synchronization."""
    success: bool
    message: str
    results: Dict[str, Any]
    sync_time: datetime


class ERPNextConnectionTest(BaseModel):
    """Response schema for ERPNext connection test."""
    connected: bool
    message: Optional[str] = None
    error: Optional[str] = None
    instance_url: Optional[str] = None
    api_version: Optional[str] = None


@router.get("/test-connection", response_model=ERPNextConnectionTest)
async def test_erpnext_connection(
    current_user: User = Depends(require_admin_access)
) -> ERPNextConnectionTest:
    """
    Test connection to ERPNext instance.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        ERPNextConnectionTest: Connection test results
    """
    try:
        result = await erpnext_service.test_connection()
        
        if result["connected"]:
            return ERPNextConnectionTest(
                connected=True,
                message=result["message"],
                instance_url=result.get("instance_url"),
                api_version=result.get("api_version")
            )
        else:
            return ERPNextConnectionTest(
                connected=False,
                error=result["error"]
            )
            
    except Exception as e:
        return ERPNextConnectionTest(
            connected=False,
            error=f"Connection test failed: {str(e)}"
        )


@router.post("/sync/customers/{customer_id}")
async def sync_customer_to_erpnext(
    customer_id: int,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync specific customer to ERPNext.
    
    Args:
        customer_id: Customer ID to sync
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Sync results
        
    Raises:
        HTTPException: If customer not found or sync fails
    """
    # Get customer
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    try:
        erpnext_id = await erpnext_service.sync_customer_to_erpnext(customer)
        
        if erpnext_id:
            # Update customer with ERPNext ID
            customer.erpnext_customer_id = erpnext_id
            customer.touch()
            await db.commit()
            
            return {
                "success": True,
                "message": f"Customer {customer.customer_name} synced successfully",
                "erpnext_customer_id": erpnext_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to sync customer to ERPNext"
            }
            
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during sync: {str(e)}"
        )


@router.post("/sync/products/{product_id}")
async def sync_product_to_erpnext(
    product_id: int,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync specific product to ERPNext.
    
    Args:
        product_id: Product ID to sync
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Sync results
    """
    # Get product
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    try:
        erpnext_id = await erpnext_service.sync_product_to_erpnext(product)
        
        if erpnext_id:
            # Update product with ERPNext ID
            product.erpnext_item_code = erpnext_id
            product.touch()
            await db.commit()
            
            return {
                "success": True,
                "message": f"Product {product.part_name} synced successfully",
                "erpnext_item_code": erpnext_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to sync product to ERPNext"
            }
            
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during sync: {str(e)}"
        )


@router.post("/sync/sales-orders/{requirement_id}")
async def sync_sales_order_to_erpnext(
    requirement_id: int,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync customer requirement to ERPNext as sales order.
    
    Args:
        requirement_id: Customer requirement ID to sync
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Sync results
    """
    # Get customer requirement with related data
    statement = (
        select(CustomerRequirement, Customer)
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
    
    requirement, customer = row
    
    try:
        erpnext_id = await erpnext_service.sync_sales_order_to_erpnext(requirement, customer)
        
        if erpnext_id:
            # Update requirement with ERPNext ID
            requirement.erpnext_sales_order_id = erpnext_id
            requirement.touch()
            await db.commit()
            
            return {
                "success": True,
                "message": f"Sales order {requirement.sale_no} synced successfully",
                "erpnext_sales_order_id": erpnext_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to sync sales order to ERPNext"
            }
            
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during sync: {str(e)}"
        )


@router.post("/sync/work-orders/{production_order_id}")
async def sync_work_order_to_erpnext(
    production_order_id: int,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync production order to ERPNext as work order.
    
    Args:
        production_order_id: Production order ID to sync
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Sync results
    """
    # Get production order
    production_order = await db.get(ProductionOrder, production_order_id)
    if not production_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    
    try:
        erpnext_id = await erpnext_service.sync_work_order_to_erpnext(production_order)
        
        if erpnext_id:
            # Update production order with ERPNext ID
            production_order.erpnext_work_order_id = erpnext_id
            production_order.touch()
            await db.commit()
            
            return {
                "success": True,
                "message": f"Work order {production_order.production_order_no} synced successfully",
                "erpnext_work_order_id": erpnext_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to sync work order to ERPNext"
            }
            
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during sync: {str(e)}"
        )


@router.post("/sync/bulk", response_model=ERPNextSyncResponse)
async def bulk_sync_to_erpnext(
    sync_request: ERPNextSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> ERPNextSyncResponse:
    """
    Perform bulk synchronization to ERPNext.
    
    Args:
        sync_request: Sync configuration
        background_tasks: Background task manager
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ERPNextSyncResponse: Sync results
    """
    try:
        # Collect data to sync
        customers = []
        products = []
        requirements = []
        production_orders = []
        
        # Get customers to sync
        if sync_request.sync_customers:
            customer_query = select(Customer).where(Customer.is_active == True)
            if sync_request.customer_ids:
                customer_query = customer_query.where(Customer.id.in_(sync_request.customer_ids))
            
            customer_result = await db.execute(customer_query)
            customers = customer_result.scalars().all()
        
        # Get products to sync
        if sync_request.sync_products:
            product_query = select(Product).where(Product.is_active == True)
            if sync_request.product_ids:
                product_query = product_query.where(Product.id.in_(sync_request.product_ids))
            
            product_result = await db.execute(product_query)
            products = product_result.scalars().all()
        
        # Get customer requirements to sync
        if sync_request.sync_sales_orders:
            req_query = select(CustomerRequirement).where(CustomerRequirement.is_active == True)
            if sync_request.requirement_ids:
                req_query = req_query.where(CustomerRequirement.id.in_(sync_request.requirement_ids))
            
            req_result = await db.execute(req_query)
            requirements = req_result.scalars().all()
        
        # Get production orders to sync
        if sync_request.sync_work_orders:
            po_query = select(ProductionOrder).where(ProductionOrder.is_active == True)
            if sync_request.production_order_ids:
                po_query = po_query.where(ProductionOrder.id.in_(sync_request.production_order_ids))
            
            po_result = await db.execute(po_query)
            production_orders = po_result.scalars().all()
        
        # Perform bulk sync
        results = await erpnext_service.bulk_sync_to_erpnext(
            customers=customers,
            products=products,
            requirements=requirements,
            production_orders=production_orders
        )
        
        if "error" in results:
            return ERPNextSyncResponse(
                success=False,
                message=results["error"],
                results={},
                sync_time=datetime.utcnow()
            )
        
        # Update database with ERPNext IDs (simplified for now)
        # In a real implementation, you'd want to track which items were successfully synced
        await db.commit()
        
        total_synced = (
            results["customers"]["synced"] +
            results["products"]["synced"] +
            results["sales_orders"]["synced"] +
            results["work_orders"]["synced"]
        )
        
        total_errors = (
            len(results["customers"]["errors"]) +
            len(results["products"]["errors"]) +
            len(results["sales_orders"]["errors"]) +
            len(results["work_orders"]["errors"])
        )
        
        return ERPNextSyncResponse(
            success=total_errors == 0,
            message=f"Bulk sync completed. {total_synced} items synced, {total_errors} errors.",
            results=results,
            sync_time=datetime.utcnow()
        )
        
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during bulk sync: {str(e)}"
        )


@router.get("/fetch/customers")
async def fetch_customers_from_erpnext(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin_access)
) -> Dict[str, Any]:
    """
    Fetch customers from ERPNext.
    
    Args:
        limit: Maximum number of customers to fetch
        current_user: Current authenticated admin user
        
    Returns:
        List of customers from ERPNext
    """
    try:
        customers = await erpnext_service.fetch_customers_from_erpnext(limit=limit)
        
        return {
            "success": True,
            "count": len(customers),
            "customers": customers
        }
        
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customers: {str(e)}"
        )


@router.get("/fetch/items")
async def fetch_items_from_erpnext(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin_access)
) -> Dict[str, Any]:
    """
    Fetch items from ERPNext.
    
    Args:
        limit: Maximum number of items to fetch
        current_user: Current authenticated admin user
        
    Returns:
        List of items from ERPNext
    """
    try:
        items = await erpnext_service.fetch_items_from_erpnext(limit=limit)
        
        return {
            "success": True,
            "count": len(items),
            "items": items
        }
        
    except ERPNextAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ERPNextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch items: {str(e)}"
        )


@router.get("/status")
async def get_erpnext_integration_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get ERPNext integration status and configuration.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Integration status information
    """
    return {
        "enabled": erpnext_service.is_enabled,
        "base_url": erpnext_service.base_url if erpnext_service.base_url else "Not configured",
        "has_credentials": bool(erpnext_service.api_key and erpnext_service.api_secret),
        "endpoints": erpnext_service.endpoints if current_user.role.name == "Admin" else "Access denied"
    }