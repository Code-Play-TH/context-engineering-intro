"""
Sales department models.

Defines CustomerRequirement and Customer models with business logic calculations.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class Customer(BaseModel, table=True):
    """
    Customer master data model.
    
    Central repository for customer information.
    """
    
    customer_code: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="Unique customer code"
    )
    customer_name: str = Field(
        max_length=255,
        index=True,
        description="Customer company name"
    )
    contact_person: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Primary contact person"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Customer email address"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Customer phone number"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Customer address"
    )
    payment_terms: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Payment terms (Net 30, COD, etc.)"
    )
    
    # ERPNext integration
    erpnext_customer_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Corresponding ERPNext customer ID"
    )
    
    # Relationships
    customer_requirements: list["CustomerRequirement"] = Relationship(
        back_populates="customer_data"
    )


class CustomerRequirement(BaseModel, table=True):
    """
    Customer requirement model (ใบรับความต้องการลูกค้า).
    
    Represents customer orders with business logic calculations.
    Implements Excel formulas for shortage/surplus and status tracking.
    """
    
    # Order identification
    sale_no: str = Field(
        max_length=100,
        index=True,
        description="Sales order number"
    )
    po_no: str = Field(
        max_length=100,
        index=True,
        description="Purchase order number from customer"
    )
    
    # Customer information
    customer_name: str = Field(
        max_length=255,
        description="Customer name (for quick access)"
    )
    customer_id: Optional[int] = Field(
        default=None,
        foreign_key="customer.id",
        description="Link to customer master data"
    )
    
    # Product information
    product_id: int = Field(
        foreign_key="product.id",
        description="Product being ordered"
    )
    
    # Order details
    due_date: datetime = Field(description="Required delivery date")
    po_quantity: int = Field(
        ge=0,
        description="Quantity ordered by customer"
    )
    delivered_quantity: int = Field(
        default=0,
        ge=0,
        description="Quantity already delivered"
    )
    unit_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Price per unit"
    )
    
    # Status tracking
    status: str = Field(
        default="pending",
        max_length=50,
        description="Overall order status"
    )
    
    # User assignment
    sales_person_id: int = Field(
        foreign_key="user.id",
        description="Sales person responsible"
    )
    
    # ERPNext integration
    erpnext_sales_order_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Corresponding ERPNext sales order ID"
    )
    
    # Notes and comments
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional notes or comments"
    )
    
    # Relationships
    product: "Product" = Relationship()
    customer_data: Optional[Customer] = Relationship(back_populates="customer_requirements")
    sales_person: "User" = Relationship()
    production_orders: list["ProductionOrder"] = Relationship(back_populates="customer_requirement")
    
    @property
    def shortage_surplus(self) -> int:
        """
        Calculate shortage or surplus quantity.
        
        Excel formula: =จำนวนส่งมอบ - PO QTY (Delivered QTY - PO QTY)
        
        Returns:
            int: Positive = surplus, negative = shortage, zero = exact
        """
        return self.delivered_quantity - self.po_quantity
    
    @property
    def summary_status(self) -> str:
        """
        Calculate summary status based on delivery.
        
        Excel formula: IF(ขาด/เกิน >= 0, "ครบ", "ขาด")
        Translation: IF(shortage_surplus >= 0, "Complete", "Shortage")
        
        Returns:
            str: "Complete" if delivered >= ordered, "Shortage" otherwise
        """
        return "Complete" if self.shortage_surplus >= 0 else "Shortage"
    
    @property
    def total_value(self) -> Optional[float]:
        """
        Calculate total order value.
        
        Returns:
            Optional[float]: Total value if unit_price is set
        """
        if self.unit_price is None:
            return None
        return self.po_quantity * self.unit_price
    
    @property
    def delivery_percentage(self) -> float:
        """
        Calculate delivery completion percentage.
        
        Returns:
            float: Percentage of order delivered (0.0 to 100.0+)
        """
        if self.po_quantity == 0:
            return 0.0
        return (self.delivered_quantity / self.po_quantity) * 100.0
    
    @property
    def is_overdue(self) -> bool:
        """
        Check if order is overdue.
        
        Returns:
            bool: True if past due date and not complete
        """
        return (
            datetime.utcnow() > self.due_date and 
            self.summary_status == "Shortage"
        )
    
    def update_delivery(self, quantity: int, note: Optional[str] = None) -> None:
        """
        Update delivered quantity and add note if provided.
        
        Args:
            quantity: New delivered quantity
            note: Optional delivery note
        """
        if quantity < 0:
            raise ValueError("Delivered quantity cannot be negative")
        
        self.delivered_quantity = quantity
        
        if note:
            if self.notes:
                self.notes += f"\n[{datetime.utcnow().isoformat()}] {note}"
            else:
                self.notes = f"[{datetime.utcnow().isoformat()}] {note}"
        
        # Auto-update status based on delivery
        if self.summary_status == "Complete":
            self.status = "completed"
        elif self.is_overdue:
            self.status = "overdue"
        else:
            self.status = "in_progress"
        
        self.touch()