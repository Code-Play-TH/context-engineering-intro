"""Seed initial data

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-14 10:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
import json

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert seed data for departments, roles, and admin user."""
    
    # Define table structures for inserts
    department_table = table('department',
        column('id', sa.Integer),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime),
        column('is_active', sa.Boolean),
        column('name', sa.String),
        column('code', sa.String),
        column('description', sa.String)
    )
    
    role_table = table('role',
        column('id', sa.Integer),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime),
        column('is_active', sa.Boolean),
        column('name', sa.String),
        column('code', sa.String),
        column('description', sa.String),
        column('permissions_json', sa.String),
        column('department_id', sa.Integer)
    )
    
    user_table = table('user',
        column('id', sa.Integer),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime),
        column('is_active', sa.Boolean),
        column('username', sa.String),
        column('email', sa.String),
        column('full_name', sa.String),
        column('hashed_password', sa.String),
        column('department_id', sa.Integer),
        column('role_id', sa.Integer),
        column('is_superuser', sa.Boolean),
        column('last_login', sa.DateTime)
    )
    
    current_time = datetime.utcnow()
    
    # Insert departments
    op.bulk_insert(department_table, [
        {
            'id': 1,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Administration',
            'code': 'admin',
            'description': 'System administration and management'
        },
        {
            'id': 2,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Sales Department',
            'code': 'sales',
            'description': 'Customer requirements and sales management'
        },
        {
            'id': 3,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Production Department',
            'code': 'production',
            'description': 'Manufacturing and production operations'
        },
        {
            'id': 4,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Purchasing Department',
            'code': 'purchasing',
            'description': 'Procurement and supplier management'
        }
    ])
    
    # Insert roles
    admin_permissions = json.dumps({
        "can_create": True,
        "can_read": True,
        "can_update": True,
        "can_delete": True,
        "can_access_all_departments": True,
        "can_manage_users": True,
        "can_manage_system": True
    })
    
    manager_permissions = json.dumps({
        "can_create": True,
        "can_read": True,
        "can_update": True,
        "can_delete": False,
        "can_access_all_departments": False,
        "can_manage_users": False,
        "can_manage_system": False
    })
    
    staff_permissions = json.dumps({
        "can_create": True,
        "can_read": True,
        "can_update": True,
        "can_delete": False,
        "can_access_all_departments": False,
        "can_manage_users": False,
        "can_manage_system": False
    })
    
    viewer_permissions = json.dumps({
        "can_create": False,
        "can_read": True,
        "can_update": False,
        "can_delete": False,
        "can_access_all_departments": False,
        "can_manage_users": False,
        "can_manage_system": False
    })
    
    op.bulk_insert(role_table, [
        # Admin roles
        {
            'id': 1,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'System Administrator',
            'code': 'system_admin',
            'description': 'Full system access and administration',
            'permissions_json': admin_permissions,
            'department_id': 1
        },
        # Sales roles
        {
            'id': 2,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Sales Manager',
            'code': 'sales_manager',
            'description': 'Sales department management',
            'permissions_json': manager_permissions,
            'department_id': 2
        },
        {
            'id': 3,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Sales Staff',
            'code': 'sales_staff',
            'description': 'Sales operations staff',
            'permissions_json': staff_permissions,
            'department_id': 2
        },
        # Production roles
        {
            'id': 4,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Production Manager',
            'code': 'production_manager',
            'description': 'Production department management',
            'permissions_json': manager_permissions,
            'department_id': 3
        },
        {
            'id': 5,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Production Staff',
            'code': 'production_staff',
            'description': 'Production operations staff',
            'permissions_json': staff_permissions,
            'department_id': 3
        },
        # Purchasing roles
        {
            'id': 6,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Purchasing Manager',
            'code': 'purchasing_manager',
            'description': 'Purchasing department management',
            'permissions_json': manager_permissions,
            'department_id': 4
        },
        {
            'id': 7,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Purchasing Staff',
            'code': 'purchasing_staff',
            'description': 'Purchasing operations staff',
            'permissions_json': staff_permissions,
            'department_id': 4
        },
        # Viewer role for all departments
        {
            'id': 8,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'name': 'Viewer',
            'code': 'viewer',
            'description': 'Read-only access',
            'permissions_json': viewer_permissions,
            'department_id': 1
        }
    ])
    
    # Insert default admin user
    # Password: "admin123" - hashed with bcrypt
    admin_password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdGSGlY8LpqNe"
    
    op.bulk_insert(user_table, [
        {
            'id': 1,
            'created_at': current_time,
            'updated_at': current_time,
            'is_active': True,
            'username': 'admin',
            'email': 'admin@factory-erp.com',
            'full_name': 'System Administrator',
            'hashed_password': admin_password_hash,
            'department_id': 1,
            'role_id': 1,
            'is_superuser': True,
            'last_login': None
        }
    ])


def downgrade() -> None:
    """Remove seed data."""
    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM user WHERE id = 1")
    op.execute("DELETE FROM role WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8)")
    op.execute("DELETE FROM department WHERE id IN (1, 2, 3, 4)")