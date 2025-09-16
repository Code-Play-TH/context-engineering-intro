"""
ATP Product models matching actual Excel structure.

Handles products from Product Info Database sheet with proper relationships
to ATP Material Code master data and production process management.
"""

from typing import Optional, List, Dict, Any
import json

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class ATPProductionStep(BaseModel, table=True):
    """
    ATP Production step model for manufacturing processes.
    
    Stores individual process steps (P1-P15) from Excel data.
    """
    __tablename__ = "atp_production_step"
    
    # Foreign key to ATP product
    atp_product_id: int = Field(foreign_key="atp_product.id")
    
    # Step identification
    step_number: int = Field(ge=1, le=15, description="Step number (1-15)")
    step_code: str = Field(max_length=50, description="Step code (e.g., L1, L2, M1)")
    step_description: Optional[str] = Field(default=None, max_length=500)
    
    # Step classification
    step_type: Optional[str] = Field(
        default=None, 
        max_length=50, 
        description="Step type (turning, milling, etc.)"
    )
    
    # Time estimates (if available)
    estimated_time_minutes: Optional[int] = Field(default=None, ge=0)
    
    # Equipment requirements
    machine_required: Optional[str] = Field(default=None, max_length=255)
    tooling_required: Optional[str] = Field(default=None, max_length=500)
    
    # Quality requirements
    tolerance: Optional[str] = Field(default=None, max_length=100)
    surface_finish: Optional[str] = Field(default=None, max_length=100)
    
    # Notes
    notes: Optional[str] = Field(default=None, max_length=1000)
    
    # Relationships
    atp_product: "ATPProduct" = Relationship(back_populates="production_steps")


class ATPProduct(BaseModel, table=True):
    """
    ATP Product model matching Product Info Database Excel structure.
    
    Comprehensive product data with material relationships and production processes.
    """
    __tablename__ = "atp_product"
    
    # Core product identification (from Excel)
    part_no: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Part number - primary identifier"
    )
    drawing_no: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Engineering drawing number"
    )
    revision: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Drawing revision"
    )
    part_name: str = Field(max_length=500, description="Product name")
    
    # Material relationships
    material_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Material code from Excel"
    )
    atp_material_code_id: Optional[int] = Field(
        default=None,
        foreign_key="atp_material_code.id",
        description="Reference to ATP Material Code master data"
    )
    
    # Material specifications (Thai descriptions from Excel)
    material_description_th: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="รายละเอียดวัตถุดิบ - Material description in Thai"
    )
    material_length: Optional[str] = Field(
        default=None,
        max_length=100,
        description="ความยาววัตถุดิบ - Material length specification"
    )
    cuts_per_box: Optional[float] = Field(
        default=None,
        ge=0,
        description="จำนวนตัด/ลัง - Number of cuts per box"
    )
    
    # Production process summary
    total_steps: Optional[float] = Field(
        default=None,
        ge=0,
        description="ขั้นตอนทั้งหมด - Total production steps"
    )
    turning_steps: Optional[float] = Field(
        default=None,
        ge=0,
        description="ขั้นตอนงานกลึง - Turning operation steps"
    )
    milling_steps: Optional[str] = Field(
        default=None,
        max_length=50,
        description="ขั้นตอนงานกัด - Milling operation steps"
    )
    
    # Color information (extracted from part name)
    color_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Extracted color code"
    )
    color_description: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Color description (e.g., MATT BLACK, ดำด้าน)"
    )
    atp_color_code_id: Optional[int] = Field(
        default=None,
        foreign_key="atp_color_code.id",
        description="Reference to ATP Color Code master data"
    )
    
    # Manufacturing specifications
    unit_of_measure: str = Field(
        default="PCS",
        max_length=10,
        description="Unit of measurement"
    )
    
    # Process steps as JSON (P1-P15 from Excel)
    process_steps_json: Optional[str] = Field(
        default=None,
        description="JSON object storing P1-P15 process steps"
    )
    
    # Cost information
    standard_cost: Optional[float] = Field(default=None, ge=0)
    material_cost: Optional[float] = Field(default=None, ge=0)
    labor_cost: Optional[float] = Field(default=None, ge=0)
    overhead_cost: Optional[float] = Field(default=None, ge=0)
    
    # Status and classification
    product_category: Optional[str] = Field(default=None, max_length=100)
    product_type: Optional[str] = Field(default=None, max_length=100)
    complexity_level: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Simple, Medium, Complex based on step count"
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
    
    # Manufacturing notes
    manufacturing_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Manufacturing and quality notes"
    )
    
    # Relationships
    atp_material_code_ref: Optional["ATPMaterialCode"] = Relationship(
        back_populates="atp_products"
    )
    atp_color_code_ref: Optional["ATPColorCode"] = Relationship(
        back_populates="atp_products"
    )
    production_steps: List[ATPProductionStep] = Relationship(
        back_populates="atp_product"
    )
    
    @property
    def process_steps(self) -> Dict[str, str]:
        """
        Get process steps as dictionary.
        
        Returns:
            Dict[str, str]: Process steps (P1-P15)
        """
        if not self.process_steps_json:
            return {}
        try:
            return json.loads(self.process_steps_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @process_steps.setter
    def process_steps(self, value: Dict[str, str]) -> None:
        """
        Set process steps from dictionary.
        
        Args:
            value: Process steps dictionary
        """
        self.process_steps_json = json.dumps(value)
    
    def add_process_step(self, step: str, code: str) -> None:
        """
        Add or update a process step.
        
        Args:
            step: Step identifier (P1, P2, etc.)
            code: Step code (L1, L2, M1, etc.)
        """
        steps = self.process_steps
        steps[step] = code
        self.process_steps = steps
        self.touch()
    
    def get_process_step(self, step: str) -> Optional[str]:
        """
        Get a specific process step code.
        
        Args:
            step: Step identifier (P1, P2, etc.)
            
        Returns:
            Optional[str]: Step code or None
        """
        return self.process_steps.get(step)
    
    def extract_color_from_name(self) -> None:
        """
        Extract color information from part name.
        
        Looks for color keywords in the part name and sets color fields.
        """
        if not self.part_name:
            return
            
        name_upper = self.part_name.upper()
        
        # Common color patterns
        color_patterns = {
            'MATT BLACK': ('0', 'MATT BLACK', 'ดำด้าน'),
            'BLACK': ('8', 'BLACK', 'ดำ'),
            'WHITE': ('2', 'WHITE', 'ขาว'),
            'RED': ('5', 'RED', 'แดง'),
            'BLUE': ('6', 'BLUE', 'น้ำเงิน'),
            'CHROME': ('1', 'CHROME', 'โครม'),
            'GOLD': ('3', 'GOLD', 'ทอง'),
            'YELLOW': ('4', 'YELLOW', 'เหลือง'),
            'ORANGE': ('7', 'ORANGE', 'ส้ม'),
        }
        
        for color_name, (code, desc_en, desc_th) in color_patterns.items():
            if color_name in name_upper:
                self.color_code = code
                self.color_description = f"{desc_en}({desc_th})"
                break
    
    def calculate_complexity_level(self) -> str:
        """
        Calculate complexity level based on step count.
        
        Returns:
            str: Complexity level (Simple, Medium, Complex)
        """
        if not self.total_steps:
            return "Unknown"
        
        if self.total_steps <= 2:
            return "Simple"
        elif self.total_steps <= 5:
            return "Medium"
        else:
            return "Complex"
    
    def update_complexity_level(self) -> None:
        """Update complexity level based on current step count."""
        self.complexity_level = self.calculate_complexity_level()
        self.touch()
    
    @property
    def specifications(self) -> Dict[str, Any]:
        """
        Get product specifications as dictionary.
        
        Returns:
            Dict[str, Any]: Product specifications
        """
        if not self.specifications_json:
            return {}
        try:
            return json.loads(self.specifications_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @specifications.setter
    def specifications(self, value: Dict[str, Any]) -> None:
        """
        Set product specifications from dictionary.
        
        Args:
            value: Specifications dictionary
        """
        self.specifications_json = json.dumps(value)
    
    def get_total_estimated_time(self) -> int:
        """
        Calculate total estimated production time from steps.
        
        Returns:
            int: Total time in minutes
        """
        return sum(
            step.estimated_time_minutes or 0 
            for step in self.production_steps
        )
    
    def get_production_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive production summary.
        
        Returns:
            Dict[str, Any]: Production summary including materials and processes
        """
        return {
            "part_no": self.part_no,
            "part_name": self.part_name,
            "material_code": self.material_code,
            "material_description": self.material_description_th,
            "total_steps": self.total_steps,
            "turning_steps": self.turning_steps,
            "milling_steps": self.milling_steps,
            "complexity_level": self.complexity_level,
            "process_steps": self.process_steps,
            "color_info": {
                "code": self.color_code,
                "description": self.color_description
            },
            "estimated_time_minutes": self.get_total_estimated_time()
        }


# Update imports for relationships
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.atp_master_data import ATPMaterialCode, ATPColorCode