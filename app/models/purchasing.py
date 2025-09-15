"""
Purchasing department models.

Defines PurchaseOrder, PurchaseOrderItem, and Supplier models.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class Supplier(BaseModel, table=True):
    """
    Supplier master data model.
    
    Central repository for supplier information.
    """
    
    supplier_code: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="Unique supplier code"
    )
    supplier_name: str = Field(
        max_length=255,
        index=True,
        description="Supplier company name"
    )
    contact_person: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Primary contact person"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Supplier email address"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Supplier phone number"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Supplier address"
    )
    payment_terms: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Payment terms with supplier"
    )
    
    # ERPNext integration
    erpnext_supplier_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Corresponding ERPNext supplier ID"
    )
    
    # Relationships
    purchase_orders: list["PurchaseOrder"] = Relationship(back_populates="supplier")


class PurchaseOrder(BaseModel, table=True):
    """
    Purchase order model for procurement tracking.
    
    Manages orders placed with suppliers.
    """
    
    # Order identification
    po_number: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Purchase order number"
    )
    
    # Supplier information
    supplier_id: int = Field(
        foreign_key="supplier.id",
        description="Supplier for this order"
    )
    
    # Financial information
    total_amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total order amount"
    )
    
    # Status and dates
    status: str = Field(
        default="draft",
        max_length=50,
        description="Order status (draft, sent, confirmed, delivered, cancelled)"
    )
    order_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date order was placed"
    )
    expected_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Expected delivery date"
    )
    actual_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Actual delivery date"
    )
    
    # ERPNext integration
    erpnext_purchase_order_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Corresponding ERPNext purchase order ID"
    )
    
    # Notes
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Order notes and comments"
    )
    
    # Relationships
    supplier: Supplier = Relationship(back_populates="purchase_orders")
    items: list["PurchaseOrderItem"] = Relationship(
        back_populates="purchase_order",
        cascade_delete=True
    )
    
    @property
    def is_overdue(self) -> bool:
        """
        Check if order is overdue.
        
        Returns:
            bool: True if past expected delivery and not delivered
        """
        return (
            self.expected_delivery_date and
            datetime.utcnow() > self.expected_delivery_date and
            self.status not in ["delivered", "cancelled"]
        )
    
    @property
    def days_until_delivery(self) -> Optional[int]:
        """
        Calculate days until expected delivery.
        
        Returns:
            Optional[int]: Days remaining (negative if overdue)
        """
        if not self.expected_delivery_date:
            return None
        
        delta = self.expected_delivery_date - datetime.utcnow()
        return delta.days
    
    def calculate_total_amount(self) -> float:
        """
        Calculate total amount from line items.
        
        Returns:
            float: Sum of all line item totals
        """
        return sum(item.total_price or 0 for item in self.items)
    
    def update_total_amount(self) -> None:
        """Update total amount from line items."""
        self.total_amount = self.calculate_total_amount()
        self.touch()


class PurchaseOrderItem(BaseModel, table=True):
    """
    Purchase order line item model.
    
    Individual items within a purchase order.
    """
    
    # Links
    purchase_order_id: int = Field(
        foreign_key="purchaseorder.id",
        description="Parent purchase order"
    )
    product_id: int = Field(
        foreign_key="product.id",
        description="Product being purchased"
    )
    
    # Quantities and pricing
    quantity: int = Field(
        ge=0,
        description="Ordered quantity"
    )
    unit_price: float = Field(
        ge=0,
        description="Price per unit"
    )
    total_price: float = Field(
        ge=0,
        description="Total line amount (quantity * unit_price)"
    )
    received_quantity: int = Field(
        default=0,
        ge=0,
        description="Quantity received so far"
    )
    
    # Notes
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Line item notes"
    )
    
    # Relationships
    purchase_order: PurchaseOrder = Relationship(back_populates="items")
    product: "Product" = Relationship()
    
    @property
    def remaining_quantity(self) -> int:
        """
        Calculate remaining quantity to receive.
        
        Returns:
            int: Quantity still pending delivery
        """
        return max(0, self.quantity - self.received_quantity)
    
    @property
    def is_fully_received(self) -> bool:
        """
        Check if item is fully received.
        
        Returns:
            bool: True if received quantity meets or exceeds ordered
        """
        return self.received_quantity >= self.quantity
    
    @property
    def receipt_percentage(self) -> float:
        """
        Calculate receipt completion percentage.
        
        Returns:
            float: Percentage received (0.0 to 100.0+)
        """
        if self.quantity == 0:
            return 0.0
        return (self.received_quantity / self.quantity) * 100.0
    
    def update_received_quantity(self, new_quantity: int) -> None:
        """
        Update received quantity.
        
        Args:
            new_quantity: New received quantity
        """
        if new_quantity < 0:
            raise ValueError("Received quantity cannot be negative")
        
        self.received_quantity = new_quantity
        self.touch()
    
    def receive_quantity(self, additional_quantity: int) -> None:
        """
        Add to received quantity.
        
        Args:
            additional_quantity: Additional quantity received
        """
        if additional_quantity < 0:
            raise ValueError("Additional quantity cannot be negative")
        
        self.received_quantity += additional_quantity
        self.touch()