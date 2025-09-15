"""
User management models.

Defines User, Department, and Role models with authentication support.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from passlib.context import CryptContext
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DepartmentEnum(str, Enum):
    """Department enumeration for factory operations."""
    SALES = "sales"
    PRODUCTION = "production"
    PURCHASING = "purchasing"
    ADMIN = "admin"


class RoleEnum(str, Enum):
    """Role enumeration for permissions."""
    SALES_MANAGER = "sales_manager"
    SALES_STAFF = "sales_staff"
    PRODUCTION_MANAGER = "production_manager"
    PRODUCTION_STAFF = "production_staff"
    PURCHASING_MANAGER = "purchasing_manager"
    PURCHASING_STAFF = "purchasing_staff"
    SYSTEM_ADMIN = "system_admin"
    VIEWER = "viewer"


class Department(BaseModel, table=True):
    """
    Department model for organizing users.
    
    Represents different departments in the factory.
    """
    
    name: str = Field(max_length=100, unique=True, index=True)
    code: str = Field(max_length=10, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="department")
    roles: List["Role"] = Relationship(back_populates="department")


class Role(BaseModel, table=True):
    """
    Role model for permission management.
    
    Defines what actions users can perform within their department.
    """
    
    name: str = Field(max_length=100, index=True)
    code: str = Field(max_length=50, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    permissions_json: str = Field(
        default="{}",
        description="JSON string of permissions"
    )
    department_id: int = Field(foreign_key="department.id")
    
    # Relationships
    department: Department = Relationship(back_populates="roles")
    users: List["User"] = Relationship(back_populates="role")


class User(BaseModel, table=True):
    """
    User model with authentication and department assignment.
    
    Manages user accounts with role-based access control.
    """
    
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    full_name: str = Field(max_length=255)
    hashed_password: str = Field(max_length=255)
    
    # Department and role assignment
    department_id: int = Field(foreign_key="department.id")
    role_id: int = Field(foreign_key="role.id")
    
    # User status
    is_superuser: bool = Field(default=False)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    department: Department = Relationship(back_populates="users")
    role: Role = Relationship(back_populates="users")
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password is correct
        """
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """
        Set a new password for the user.
        
        Args:
            password: New plain text password
        """
        self.hashed_password = self.hash_password(password)
        self.touch()
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        self.touch()
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission: Permission string to check
            
        Returns:
            bool: True if user has permission
        """
        if self.is_superuser:
            return True
        
        # TODO: Implement permission checking logic
        # This would parse the role's permissions_json and check
        return False
    
    def can_access_department(self, department: str) -> bool:
        """
        Check if user can access a specific department's data.
        
        Args:
            department: Department code to check
            
        Returns:
            bool: True if user can access department
        """
        if self.is_superuser:
            return True
        
        # Admin users can access all departments
        if self.department.code == DepartmentEnum.ADMIN:
            return True
        
        # Users can access their own department
        return self.department.code == department