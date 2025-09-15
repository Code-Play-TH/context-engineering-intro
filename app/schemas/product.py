"""
Product-related Pydantic schemas for request/response validation.

Contains schemas for product management and production steps.
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field


# Production step schemas
class ProductionStepBase(BaseModel):
    """
    Base production step schema.
    """
    step_number: int = Field(ge=1, description="Step sequence number")
    step_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    estimated_time_minutes: Optional[int] = Field(default=None, ge=0)
    machine_required: Optional[str] = Field(default=None, max_length=255)
    skill_level: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)


class ProductionStepCreate(ProductionStepBase):
    """
    Schema for creating production steps.
    """
    product_id: int = Field(gt=0)


class ProductionStepUpdate(BaseModel):
    """
    Schema for updating production steps.
    """
    step_number: Optional[int] = Field(default=None, ge=1)
    step_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    estimated_time_minutes: Optional[int] = Field(default=None, ge=0)
    machine_required: Optional[str] = Field(default=None, max_length=255)
    skill_level: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class ProductionStepResponse(BaseModel):
    """
    Production step response schema.
    """
    id: int
    product_id: int
    step_number: int
    step_name: str
    description: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    machine_required: Optional[str] = None
    skill_level: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Product schemas
class ProductBase(BaseModel):
    """
    Base product schema.
    """
    part_no: str = Field(min_length=1, max_length=100, description="Unique part number")
    part_name: str = Field(min_length=1, max_length=255)
    drawing_no: Optional[str] = Field(default=None, max_length=100)
    material_code: Optional[str] = Field(default=None, max_length=100)
    material_description: Optional[str] = Field(default=None, max_length=500)
    unit_of_measure: str = Field(default="PCS", max_length=10)
    standard_cost: Optional[float] = Field(default=None, ge=0)
    erpnext_item_code: Optional[str] = Field(default=None, max_length=255)
    specifications: Optional[dict[str, Any]] = Field(default_factory=dict)


class ProductCreate(ProductBase):
    """
    Schema for creating products.
    """
    production_steps: List[ProductionStepBase] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    """
    Schema for updating products.
    """
    part_name: Optional[str] = Field(default=None, max_length=255)
    drawing_no: Optional[str] = Field(default=None, max_length=100)
    material_code: Optional[str] = Field(default=None, max_length=100)
    material_description: Optional[str] = Field(default=None, max_length=500)
    unit_of_measure: Optional[str] = Field(default=None, max_length=10)
    standard_cost: Optional[float] = Field(default=None, ge=0)
    erpnext_item_code: Optional[str] = Field(default=None, max_length=255)
    specifications: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """
    Product response schema.
    """
    id: int
    part_no: str
    part_name: str
    drawing_no: Optional[str] = None
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    unit_of_measure: str
    standard_cost: Optional[float] = None
    erpnext_item_code: Optional[str] = None
    specifications: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    total_production_time: int = Field(description="Total estimated production time in minutes")
    
    # Related data
    production_steps: List[ProductionStepResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductSummary(BaseModel):
    """
    Product summary schema for lists and lookups.
    """
    id: int
    part_no: str
    part_name: str
    drawing_no: Optional[str] = None
    material_code: Optional[str] = None
    unit_of_measure: str
    standard_cost: Optional[float] = None
    is_active: bool

    model_config = {"from_attributes": True}


class ProductLookup(BaseModel):
    """
    Product lookup schema for VLOOKUP functionality.
    
    Used when creating customer requirements or production orders.
    """
    id: int
    part_no: str
    part_name: str
    drawing_no: Optional[str] = None
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    unit_of_measure: str
    standard_cost: Optional[float] = None
    total_production_time: int

    model_config = {"from_attributes": True}


class ProductSearchRequest(BaseModel):
    """
    Product search request schema.
    """
    query: str = Field(min_length=1, description="Search term")
    search_fields: List[str] = Field(
        default=["part_no", "part_name", "material_code"],
        description="Fields to search in"
    )
    limit: int = Field(default=20, ge=1, le=100)


class ProductBulkImportRequest(BaseModel):
    """
    Product bulk import request schema.
    """
    products: List[ProductCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False, description="Update existing products")


class ProductBulkImportResponse(BaseModel):
    """
    Product bulk import response schema.
    """
    total_processed: int
    created: int
    updated: int
    errors: List[dict[str, Any]] = Field(default_factory=list)
    success_rate: float = Field(description="Success rate percentage")