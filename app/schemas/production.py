"""
Production-related Pydantic schemas for request/response validation.

Contains schemas for production orders and production tracking.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.product import ProductLookup
from app.schemas.sales import CustomerRequirementSummary


# Production order schemas
class ProductionOrderBase(BaseModel):
    """
    Base production order schema.
    """
    production_order_no: str = Field(min_length=1, max_length=100)
    customer_requirement_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    planned_quantity: int = Field(ge=0)
    target_completion_date: datetime
    priority: str = Field(default="normal", max_length=20)
    production_notes: Optional[str] = Field(default=None, max_length=1000)


class ProductionOrderCreate(ProductionOrderBase):
    """
    Schema for creating production orders.
    """
    # assigned_to_id will be set from current user or specified
    assigned_to_id: Optional[int] = Field(default=None, gt=0)


class ProductionOrderUpdate(BaseModel):
    """
    Schema for updating production orders.
    """
    planned_quantity: Optional[int] = Field(default=None, ge=0)
    produced_quantity: Optional[int] = Field(default=None, ge=0)
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    production_status: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[str] = Field(default=None, max_length=20)
    assigned_to_id: Optional[int] = Field(default=None, gt=0)
    production_notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class ProductionOrderResponse(BaseModel):
    """
    Production order response schema.
    """
    id: int
    production_order_no: str
    customer_requirement_id: int
    product_id: int
    planned_quantity: int
    produced_quantity: int
    start_date: Optional[datetime] = None
    target_completion_date: datetime
    actual_completion_date: Optional[datetime] = None
    production_status: str
    priority: str
    assigned_to_id: int
    erpnext_work_order_id: Optional[str] = None
    production_notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    completion_percentage: float = Field(description="Production completion percentage")
    remaining_quantity: int = Field(description="Remaining quantity to produce")
    is_completed: bool = Field(description="Whether production is completed")
    is_overdue: bool = Field(description="Whether production is overdue")
    days_until_due: int = Field(description="Days until due date")
    
    # Related data
    product: ProductLookup
    customer_requirement: CustomerRequirementSummary

    model_config = {"from_attributes": True}


class ProductionOrderSummary(BaseModel):
    """
    Production order summary schema for lists.
    """
    id: int
    production_order_no: str
    product_part_no: str
    product_part_name: str
    customer_name: str
    planned_quantity: int
    produced_quantity: int
    completion_percentage: float
    target_completion_date: datetime
    production_status: str
    priority: str
    is_overdue: bool

    model_config = {"from_attributes": True}


class ProductionQuantityUpdate(BaseModel):
    """
    Schema for updating production quantities.
    """
    produced_quantity: int = Field(ge=0)
    production_note: Optional[str] = Field(default=None, max_length=500)


class ProductionStartRequest(BaseModel):
    """
    Schema for starting production.
    """
    start_date: Optional[datetime] = None
    production_note: Optional[str] = Field(default=None, max_length=500)


class ProductionCompletionRequest(BaseModel):
    """
    Schema for completing production.
    """
    completion_date: Optional[datetime] = None
    final_quantity: Optional[int] = Field(default=None, ge=0)
    completion_note: Optional[str] = Field(default=None, max_length=500)


# Production tracking schemas
class ProductionTrackingBase(BaseModel):
    """
    Base production tracking schema.
    """
    production_order_id: int = Field(gt=0)
    step_id: Optional[int] = Field(default=None, gt=0)
    quantity_produced: int = Field(ge=0)
    machine_used: Optional[str] = Field(default=None, max_length=255)
    quality_check_passed: bool = Field(default=True)
    notes: Optional[str] = Field(default=None, max_length=1000)


class ProductionTrackingCreate(ProductionTrackingBase):
    """
    Schema for creating production tracking entries.
    """
    start_time: Optional[datetime] = None
    # operator_id will be set from current user


class ProductionTrackingUpdate(BaseModel):
    """
    Schema for updating production tracking entries.
    """
    end_time: Optional[datetime] = None
    quantity_produced: Optional[int] = Field(default=None, ge=0)
    machine_used: Optional[str] = Field(default=None, max_length=255)
    quality_check_passed: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class ProductionTrackingResponse(BaseModel):
    """
    Production tracking response schema.
    """
    id: int
    production_order_id: int
    step_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    quantity_produced: int
    operator_id: int
    machine_used: Optional[str] = None
    quality_check_passed: bool
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    duration_minutes: Optional[int] = Field(description="Step duration in minutes")
    is_completed: bool = Field(description="Whether tracking entry is completed")

    model_config = {"from_attributes": True}


class ProductionTrackingSummary(BaseModel):
    """
    Production tracking summary schema for lists.
    """
    id: int
    production_order_no: str
    step_name: Optional[str] = None
    operator_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    quantity_produced: int
    duration_minutes: Optional[int] = None
    quality_check_passed: bool

    model_config = {"from_attributes": True}


class ProductionOrderSearchRequest(BaseModel):
    """
    Production order search request schema.
    """
    production_status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_id: Optional[int] = None
    customer_name: Optional[str] = None
    product_part_no: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    overdue_only: bool = False
    completed_only: bool = False


class ProductionDashboardData(BaseModel):
    """
    Production dashboard data schema.
    """
    total_orders: int
    active_orders: int
    completed_orders: int
    overdue_orders: int
    
    # Quantity metrics
    total_planned_quantity: int
    total_produced_quantity: int
    overall_completion_percentage: float
    
    # Current production status
    orders_by_status: dict[str, int]
    orders_by_priority: dict[str, int]
    
    # Recent activity
    recent_completions: List[ProductionOrderSummary]
    recent_tracking: List[ProductionTrackingSummary]
    
    # Capacity utilization
    capacity_utilization: dict[str, any]


class ProductionReportRequest(BaseModel):
    """
    Production report request schema.
    """
    report_type: str = Field(description="Type of report (daily, weekly, monthly)")
    date_from: datetime
    date_to: datetime
    department_id: Optional[int] = None
    product_ids: Optional[List[int]] = None
    include_tracking: bool = Field(default=True)


class ProductionEfficiencyReport(BaseModel):
    """
    Production efficiency report schema.
    """
    period: str
    total_orders: int
    completed_orders: int
    on_time_completions: int
    average_completion_time: float
    efficiency_percentage: float
    quality_rate: float
    
    # Detailed breakdowns
    by_product: List[dict[str, any]]
    by_operator: List[dict[str, any]]
    by_machine: List[dict[str, any]]