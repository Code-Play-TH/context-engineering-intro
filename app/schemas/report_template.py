"""
Pydantic schemas for report template operations.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from app.models.report_template import TemplateType


class TemplateFilters(BaseModel):
    """Filters for listing templates."""
    search: Optional[str] = Field(None, description="Search in name and description")
    template_type: Optional[TemplateType] = Field(None, description="Filter by template type")
    is_shared: Optional[bool] = Field(None, description="Filter by shared status")
    created_by: Optional[int] = Field(None, description="Filter by creator")
    limit: int = Field(50, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class TemplateCreate(BaseModel):
    """Schema for creating a new template."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    template_type: TemplateType = Field(..., description="Template type (powerpoint or pdf)")
    is_shared: bool = Field(False, description="Whether template is shared with organization")
    structure: Dict[str, Any] = Field(..., description="Template layout definition")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    
    @validator('variables')
    def validate_variables(cls, v):
        """Validate template variables format."""
        for var in v:
            if not var.startswith('{{') or not var.endswith('}}'):
                raise ValueError(f"Variable '{var}' must be in format {{{{variable_name}}}}")
        return v
    
    @validator('structure')
    def validate_structure(cls, v, values):
        """Validate template structure based on type."""
        template_type = values.get('template_type')
        
        if template_type == TemplateType.POWERPOINT:
            if 'slides' not in v:
                raise ValueError("PowerPoint template must have 'slides' key")
            if not isinstance(v['slides'], list):
                raise ValueError("PowerPoint 'slides' must be a list")
        
        elif template_type == TemplateType.PDF:
            if 'pages' not in v:
                raise ValueError("PDF template must have 'pages' key")
            if not isinstance(v['pages'], list):
                raise ValueError("PDF 'pages' must be a list")
        
        return v


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    is_shared: Optional[bool] = Field(None, description="Whether template is shared with organization")
    structure: Optional[Dict[str, Any]] = Field(None, description="Template layout definition")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    
    @validator('variables')
    def validate_variables(cls, v):
        """Validate template variables format."""
        if v is not None:
            for var in v:
                if not var.startswith('{{') or not var.endswith('}}'):
                    raise ValueError(f"Variable '{var}' must be in format {{{{variable_name}}}}")
        return v


class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: int
    name: str
    description: Optional[str]
    template_type: TemplateType
    is_shared: bool
    structure: Dict[str, Any]
    variables: List[str]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Schema for template list response."""
    templates: List[TemplateResponse]
    total: int
    limit: int
    offset: int


class TemplateDuplicateRequest(BaseModel):
    """Schema for duplicating a template."""
    name: str = Field(..., min_length=1, max_length=255, description="New template name")
    description: Optional[str] = Field(None, max_length=1000, description="New template description")
    is_shared: bool = Field(False, description="Whether duplicated template is shared")