"""
Base model with common fields for all database models.

Provides timestamp mixins and soft delete patterns.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """
    Base model with common fields for all database entities.
    
    Provides:
    - Primary key field
    - Created and updated timestamps
    - Soft delete capability
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when record was last updated"
    )
    is_active: bool = Field(
        default=True,
        description="Soft delete flag - False means deleted"
    )
    
    def soft_delete(self) -> None:
        """
        Mark record as deleted using soft delete pattern.
        
        Sets is_active to False and updates timestamp.
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """
        Restore a soft-deleted record.
        
        Sets is_active to True and updates timestamp.
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def touch(self) -> None:
        """
        Update the updated_at timestamp without changing other fields.
        """
        self.updated_at = datetime.utcnow()


class TimestampMixin(SQLModel):
    """
    Mixin for models that only need timestamp fields.
    
    Use this for models that don't need primary key or soft delete.
    """
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when record was last updated"
    )