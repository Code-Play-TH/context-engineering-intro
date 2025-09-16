"""
Schemas for master data (Material Code and Color Code).

Contains Pydantic schemas for request/response validation of master data.
"""

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


# Material Code schemas
class MaterialCodeBase(BaseModel):
    """Base material code schema."""
    material_code: str = Field(min_length=1, max_length=50)
    material_name: str = Field(min_length=1, max_length=255)
    material_category: Optional[str] = Field(default=None, max_length=100)
    material_type: Optional[str] = Field(default=None, max_length=100)
    density: Optional[float] = Field(default=None, ge=0)
    melting_point: Optional[float] = Field(default=None)
    hardness: Optional[str] = Field(default=None, max_length=50)
    standard_thickness: Optional[float] = Field(default=None, ge=0)
    unit_weight: Optional[float] = Field(default=None, ge=0)
    cost_per_unit: Optional[float] = Field(default=None, ge=0)
    primary_supplier: Optional[str] = Field(default=None, max_length=255)
    supplier_code: Optional[str] = Field(default=None, max_length=100)
    tensile_strength: Optional[float] = Field(default=None)
    yield_strength: Optional[float] = Field(default=None)
    surface_finish: Optional[str] = Field(default=None, max_length=100)
    specifications: Optional[str] = Field(default=None, max_length=1000)
    handling_notes: Optional[str] = Field(default=None, max_length=500)


class MaterialCodeCreate(MaterialCodeBase):
    """Schema for creating material codes."""
    pass


class MaterialCodeUpdate(BaseModel):
    """Schema for updating material codes."""
    material_name: Optional[str] = Field(default=None, max_length=255)
    material_category: Optional[str] = Field(default=None, max_length=100)
    material_type: Optional[str] = Field(default=None, max_length=100)
    density: Optional[float] = Field(default=None, ge=0)
    melting_point: Optional[float] = Field(default=None)
    hardness: Optional[str] = Field(default=None, max_length=50)
    standard_thickness: Optional[float] = Field(default=None, ge=0)
    unit_weight: Optional[float] = Field(default=None, ge=0)
    cost_per_unit: Optional[float] = Field(default=None, ge=0)
    primary_supplier: Optional[str] = Field(default=None, max_length=255)
    supplier_code: Optional[str] = Field(default=None, max_length=100)
    tensile_strength: Optional[float] = Field(default=None)
    yield_strength: Optional[float] = Field(default=None)
    surface_finish: Optional[str] = Field(default=None, max_length=100)
    specifications: Optional[str] = Field(default=None, max_length=1000)
    handling_notes: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class MaterialCodeResponse(MaterialCodeBase):
    """Material code response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MaterialCodeSummary(BaseModel):
    """Material code summary for lookups."""
    id: int
    material_code: str
    material_name: str
    material_category: Optional[str] = None
    cost_per_unit: Optional[float] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


# Color Code schemas
class ColorCodeBase(BaseModel):
    """Base color code schema."""
    color_code: str = Field(min_length=1, max_length=20)
    color_name: str = Field(min_length=1, max_length=100)
    hex_value: Optional[str] = Field(default=None, max_length=7)
    rgb_value: Optional[str] = Field(default=None, max_length=20)
    cmyk_value: Optional[str] = Field(default=None, max_length=20)
    pantone_code: Optional[str] = Field(default=None, max_length=20)
    ral_code: Optional[str] = Field(default=None, max_length=20)
    ncs_code: Optional[str] = Field(default=None, max_length=20)
    color_family: Optional[str] = Field(default=None, max_length=50)
    color_intensity: Optional[str] = Field(default=None, max_length=50)
    finish_type: Optional[str] = Field(default=None, max_length=100)
    paint_type: Optional[str] = Field(default=None, max_length=100)
    cure_temperature: Optional[float] = Field(default=None)
    cure_time_minutes: Optional[int] = Field(default=None, ge=0)
    cost_per_liter: Optional[float] = Field(default=None, ge=0)
    coverage_per_liter: Optional[float] = Field(default=None, ge=0)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    supplier_product_code: Optional[str] = Field(default=None, max_length=100)
    color_tolerance: Optional[str] = Field(default=None, max_length=100)
    uv_resistance: Optional[str] = Field(default=None, max_length=50)
    weather_resistance: Optional[str] = Field(default=None, max_length=50)
    application_notes: Optional[str] = Field(default=None, max_length=1000)


class ColorCodeCreate(ColorCodeBase):
    """Schema for creating color codes."""
    pass


class ColorCodeUpdate(BaseModel):
    """Schema for updating color codes."""
    color_name: Optional[str] = Field(default=None, max_length=100)
    hex_value: Optional[str] = Field(default=None, max_length=7)
    rgb_value: Optional[str] = Field(default=None, max_length=20)
    cmyk_value: Optional[str] = Field(default=None, max_length=20)
    pantone_code: Optional[str] = Field(default=None, max_length=20)
    ral_code: Optional[str] = Field(default=None, max_length=20)
    ncs_code: Optional[str] = Field(default=None, max_length=20)
    color_family: Optional[str] = Field(default=None, max_length=50)
    color_intensity: Optional[str] = Field(default=None, max_length=50)
    finish_type: Optional[str] = Field(default=None, max_length=100)
    paint_type: Optional[str] = Field(default=None, max_length=100)
    cure_temperature: Optional[float] = Field(default=None)
    cure_time_minutes: Optional[int] = Field(default=None, ge=0)
    cost_per_liter: Optional[float] = Field(default=None, ge=0)
    coverage_per_liter: Optional[float] = Field(default=None, ge=0)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    supplier_product_code: Optional[str] = Field(default=None, max_length=100)
    color_tolerance: Optional[str] = Field(default=None, max_length=100)
    uv_resistance: Optional[str] = Field(default=None, max_length=50)
    weather_resistance: Optional[str] = Field(default=None, max_length=50)
    application_notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class ColorCodeResponse(ColorCodeBase):
    """Color code response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ColorCodeSummary(BaseModel):
    """Color code summary for lookups."""
    id: int
    color_code: str
    color_name: str
    hex_value: Optional[str] = None
    color_family: Optional[str] = None
    finish_type: Optional[str] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


# Bulk import schemas
class MaterialCodeBulkImportRequest(BaseModel):
    """Material code bulk import request."""
    material_codes: List[MaterialCodeCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False)


class ColorCodeBulkImportRequest(BaseModel):
    """Color code bulk import request."""
    color_codes: List[ColorCodeCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False)


class MasterDataImportResponse(BaseModel):
    """Master data import response."""
    total_processed: int
    created: int
    updated: int
    errors: List[dict] = Field(default_factory=list)
    success_rate: float