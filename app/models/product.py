"""
Product management models.

Defines Product and ProductionStep models for manufacturing data.
"""

import json
from typing import Optional, List, Any

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class ProductionStep(BaseModel, table=True):
    """
    Production step model for manufacturing processes.
    
    Defines individual steps in the production process for products.
    """
    
    product_id: int = Field(foreign_key="product.id")
    step_number: int = Field(ge=1, description="Step sequence number")
    step_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    estimated_time_minutes: Optional[int] = Field(default=None, ge=0)
    machine_required: Optional[str] = Field(default=None, max_length=255)
    skill_level: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Required skill level (beginner, intermediate, advanced)"
    )
    notes: Optional[str] = Field(default=None, max_length=1000)
    
    # Relationships
    product: "Product" = Relationship(back_populates="production_steps")


class Product(BaseModel, table=True):
    """
    Product master data model.
    
    Central repository for all product information including specifications
    and production requirements. Implements VLOOKUP functionality from Excel.
    """
    
    # Core product identification
    part_no: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Unique part number - primary identifier"
    )
    part_name: str = Field(max_length=255, description="Product name")
    
    # Technical specifications
    drawing_no: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Engineering drawing number"
    )
    material_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Material specification code"
    )
    material_description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Detailed material description"
    )
    
    # Business information
    unit_of_measure: str = Field(
        default="PCS",
        max_length=10,
        description="Unit of measurement (PCS, KG, M, etc.)"
    )
    standard_cost: Optional[float] = Field(
        default=None,
        ge=0,
        description="Standard cost per unit"
    )
    
    # Manufacturing data
    production_steps_json: Optional[str] = Field(
        default=None,
        description="JSON array of production steps (legacy support)"
    )
    
    # ERPNext integration
    erpnext_item_code: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Corresponding ERPNext item code"
    )
    
    # Additional specifications
    specifications_json: Optional[str] = Field(
        default="{}",
        description="JSON object for additional product specifications"
    )
    
    # Relationships
    production_steps: List[ProductionStep] = Relationship(
        back_populates="product"
    )
    
    @property
    def specifications(self) -> dict[str, Any]:
        """
        Get product specifications as dictionary.
        
        Returns:
            dict: Product specifications
        """
        if not self.specifications_json:
            return {}
        try:
            return json.loads(self.specifications_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @specifications.setter
    def specifications(self, value: dict[str, Any]) -> None:
        """
        Set product specifications from dictionary.
        
        Args:
            value: Specifications dictionary
        """
        self.specifications_json = json.dumps(value)
    
    def add_specification(self, key: str, value: Any) -> None:
        """
        Add or update a single specification.
        
        Args:
            key: Specification key
            value: Specification value
        """
        specs = self.specifications
        specs[key] = value
        self.specifications = specs
        self.touch()
    
    def get_specification(self, key: str, default: Any = None) -> Any:
        """
        Get a specific specification value.
        
        Args:
            key: Specification key
            default: Default value if key not found
            
        Returns:
            Any: Specification value or default
        """
        return self.specifications.get(key, default)
    
    def get_total_production_time(self) -> int:
        """
        Calculate total estimated production time.
        
        Returns:
            int: Total time in minutes
        """
        return sum(
            step.estimated_time_minutes or 0 
            for step in self.production_steps
        )
    
    def get_production_steps_summary(self) -> List[dict[str, Any]]:
        """
        Get a summary of all production steps.
        
        Returns:
            List[dict]: List of production step summaries
        """
        return [
            {
                "step_number": step.step_number,
                "step_name": step.step_name,
                "estimated_time_minutes": step.estimated_time_minutes,
                "machine_required": step.machine_required,
                "skill_level": step.skill_level,
            }
            for step in sorted(self.production_steps, key=lambda x: x.step_number)
        ]