"""
ATP-specific master data schemas matching actual Excel structure.

Contains Pydantic schemas for ATP Material Code and Color Code data.
"""

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


# ATP Material Code schemas
class ATPMaterialCodeBase(BaseModel):
    """Base ATP material code schema."""
    atp_code: str = Field(min_length=1, max_length=50)
    material_code: str = Field(min_length=1, max_length=50)
    description_th: str = Field(min_length=1, max_length=500)
    description_en: Optional[str] = Field(default=None, max_length=500)
    length_per_piece: Optional[float] = Field(default=None, ge=0)
    grade: Optional[str] = Field(default=None, max_length=50)
    weight_per_line: Optional[float] = Field(default=None, ge=0)
    material_type: Optional[str] = Field(default=None, max_length=100)
    cross_section: Optional[str] = Field(default=None, max_length=200)
    unit_cost: Optional[float] = Field(default=None, ge=0)
    supplier: Optional[str] = Field(default=None, max_length=255)
    usage_notes: Optional[str] = Field(default=None, max_length=1000)


class ATPMaterialCodeCreate(ATPMaterialCodeBase):
    """Schema for creating ATP material codes."""
    pass


class ATPMaterialCodeUpdate(BaseModel):
    """Schema for updating ATP material codes."""
    material_code: Optional[str] = Field(default=None, max_length=50)
    description_th: Optional[str] = Field(default=None, max_length=500)
    description_en: Optional[str] = Field(default=None, max_length=500)
    length_per_piece: Optional[float] = Field(default=None, ge=0)
    grade: Optional[str] = Field(default=None, max_length=50)
    weight_per_line: Optional[float] = Field(default=None, ge=0)
    material_type: Optional[str] = Field(default=None, max_length=100)
    cross_section: Optional[str] = Field(default=None, max_length=200)
    unit_cost: Optional[float] = Field(default=None, ge=0)
    supplier: Optional[str] = Field(default=None, max_length=255)
    usage_notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class ATPMaterialCodeResponse(ATPMaterialCodeBase):
    """ATP material code response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ATPMaterialCodeSummary(BaseModel):
    """ATP material code summary for lookups."""
    id: int
    atp_code: str
    material_code: str
    description_th: str
    grade: Optional[str] = None
    weight_per_line: Optional[float] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


# ATP Color Code schemas
class ATPColorCodeBase(BaseModel):
    """Base ATP color code schema."""
    color_code: str = Field(min_length=1, max_length=20)
    color_name: str = Field(min_length=1, max_length=100)
    color_name_th: Optional[str] = Field(default=None, max_length=100)
    color_type: Optional[str] = Field(default=None, max_length=50)
    finish_type: Optional[str] = Field(default=None, max_length=50)
    hex_value: Optional[str] = Field(default=None, max_length=7)
    pantone_reference: Optional[str] = Field(default=None, max_length=50)
    process_type: Optional[str] = Field(default=None, max_length=100)
    process_temperature: Optional[float] = Field(default=None)
    process_time: Optional[int] = Field(default=None, ge=0)
    cost_per_sqm: Optional[float] = Field(default=None, ge=0)
    thickness: Optional[float] = Field(default=None, ge=0)
    durability_rating: Optional[str] = Field(default=None, max_length=50)
    supplier: Optional[str] = Field(default=None, max_length=255)
    supplier_code: Optional[str] = Field(default=None, max_length=100)
    application_notes: Optional[str] = Field(default=None, max_length=1000)
    is_raw_material: bool = Field(default=False)
    requires_special_handling: bool = Field(default=False)


class ATPColorCodeCreate(ATPColorCodeBase):
    """Schema for creating ATP color codes."""
    pass


class ATPColorCodeUpdate(BaseModel):
    """Schema for updating ATP color codes."""
    color_name: Optional[str] = Field(default=None, max_length=100)
    color_name_th: Optional[str] = Field(default=None, max_length=100)
    color_type: Optional[str] = Field(default=None, max_length=50)
    finish_type: Optional[str] = Field(default=None, max_length=50)
    hex_value: Optional[str] = Field(default=None, max_length=7)
    pantone_reference: Optional[str] = Field(default=None, max_length=50)
    process_type: Optional[str] = Field(default=None, max_length=100)
    process_temperature: Optional[float] = Field(default=None)
    process_time: Optional[int] = Field(default=None, ge=0)
    cost_per_sqm: Optional[float] = Field(default=None, ge=0)
    thickness: Optional[float] = Field(default=None, ge=0)
    durability_rating: Optional[str] = Field(default=None, max_length=50)
    supplier: Optional[str] = Field(default=None, max_length=255)
    supplier_code: Optional[str] = Field(default=None, max_length=100)
    application_notes: Optional[str] = Field(default=None, max_length=1000)
    is_raw_material: Optional[bool] = None
    requires_special_handling: Optional[bool] = None
    is_active: Optional[bool] = None


class ATPColorCodeResponse(ATPColorCodeBase):
    """ATP color code response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ATPColorCodeSummary(BaseModel):
    """ATP color code summary for lookups."""
    id: int
    color_code: str
    color_name: str
    color_type: Optional[str] = None
    is_raw_material: bool
    is_active: bool
    
    model_config = {"from_attributes": True}


# Excel import schemas (matching your Excel structure)
class ATPMaterialCodeExcelImport(BaseModel):
    """Schema for importing from Excel - matches exact column names."""
    atp_code: str = Field(alias="ATP Code")
    material_code: str = Field(alias="Material Code") 
    description_th: str = Field(alias="รายละเอียด")
    length_per_piece: Optional[float] = Field(default=None, alias="ยาว/ท่อน")
    grade: Optional[str] = Field(default=None, alias="GRADE")
    weight_per_line: Optional[float] = Field(default=None, alias="น้ำหนัก/เส้น")
    
    model_config = {"populate_by_name": True}


class ATPColorCodeExcelImport(BaseModel):
    """Schema for importing from Excel - matches exact column names."""
    color_code: str = Field(alias="Color Code")
    color_name: str = Field(alias="Color")
    
    model_config = {"populate_by_name": True}


# Bulk import schemas
class ATPMaterialCodeBulkImportRequest(BaseModel):
    """ATP material code bulk import request."""
    material_codes: List[ATPMaterialCodeCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False)


class ATPColorCodeBulkImportRequest(BaseModel):
    """ATP color code bulk import request."""
    color_codes: List[ATPColorCodeCreate] = Field(min_length=1)
    update_existing: bool = Field(default=False)


class ATPMasterDataImportResponse(BaseModel):
    """ATP master data import response."""
    total_processed: int
    created: int
    updated: int
    errors: List[dict] = Field(default_factory=list)
    success_rate: float


# Excel processing results
class ATPExcelProcessingResult(BaseModel):
    """Result of processing ATP Excel file."""
    material_codes_found: int
    color_codes_found: int
    material_codes: List[ATPMaterialCodeExcelImport]
    color_codes: List[ATPColorCodeExcelImport]
    processing_errors: List[str] = Field(default_factory=list)