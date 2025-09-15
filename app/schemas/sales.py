"""
Sales-related Pydantic schemas for request/response validation.

Contains schemas for customer requirements and customer management.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.schemas.product import ProductLookup


# Customer schemas
class CustomerBase(BaseModel):
    """
    Base customer schema.
    """
    customer_code: str = Field(min_length=1, max_length=50)
    customer_name: str = Field(min_length=1, max_length=255)
    contact_person: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=1000)
    payment_terms: Optional[str] = Field(default=None, max_length=100)
    erpnext_customer_id: Optional[str] = Field(default=None, max_length=255)


class CustomerCreate(CustomerBase):
    """
    Schema for creating customers.
    """
    pass


class CustomerUpdate(BaseModel):
    """
    Schema for updating customers.
    """
    customer_name: Optional[str] = Field(default=None, max_length=255)
    contact_person: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=1000)
    payment_terms: Optional[str] = Field(default=None, max_length=100)
    erpnext_customer_id: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    """
    Customer response schema.
    """
    id: int
    customer_code: str
    customer_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    erpnext_customer_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerSummary(BaseModel):
    """
    Customer summary schema for lists and lookups.
    """
    id: int
    customer_code: str
    customer_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


# Customer requirement schemas
class CustomerRequirementBase(BaseModel):
    """
    Base customer requirement schema.
    """
    sale_no: str = Field(min_length=1, max_length=100)
    po_no: str = Field(min_length=1, max_length=100)
    customer_name: str = Field(min_length=1, max_length=255)
    customer_id: Optional[int] = Field(default=None, gt=0)
    product_id: int = Field(gt=0)
    due_date: datetime
    po_quantity: int = Field(ge=0)
    delivered_quantity: int = Field(default=0, ge=0)
    unit_price: Optional[float] = Field(default=None, ge=0)
    status: str = Field(default="pending", max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)


class CustomerRequirementCreate(CustomerRequirementBase):
    """
    Schema for creating customer requirements.
    """
    # sales_person_id will be set from current user
    pass


class CustomerRequirementUpdate(BaseModel):
    """
    Schema for updating customer requirements.
    """
    customer_name: Optional[str] = Field(default=None, max_length=255)
    customer_id: Optional[int] = Field(default=None, gt=0)
    due_date: Optional[datetime] = None
    po_quantity: Optional[int] = Field(default=None, ge=0)
    delivered_quantity: Optional[int] = Field(default=None, ge=0)
    unit_price: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class CustomerRequirementResponse(BaseModel):
    """
    Customer requirement response schema.
    """
    id: int
    sale_no: str
    po_no: str
    customer_name: str
    customer_id: Optional[int] = None
    product_id: int
    due_date: datetime
    po_quantity: int
    delivered_quantity: int
    unit_price: Optional[float] = None
    status: str
    sales_person_id: int
    erpnext_sales_order_id: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    shortage_surplus: int = Field(description="Delivered quantity - PO quantity")
    summary_status: str = Field(description="Complete or Shortage")
    total_value: Optional[float] = Field(description="Total order value")
    delivery_percentage: float = Field(description="Delivery completion percentage")
    is_overdue: bool = Field(description="Whether order is overdue")
    
    # Related data
    product: ProductLookup
    customer_data: Optional[CustomerSummary] = None

    model_config = {"from_attributes": True}


class CustomerRequirementSummary(BaseModel):
    """
    Customer requirement summary schema for lists.
    """
    id: int
    sale_no: str
    po_no: str
    customer_name: str
    product_part_no: str
    product_part_name: str
    due_date: datetime
    po_quantity: int
    delivered_quantity: int
    shortage_surplus: int
    summary_status: str
    status: str
    is_overdue: bool

    model_config = {"from_attributes": True}


class DeliveryUpdate(BaseModel):
    """
    Schema for updating delivery quantities.
    """
    delivered_quantity: int = Field(ge=0)
    delivery_note: Optional[str] = Field(default=None, max_length=500)


class CustomerRequirementSearchRequest(BaseModel):
    """
    Customer requirement search request schema.
    """
    customer_name: Optional[str] = None
    sale_no: Optional[str] = None
    po_no: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    overdue_only: bool = False
    shortage_only: bool = False


class SalesDashboardData(BaseModel):
    """
    Sales dashboard data schema.
    """
    total_orders: int
    pending_orders: int
    completed_orders: int
    overdue_orders: int
    total_value: float
    pending_value: float
    
    # Recent activity
    recent_orders: List[CustomerRequirementSummary]
    
    # Status breakdown
    status_breakdown: dict[str, int]
    
    # Monthly trends (last 12 months)
    monthly_trends: List[dict[str, any]]


class CustomerRequirementBulkImportRequest(BaseModel):
    """
    Customer requirement bulk import request schema.
    """
    requirements: List[CustomerRequirementCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False)


class CustomerRequirementBulkImportResponse(BaseModel):
    """
    Customer requirement bulk import response schema.
    """
    total_processed: int
    created: int
    updated: int
    errors: List[dict[str, any]] = Field(default_factory=list)
    success_rate: float