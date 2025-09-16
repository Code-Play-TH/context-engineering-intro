"""
ATP-specific master data models matching actual Excel structure.

Contains Material Code and Color Code models based on your Excel file structure.
"""

from typing import Optional, List

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class ATPMaterialCode(BaseModel, table=True):
    """
    ATP Material Code master data.
    
    Based on actual Excel structure with Thai descriptions.
    """
    __tablename__ = "atp_material_code"
    
    # Primary identification (matches Excel columns)
    atp_code: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="ATP internal code"
    )
    material_code: str = Field(
        max_length=50,
        index=True,
        description="Material code identifier"
    )
    
    # Thai description field (รายละเอียด)
    description_th: str = Field(
        max_length=500,
        description="Material description in Thai"
    )
    description_en: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Material description in English (optional)"
    )
    
    # Physical specifications (ยาว/ท่อน)
    length_per_piece: Optional[float] = Field(
        default=None,
        ge=0,
        description="Length per piece in mm"
    )
    
    # Material grade (GRADE)
    grade: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Material grade (6061 T1, 6061 T6, etc.)"
    )
    
    # Weight specification (น้ำหนัก/เส้น)
    weight_per_line: Optional[float] = Field(
        default=None,
        ge=0,
        description="Weight per line in kg"
    )
    
    # Additional fields for manufacturing
    material_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Material type (Aluminum, Steel, etc.)"
    )
    cross_section: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Cross-section description"
    )
    
    # Cost information
    unit_cost: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost per unit/piece"
    )
    
    # Supplier information
    supplier: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Primary supplier"
    )
    
    # Usage notes
    usage_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Usage and application notes"
    )
    
    # Relationships
    products: List["Product"] = Relationship(back_populates="atp_material_code_ref")
    atp_products: List["ATPProduct"] = Relationship(back_populates="atp_material_code_ref")


class ATPColorCode(BaseModel, table=True):
    """
    ATP Color Code master data.
    
    Based on actual Excel structure with simple code-color mapping.
    """
    __tablename__ = "atp_color_code"
    
    # Primary identification (matches Excel columns)
    color_code: str = Field(
        max_length=20,
        unique=True,
        index=True,
        description="Color code (0, 1, 5, A, P, T, Z, etc.)"
    )
    color_name: str = Field(
        max_length=100,
        description="Color name (RAW, CHROME, RED, etc.)"
    )
    
    # Color specifications
    color_name_th: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Color name in Thai"
    )
    
    # Color type classification
    color_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Color type (Anodized, Plated, Paint, Raw, etc.)"
    )
    finish_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Finish type (Matte, Gloss, Hard, etc.)"
    )
    
    # Technical specifications
    hex_value: Optional[str] = Field(
        default=None,
        max_length=7,
        description="Hex color value (#RRGGBB)"
    )
    pantone_reference: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Pantone or other color standard reference"
    )
    
    # Manufacturing process
    process_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Manufacturing process (Anodizing, Plating, Coating, etc.)"
    )
    process_temperature: Optional[float] = Field(
        default=None,
        description="Process temperature in Celsius"
    )
    process_time: Optional[int] = Field(
        default=None,
        ge=0,
        description="Process time in minutes"
    )
    
    # Cost information
    cost_per_sqm: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost per square meter"
    )
    
    # Quality specifications
    thickness: Optional[float] = Field(
        default=None,
        ge=0,
        description="Coating thickness in microns"
    )
    durability_rating: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Durability rating"
    )
    
    # Supplier information
    supplier: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Color process supplier"
    )
    supplier_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Supplier's color code"
    )
    
    # Usage notes
    application_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Application and usage notes"
    )
    
    # Special properties
    is_raw_material: bool = Field(
        default=False,
        description="True if this represents raw/unfinished material"
    )
    requires_special_handling: bool = Field(
        default=False,
        description="True if requires special handling"
    )
    
    # Relationships
    products: List["Product"] = Relationship(back_populates="atp_color_code_ref")
    atp_products: List["ATPProduct"] = Relationship(back_populates="atp_color_code_ref")


# Update imports for relationships
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.atp_product import ATPProduct