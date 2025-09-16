"""
Master data models for lookups and reference data.

Contains Material Code and Color Code master tables for product specifications.
"""

from typing import Optional, List

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class MaterialCode(BaseModel, table=True):
    """
    Material Code master data.
    
    Defines material specifications, properties, and classifications
    used in product manufacturing.
    """
    
    # Primary identification
    material_code: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="Unique material code identifier"
    )
    material_name: str = Field(
        max_length=255,
        description="Material name/description"
    )
    
    # Classification
    material_category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Material category (Steel, Aluminum, Plastic, etc.)"
    )
    material_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Material type subcategory"
    )
    
    # Physical properties
    density: Optional[float] = Field(
        default=None,
        ge=0,
        description="Material density (g/cm³)"
    )
    melting_point: Optional[float] = Field(
        default=None,
        description="Melting point in Celsius"
    )
    hardness: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Material hardness specification"
    )
    
    # Business properties
    standard_thickness: Optional[float] = Field(
        default=None,
        ge=0,
        description="Standard thickness in mm"
    )
    unit_weight: Optional[float] = Field(
        default=None,
        ge=0,
        description="Weight per unit (kg/m², kg/m, etc.)"
    )
    cost_per_unit: Optional[float] = Field(
        default=None,
        ge=0,
        description="Standard cost per unit"
    )
    
    # Supplier information
    primary_supplier: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Primary supplier name"
    )
    supplier_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Supplier's material code"
    )
    
    # Technical specifications
    tensile_strength: Optional[float] = Field(
        default=None,
        description="Tensile strength (MPa)"
    )
    yield_strength: Optional[float] = Field(
        default=None,
        description="Yield strength (MPa)"
    )
    surface_finish: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Standard surface finish"
    )
    
    # Additional notes
    specifications: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional material specifications"
    )
    handling_notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Special handling requirements"
    )
    
    # Relationships
    products: List["Product"] = Relationship(back_populates="material_code_ref")


class ColorCode(BaseModel, table=True):
    """
    Color Code master data.
    
    Defines standard colors used in product manufacturing and finishing.
    """
    
    # Primary identification
    color_code: str = Field(
        max_length=20,
        unique=True,
        index=True,
        description="Unique color code identifier"
    )
    color_name: str = Field(
        max_length=100,
        description="Color name/description"
    )
    
    # Color specifications
    hex_value: Optional[str] = Field(
        default=None,
        max_length=7,
        description="Hex color value (#RRGGBB)"
    )
    rgb_value: Optional[str] = Field(
        default=None,
        max_length=20,
        description="RGB color value (255,255,255)"
    )
    cmyk_value: Optional[str] = Field(
        default=None,
        max_length=20,
        description="CMYK color value for printing"
    )
    
    # Industry standards
    pantone_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Pantone color code"
    )
    ral_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="RAL color code"
    )
    ncs_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="NCS (Natural Color System) code"
    )
    
    # Color properties
    color_family: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Color family (Red, Blue, Green, etc.)"
    )
    color_intensity: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Color intensity (Light, Medium, Dark)"
    )
    finish_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Finish type (Matte, Glossy, Satin, etc.)"
    )
    
    # Manufacturing properties
    paint_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Paint/coating type"
    )
    cure_temperature: Optional[float] = Field(
        default=None,
        description="Curing temperature in Celsius"
    )
    cure_time_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Curing time in minutes"
    )
    
    # Cost and supplier
    cost_per_liter: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost per liter of paint/coating"
    )
    coverage_per_liter: Optional[float] = Field(
        default=None,
        ge=0,
        description="Coverage area per liter (m²)"
    )
    supplier_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Paint/coating supplier"
    )
    supplier_product_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Supplier's product code"
    )
    
    # Quality specifications
    color_tolerance: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Acceptable color tolerance"
    )
    uv_resistance: Optional[str] = Field(
        default=None,
        max_length=50,
        description="UV resistance rating"
    )
    weather_resistance: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Weather resistance rating"
    )
    
    # Additional notes
    application_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Application instructions and notes"
    )
    
    # Relationships
    products: List["Product"] = Relationship(back_populates="color_code_ref")


# Update imports for relationships
from app.models.product import Product