#!/usr/bin/env python3
"""
Bootstrap script to create admin user and basic data.
This runs after migrations to ensure the admin user exists.
"""

import asyncio
import asyncpg
from datetime import datetime
import json
import os

async def create_admin_user():
    """Create admin user and basic departments/roles if they don't exist."""
    
    # Database connection
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/factory_erp')
    # Convert SQLAlchemy URL format to asyncpg format
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Check if admin user already exists
        admin_exists = await conn.fetchval(
            "SELECT COUNT(*) FROM \"user\" WHERE username = $1", 
            "admin"
        )
        
        if admin_exists > 0:
            print("Admin user already exists, skipping bootstrap...")
            return
        
        print("Creating admin user and basic data...")
        current_time = datetime.utcnow()
        
        # Create departments if they don't exist
        dept_exists = await conn.fetchval("SELECT COUNT(*) FROM department WHERE code = $1", "admin")
        if dept_exists == 0:
            await conn.execute("""
                INSERT INTO department (created_at, updated_at, is_active, name, code, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (code) DO NOTHING
            """, current_time, current_time, True, 'Administration', 'admin', 'System administration and management')
            
            await conn.execute("""
                INSERT INTO department (created_at, updated_at, is_active, name, code, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (code) DO NOTHING
            """, current_time, current_time, True, 'Sales Department', 'sales', 'Customer requirements and sales management')
            
            print("Created departments")
        
        # Create admin role if it doesn't exist
        role_exists = await conn.fetchval("SELECT COUNT(*) FROM role WHERE code = $1", "system_admin")
        if role_exists == 0:
            admin_permissions = json.dumps({
                "can_create": True,
                "can_read": True,
                "can_update": True,
                "can_delete": True,
                "can_access_all_departments": True,
                "can_manage_users": True,
                "can_manage_system": True
            })
            
            # Get admin department ID
            dept_id = await conn.fetchval("SELECT id FROM department WHERE code = $1", "admin")
            
            await conn.execute("""
                INSERT INTO role (created_at, updated_at, is_active, name, code, description, permissions_json, department_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (code) DO NOTHING
            """, current_time, current_time, True, 'System Administrator', 'system_admin', 'Full system access and administration', admin_permissions, dept_id)
            
            print("Created admin role")
        
        # Create admin user
        # Password: "admin123" - hashed with bcrypt
        admin_password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdGSGlY8LpqNe"
        
        dept_id = await conn.fetchval("SELECT id FROM department WHERE code = $1", "admin")
        role_id = await conn.fetchval("SELECT id FROM role WHERE code = $1", "system_admin")
        
        await conn.execute("""
            INSERT INTO "user" (created_at, updated_at, is_active, username, email, full_name, hashed_password, department_id, role_id, is_superuser, last_login)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (username) DO NOTHING
        """, current_time, current_time, True, 'admin', 'admin@factory-erp.com', 'System Administrator', admin_password_hash, dept_id, role_id, True, None)
        
        print("Created admin user: username=admin, password=admin123")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())