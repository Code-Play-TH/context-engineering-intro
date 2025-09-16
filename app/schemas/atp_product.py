"""
ATP Product schemas for API operations and Excel import.

Contains Pydantic schemas for ATP Product data handling including
Excel import structures and API response models.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


# ATP Product base schemas
class ATPProductBase(BaseModel):
    """Base ATP product schema."""
    part_no: str = Field(min_length=1, max_length=100)
    drawing_no: Optional[str] = Field(default=None, max_length=100)
    revision: Optional[str] = Field(default=None, max_length=20)
    part_name: str = Field(min_length=1, max_length=500)
    material_code: Optional[str] = Field(default=None, max_length=100)
    material_description_th: Optional[str] = Field(default=None, max_length=1000)
    material_length: Optional[str] = Field(default=None, max_length=100)
    cuts_per_box: Optional[float] = Field(default=None, ge=0)
    total_steps: Optional[float] = Field(default=None, ge=0)
    turning_steps: Optional[float] = Field(default=None, ge=0)
    milling_steps: Optional[str] = Field(default=None, max_length=50)
    color_code: Optional[str] = Field(default=None, max_length=20)
    color_description: Optional[str] = Field(default=None, max_length=200)
    unit_of_measure: str = Field(default="PCS", max_length=10)
    standard_cost: Optional[float] = Field(default=None, ge=0)
    material_cost: Optional[float] = Field(default=None, ge=0)
    labor_cost: Optional[float] = Field(default=None, ge=0)
    overhead_cost: Optional[float] = Field(default=None, ge=0)
    product_category: Optional[str] = Field(default=None, max_length=100)
    product_type: Optional[str] = Field(default=None, max_length=100)
    complexity_level: Optional[str] = Field(default=None, max_length=20)
    manufacturing_notes: Optional[str] = Field(default=None, max_length=2000)


class ATPProductCreate(ATPProductBase):
    """Schema for creating ATP products."""
    process_steps: Optional[Dict[str, str]] = Field(default_factory=dict)
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ATPProductUpdate(BaseModel):
    """Schema for updating ATP products."""
    drawing_no: Optional[str] = Field(default=None, max_length=100)
    revision: Optional[str] = Field(default=None, max_length=20)
    part_name: Optional[str] = Field(default=None, max_length=500)
    material_code: Optional[str] = Field(default=None, max_length=100)
    material_description_th: Optional[str] = Field(default=None, max_length=1000)
    material_length: Optional[str] = Field(default=None, max_length=100)
    cuts_per_box: Optional[float] = Field(default=None, ge=0)
    total_steps: Optional[float] = Field(default=None, ge=0)
    turning_steps: Optional[float] = Field(default=None, ge=0)
    milling_steps: Optional[str] = Field(default=None, max_length=50)
    color_code: Optional[str] = Field(default=None, max_length=20)
    color_description: Optional[str] = Field(default=None, max_length=200)
    standard_cost: Optional[float] = Field(default=None, ge=0)
    material_cost: Optional[float] = Field(default=None, ge=0)
    labor_cost: Optional[float] = Field(default=None, ge=0)
    overhead_cost: Optional[float] = Field(default=None, ge=0)
    product_category: Optional[str] = Field(default=None, max_length=100)
    product_type: Optional[str] = Field(default=None, max_length=100)
    manufacturing_notes: Optional[str] = Field(default=None, max_length=2000)
    process_steps: Optional[Dict[str, str]] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ATPProductResponse(ATPProductBase):
    """ATP product response schema."""
    id: int
    atp_material_code_id: Optional[int] = None
    atp_color_code_id: Optional[int] = None
    process_steps: Dict[str, str] = Field(default_factory=dict)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    complexity_level: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ATPProductSummary(BaseModel):
    """ATP product summary for listings."""
    id: int
    part_no: str
    part_name: str
    material_code: Optional[str] = None
    total_steps: Optional[float] = None
    complexity_level: Optional[str] = None
    color_description: Optional[str] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


# Production step schemas
class ATPProductionStepBase(BaseModel):
    """Base production step schema."""
    step_number: int = Field(ge=1, le=15)
    step_code: str = Field(max_length=50)
    step_description: Optional[str] = Field(default=None, max_length=500)
    step_type: Optional[str] = Field(default=None, max_length=50)
    estimated_time_minutes: Optional[int] = Field(default=None, ge=0)
    machine_required: Optional[str] = Field(default=None, max_length=255)
    tooling_required: Optional[str] = Field(default=None, max_length=500)
    tolerance: Optional[str] = Field(default=None, max_length=100)
    surface_finish: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=1000)


class ATPProductionStepCreate(ATPProductionStepBase):
    """Schema for creating production steps."""
    atp_product_id: int


class ATPProductionStepResponse(ATPProductionStepBase):
    """Production step response schema."""
    id: int
    atp_product_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Excel import schemas
class ATPProductExcelImport(BaseModel):
    """Schema for importing from Excel - matches Product Info Database structure."""
    part_no: str
    drawing_no: Optional[str] = None
    revision: Optional[str] = None
    part_name: Optional[str] = None
    material_code: Optional[str] = None
    material_description_th: Optional[str] = None
    material_length: Optional[str] = None
    cuts_per_box: Optional[float] = None
    total_steps: Optional[float] = None
    turning_steps: Optional[float] = None
    milling_steps: Optional[str] = None
    color_code: Optional[str] = None
    color_description: Optional[str] = None
    process_steps: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    model_config = {"populate_by_name": True}


class ATPProductBulkImportRequest(BaseModel):
    """ATP product bulk import request."""
    products: List[ATPProductCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False)


class ATPProductImportResponse(BaseModel):
    """ATP product import response."""
    total_processed: int
    created: int
    updated: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    success_rate: float


class ATPProductProcessingResult(BaseModel):
    """Result of processing ATP Product Excel file."""
    products_found: int
    products: List[ATPProductExcelImport]
    processing_errors: List[str] = Field(default_factory=list)


# Enhanced response schemas with relationships
class ATPProductDetailResponse(ATPProductResponse):
    """Detailed ATP product response with relationships."""
    atp_material_code: Optional[Dict[str, Any]] = None
    atp_color_code: Optional[Dict[str, Any]] = None
    production_steps: List[ATPProductionStepResponse] = Field(default_factory=list)
    production_summary: Optional[Dict[str, Any]] = None


class ATPProductSearchResult(BaseModel):
    """Search result for ATP products."""
    products: List[ATPProductSummary]
    total_count: int
    page: int
    per_page: int
    has_more: bool


# Analytics and reporting schemas
class ATPProductionAnalytics(BaseModel):
    """Production analytics summary."""
    total_products: int
    by_complexity: Dict[str, int] = Field(default_factory=dict)
    by_material_type: Dict[str, int] = Field(default_factory=dict)
    by_color: Dict[str, int] = Field(default_factory=dict)
    avg_steps_per_product: float
    total_production_time_minutes: int


class ATPMaterialUsageReport(BaseModel):
    """Material usage report."""
    material_code: str
    material_description: str
    product_count: int
    products: List[ATPProductSummary]
    total_estimated_cost: Optional[float] = None