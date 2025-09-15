"""
Tests for user-related models.

Tests User, Department, and Role models including relationships and validation.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Department, Role
from app.core.security import get_password_hash, verify_password


class TestDepartment:
    """Test cases for Department model."""
    
    @pytest.mark.asyncio
    async def test_create_department(self, test_db: AsyncSession):
        """Test creating a department."""
        department = Department(
            name="Engineering",
            description="Engineering Department"
        )
        
        test_db.add(department)
        await test_db.commit()
        await test_db.refresh(department)
        
        assert department.id is not None
        assert department.name == "Engineering"
        assert department.description == "Engineering Department"
        assert department.is_active is True
        assert isinstance(department.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_department_unique_name(self, test_db: AsyncSession):
        """Test that department names must be unique."""
        dept1 = Department(name="Test Dept", description="First")
        dept2 = Department(name="Test Dept", description="Second")
        
        test_db.add(dept1)
        await test_db.commit()
        
        test_db.add(dept2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()
    
    @pytest.mark.asyncio
    async def test_department_soft_delete(self, test_db: AsyncSession):
        """Test soft delete functionality."""
        department = Department(name="To Delete", description="Will be deleted")
        
        test_db.add(department)
        await test_db.commit()
        await test_db.refresh(department)
        
        # Soft delete
        department.soft_delete()
        await test_db.commit()
        
        assert department.is_active is False
        assert department.deleted_at is not None


class TestRole:
    """Test cases for Role model."""
    
    @pytest.mark.asyncio
    async def test_create_role(self, test_db: AsyncSession):
        """Test creating a role."""
        permissions = {
            "users": ["read", "create"],
            "products": ["read"]
        }
        
        role = Role(
            name="Test Role",
            description="A test role",
            permissions=permissions
        )
        
        test_db.add(role)
        await test_db.commit()
        await test_db.refresh(role)
        
        assert role.id is not None
        assert role.name == "Test Role"
        assert role.permissions == permissions
        assert role.is_active is True
    
    @pytest.mark.asyncio
    async def test_role_has_permission(self, test_db: AsyncSession):
        """Test permission checking."""
        permissions = {
            "users": ["read", "create", "update"],
            "products": ["read"]
        }
        
        role = Role(
            name="Test Role",
            permissions=permissions
        )
        
        # Test existing permissions
        assert role.has_permission("users", "read")
        assert role.has_permission("users", "create")
        assert role.has_permission("products", "read")
        
        # Test non-existing permissions
        assert not role.has_permission("users", "delete")
        assert not role.has_permission("orders", "read")
        assert not role.has_permission("products", "create")
    
    @pytest.mark.asyncio
    async def test_role_unique_name(self, test_db: AsyncSession):
        """Test that role names must be unique."""
        role1 = Role(name="Duplicate", description="First")
        role2 = Role(name="Duplicate", description="Second")
        
        test_db.add(role1)
        await test_db.commit()
        
        test_db.add(role2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()


class TestUser:
    """Test cases for User model."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db: AsyncSession, test_departments: list[Department], test_roles: list[Role]):
        """Test creating a user."""
        department = test_departments[0]
        role = test_roles[0]
        
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert verify_password("password123", user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_user_unique_username(self, test_db: AsyncSession, test_departments: list[Department], test_roles: list[Role]):
        """Test that usernames must be unique."""
        department = test_departments[0]
        role = test_roles[0]
        
        user1 = User(
            username="duplicate",
            email="user1@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        user2 = User(
            username="duplicate",
            email="user2@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        test_db.add(user1)
        await test_db.commit()
        
        test_db.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()
    
    @pytest.mark.asyncio
    async def test_user_unique_email(self, test_db: AsyncSession, test_departments: list[Department], test_roles: list[Role]):
        """Test that emails must be unique."""
        department = test_departments[0]
        role = test_roles[0]
        
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        user2 = User(
            username="user2",
            email="duplicate@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        test_db.add(user1)
        await test_db.commit()
        
        test_db.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()
    
    @pytest.mark.asyncio
    async def test_user_full_name(self, test_db: AsyncSession, test_departments: list[Department], test_roles: list[Role]):
        """Test full name property."""
        department = test_departments[0]
        role = test_roles[0]
        
        # Test with both first and last name
        user1 = User(
            username="user1",
            email="user1@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        assert user1.full_name == "John Doe"
        
        # Test with only first name
        user2 = User(
            username="user2",
            email="user2@example.com",
            first_name="Jane",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        assert user2.full_name == "Jane"
        
        # Test with no names
        user3 = User(
            username="user3",
            email="user3@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        assert user3.full_name == "user3"
    
    @pytest.mark.asyncio
    async def test_user_last_login_update(self, test_db: AsyncSession, test_departments: list[Department], test_roles: list[Role]):
        """Test updating last login time."""
        department = test_departments[0]
        role = test_roles[0]
        
        user = User(
            username="logintest",
            email="login@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Initially no last login
        assert user.last_login is None
        
        # Update last login
        user.update_last_login()
        await test_db.commit()
        
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
    
    @pytest.mark.asyncio
    async def test_user_touch_functionality(self, test_db: AsyncSession, test_departments: list[Department], test_roles: list[Role]):
        """Test touch functionality updates timestamp."""
        department = test_departments[0]
        role = test_roles[0]
        
        user = User(
            username="touchtest",
            email="touch@example.com",
            hashed_password=get_password_hash("password123"),
            department_id=department.id,
            role_id=role.id
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Wait a bit and touch
        import asyncio
        await asyncio.sleep(0.01)
        
        user.touch()
        await test_db.commit()
        
        assert user.updated_at > original_updated_at