"""
Database models for the Factory ERP system.

This package contains all SQLModel definitions for the application.
"""

# Import all models to ensure they're registered with SQLModel
from app.models.base import BaseModel  # noqa
from app.models.user import User, Department, Role  # noqa
from app.models.product import Product, ProductionStep  # noqa
from app.models.sales import CustomerRequirement, Customer  # noqa
from app.models.production import ProductionOrder, ProductionTracking  # noqa
from app.models.purchasing import PurchaseOrder, PurchaseOrderItem, Supplier  # noqa
from app.models.audit import AuditLog, ERPNextSyncLog, ExcelOperation  # noqa

__all__ = [
    "BaseModel",
    "User",
    "Department", 
    "Role",
    "Product",
    "ProductionStep",
    "CustomerRequirement",
    "Customer",
    "ProductionOrder",
    "ProductionTracking",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "Supplier",
    "AuditLog",
    "ERPNextSyncLog",
    "ExcelOperation",
]