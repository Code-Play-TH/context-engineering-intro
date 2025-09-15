"""
Production department models.

Defines ProductionOrder and ProductionTracking models for manufacturing operations.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class ProductionOrder(BaseModel, table=True):
    """
    Production order model (ใบสั่งผลิต).
    
    Links customer requirements to production planning and tracking.
    """
    
    # Order identification
    production_order_no: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Unique production order number"
    )
    
    # Links to related orders
    customer_requirement_id: int = Field(
        foreign_key="customerrequirement.id",
        description="Source customer requirement"
    )
    product_id: int = Field(
        foreign_key="product.id",
        description="Product to be manufactured"
    )
    
    # Production quantities
    planned_quantity: int = Field(
        ge=0,
        description="Planned production quantity"
    )
    produced_quantity: int = Field(
        default=0,
        ge=0,
        description="Actual quantity produced so far"
    )
    
    # Scheduling
    start_date: Optional[datetime] = Field(
        default=None,
        description="Actual production start date"
    )
    target_completion_date: datetime = Field(
        description="Target completion date"
    )
    actual_completion_date: Optional[datetime] = Field(
        default=None,
        description="Actual completion date"
    )
    
    # Status and assignment
    production_status: str = Field(
        default="planned",
        max_length=50,
        description="Current production status"
    )
    priority: str = Field(
        default="normal",
        max_length=20,
        description="Production priority (low, normal, high, urgent)"
    )
    assigned_to_id: int = Field(
        foreign_key="user.id",
        description="Production manager responsible"
    )
    
    # ERPNext integration
    erpnext_work_order_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Corresponding ERPNext work order ID"
    )
    
    # Notes
    production_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Production notes and comments"
    )
    
    # Relationships
    customer_requirement: "CustomerRequirement" = Relationship(back_populates="production_orders")
    product: "Product" = Relationship()
    assigned_to: "User" = Relationship()
    production_tracking: list["ProductionTracking"] = Relationship(
        back_populates="production_order",
        cascade_delete=True
    )
    
    @property
    def completion_percentage(self) -> float:
        """
        Calculate production completion percentage.
        
        Returns:
            float: Percentage completed (0.0 to 100.0+)
        """
        if self.planned_quantity == 0:
            return 0.0
        return (self.produced_quantity / self.planned_quantity) * 100.0
    
    @property
    def remaining_quantity(self) -> int:
        """
        Calculate remaining quantity to produce.
        
        Returns:
            int: Quantity still needed
        """
        return max(0, self.planned_quantity - self.produced_quantity)
    
    @property
    def is_completed(self) -> bool:
        """
        Check if production is completed.
        
        Returns:
            bool: True if produced quantity meets or exceeds planned
        """
        return self.produced_quantity >= self.planned_quantity
    
    @property
    def is_overdue(self) -> bool:
        """
        Check if production is overdue.
        
        Returns:
            bool: True if past target date and not completed
        """
        return (
            datetime.utcnow() > self.target_completion_date and 
            not self.is_completed
        )
    
    @property
    def days_until_due(self) -> int:
        """
        Calculate days until due date.
        
        Returns:
            int: Days remaining (negative if overdue)
        """
        delta = self.target_completion_date - datetime.utcnow()
        return delta.days
    
    def start_production(self, start_date: Optional[datetime] = None) -> None:
        """
        Start production process.
        
        Args:
            start_date: Start date (defaults to now)
        """
        self.start_date = start_date or datetime.utcnow()
        self.production_status = "in_progress"
        self.touch()
    
    def complete_production(self, completion_date: Optional[datetime] = None) -> None:
        """
        Mark production as completed.
        
        Args:
            completion_date: Completion date (defaults to now)
        """
        self.actual_completion_date = completion_date or datetime.utcnow()
        self.production_status = "completed"
        self.touch()
    
    def update_production_quantity(self, new_quantity: int, note: Optional[str] = None) -> None:
        """
        Update produced quantity.
        
        Args:
            new_quantity: New produced quantity
            note: Optional note about the update
        """
        if new_quantity < 0:
            raise ValueError("Produced quantity cannot be negative")
        
        old_quantity = self.produced_quantity
        self.produced_quantity = new_quantity
        
        # Add note if provided
        if note:
            timestamp = datetime.utcnow().isoformat()
            update_note = f"[{timestamp}] Quantity updated from {old_quantity} to {new_quantity}: {note}"
            
            if self.production_notes:
                self.production_notes += f"\n{update_note}"
            else:
                self.production_notes = update_note
        
        # Auto-update status
        if self.is_completed and self.production_status != "completed":
            self.complete_production()
        
        self.touch()


class ProductionTracking(BaseModel, table=True):
    """
    Production tracking model for detailed step-by-step progress.
    
    Tracks individual production steps and operator performance.
    """
    
    # Links
    production_order_id: int = Field(
        foreign_key="productionorder.id",
        description="Related production order"
    )
    step_id: Optional[int] = Field(
        default=None,
        foreign_key="productionstep.id",
        description="Production step being tracked"
    )
    
    # Timing
    start_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Step start time"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="Step completion time"
    )
    
    # Production details
    quantity_produced: int = Field(
        ge=0,
        description="Quantity produced in this tracking entry"
    )
    operator_id: int = Field(
        foreign_key="user.id",
        description="Operator performing the work"
    )
    machine_used: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Machine or equipment used"
    )
    
    # Quality and notes
    quality_check_passed: bool = Field(
        default=True,
        description="Quality check result"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Production notes for this step"
    )
    
    # Relationships
    production_order: ProductionOrder = Relationship(back_populates="production_tracking")
    step: Optional["ProductionStep"] = Relationship()
    operator: "User" = Relationship()
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """
        Calculate step duration in minutes.
        
        Returns:
            Optional[int]: Duration in minutes if completed
        """
        if not self.end_time:
            return None
        
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def is_completed(self) -> bool:
        """
        Check if tracking entry is completed.
        
        Returns:
            bool: True if end_time is set
        """
        return self.end_time is not None
    
    def complete_step(self, end_time: Optional[datetime] = None) -> None:
        """
        Mark step as completed.
        
        Args:
            end_time: Completion time (defaults to now)
        """
        self.end_time = end_time or datetime.utcnow()
        self.touch()