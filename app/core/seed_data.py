"""
Seed data initialization for the Factory ERP system.

Creates initial departments, roles, and users for system setup.
"""

import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.user import User, Department, Role, DepartmentEnum, RoleEnum
from app.core.security import get_password_hash


async def create_seed_data() -> None:
    """
    Create initial seed data for the Factory ERP system.
    
    Creates default departments, roles, and an admin user.
    """
    async for session in get_session():
        try:
            await _create_departments(session)
            await _create_roles(session)
            await _create_admin_user(session)
            await session.commit()
            print("Seed data created successfully")
        except Exception as e:
            await session.rollback()
            print(f"Error creating seed data: {e}")
            raise
        finally:
            await session.close()


async def _create_departments(session: AsyncSession) -> None:
    """Create default departments."""
    departments_data = [
        {
            "name": "Sales Department",
            "code": "SALES",
            "description": "Manages customer relationships and sales processes"
        },
        {
            "name": "Production Department", 
            "code": "PROD",
            "description": "Handles manufacturing and production operations"
        },
        {
            "name": "Purchasing Department",
            "code": "PURCH", 
            "description": "Manages supplier relationships and procurement"
        },
        {
            "name": "Administration",
            "code": "ADMIN",
            "description": "System administration and general management"
        }
    ]
    
    for dept_data in departments_data:
        # Check if department already exists
        result = await session.execute(
            select(Department).where(Department.code == dept_data["code"])
        )
        existing_dept = result.scalar_one_or_none()
        
        if not existing_dept:
            department = Department(**dept_data)
            session.add(department)
            print(f"Created department: {dept_data['name']}")


async def _create_roles(session: AsyncSession) -> None:
    """Create default roles for each department."""
    # Get departments for foreign key relationships
    departments = {}
    result = await session.execute(select(Department))
    for dept in result.scalars().all():
        departments[dept.code] = dept
    
    roles_data = [
        # Sales Department Roles
        {
            "name": "Sales Manager",
            "code": "SALES_MGR",
            "description": "Manages sales team and processes",
            "department_code": "SALES",
            "permissions": {
                "sales": {"read": True, "write": True, "delete": True, "manage": True},
                "customers": {"read": True, "write": True, "delete": True},
                "reports": {"sales": True}
            }
        },
        {
            "name": "Sales Staff",
            "code": "SALES_STAFF", 
            "description": "Handles customer orders and inquiries",
            "department_code": "SALES",
            "permissions": {
                "sales": {"read": True, "write": True, "delete": False},
                "customers": {"read": True, "write": True, "delete": False}
            }
        },
        
        # Production Department Roles
        {
            "name": "Production Manager",
            "code": "PROD_MGR",
            "description": "Manages production operations and staff",
            "department_code": "PROD", 
            "permissions": {
                "production": {"read": True, "write": True, "delete": True, "manage": True},
                "products": {"read": True, "write": True, "delete": False},
                "reports": {"production": True}
            }
        },
        {
            "name": "Production Staff",
            "code": "PROD_STAFF",
            "description": "Executes production tasks and tracking", 
            "department_code": "PROD",
            "permissions": {
                "production": {"read": True, "write": True, "delete": False},
                "products": {"read": True, "write": False, "delete": False}
            }
        },
        
        # Purchasing Department Roles
        {
            "name": "Purchasing Manager", 
            "code": "PURCH_MGR",
            "description": "Manages procurement and supplier relationships",
            "department_code": "PURCH",
            "permissions": {
                "purchasing": {"read": True, "write": True, "delete": True, "manage": True},
                "suppliers": {"read": True, "write": True, "delete": True},
                "reports": {"purchasing": True}
            }
        },
        {
            "name": "Purchasing Staff",
            "code": "PURCH_STAFF",
            "description": "Handles purchase orders and supplier communications",
            "department_code": "PURCH", 
            "permissions": {
                "purchasing": {"read": True, "write": True, "delete": False},
                "suppliers": {"read": True, "write": True, "delete": False}
            }
        },
        
        # Administration Roles
        {
            "name": "System Administrator",
            "code": "SYS_ADMIN",
            "description": "Full system access and administration", 
            "department_code": "ADMIN",
            "permissions": {
                "system": {"read": True, "write": True, "delete": True, "manage": True},
                "users": {"read": True, "write": True, "delete": True, "manage": True},
                "departments": {"read": True, "write": True, "delete": True, "manage": True},
                "roles": {"read": True, "write": True, "delete": True, "manage": True},
                "reports": {"all": True}
            }
        },
        {
            "name": "Viewer",
            "code": "VIEWER", 
            "description": "Read-only access to system data",
            "department_code": "ADMIN",
            "permissions": {
                "sales": {"read": True},
                "production": {"read": True}, 
                "purchasing": {"read": True},
                "products": {"read": True}
            }
        }
    ]
    
    for role_data in roles_data:
        # Check if role already exists
        result = await session.execute(
            select(Role).where(Role.code == role_data["code"])
        )
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            dept_code = role_data.pop("department_code")
            department = departments[dept_code]
            
            permissions = role_data.pop("permissions")
            role_data["permissions_json"] = json.dumps(permissions)
            role_data["department_id"] = department.id
            
            role = Role(**role_data)
            session.add(role)
            print(f"Created role: {role_data['name']}")


async def _create_admin_user(session: AsyncSession) -> None:
    """Create default admin user."""
    # Check if admin user already exists
    result = await session.execute(
        select(User).where(User.username == "admin")
    )
    existing_user = result.scalar_one_or_none()
    
    if not existing_user:
        # Get admin department and system admin role
        admin_dept_result = await session.execute(
            select(Department).where(Department.code == "ADMIN")
        )
        admin_dept = admin_dept_result.scalar_one_or_none()
        
        admin_role_result = await session.execute(
            select(Role).where(Role.code == "SYS_ADMIN")
        )
        admin_role = admin_role_result.scalar_one_or_none()
        
        if admin_dept and admin_role:
            admin_user = User(
                username="admin",
                email="admin@factory-erp.local",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),  # Change in production!
                department_id=admin_dept.id,
                role_id=admin_role.id,
                is_superuser=True
            )
            
            session.add(admin_user)
            print("Created admin user (username: admin, password: admin123)")
            print("WARNING: Change the admin password in production!")
        else:
            print("Could not create admin user - missing department or role")