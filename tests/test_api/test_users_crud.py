"""
Test User CRUD operations API endpoints.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, UserStatus
from app.schemas.users import UserCreate, UserUpdate


class TestUsersCRUD:
    """Test cases for Users CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test creating a new user."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "SecurePassword123!",
            "role": "viewer",
            "status": "active"
        }

        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert data["role"] == user_data["role"]
        assert data["status"] == user_data["status"]
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test creating user with duplicate email fails."""
        user_data = {
            "email": admin_user.email,  # Use existing email
            "username": "duplicate",
            "first_name": "Duplicate",
            "last_name": "User",
            "password": "SecurePassword123!"
        }

        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_users(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test listing users with pagination."""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        assert isinstance(data["users"], list)

    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test listing users with filters."""
        response = client.get(
            "/api/v1/users/?status=active&role=admin&sort_by=email&sort_order=asc",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    @pytest.mark.asyncio
    async def test_get_user(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test getting a specific user."""
        response = client.get(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user.id
        assert data["email"] == admin_user.email
        assert "recent_sessions" in data
        assert "recent_audit_logs" in data

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test getting non-existent user returns 404."""
        response = client.get(
            "/api/v1/users/99999",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user(self, client: TestClient, admin_user, test_user, db_session: AsyncSession):
        """Test updating a user."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio"
        }

        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["bio"] == update_data["bio"]

    @pytest.mark.asyncio
    async def test_update_user_self(self, client: TestClient, test_user, db_session: AsyncSession):
        """Test user updating their own profile."""
        update_data = {
            "bio": "Self updated bio",
            "timezone": "America/New_York"
        }

        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == update_data["bio"]
        assert data["timezone"] == update_data["timezone"]

    @pytest.mark.asyncio
    async def test_update_user_email_duplicate(self, client: TestClient, admin_user, test_user, db_session: AsyncSession):
        """Test updating user with duplicate email fails."""
        update_data = {
            "email": admin_user.email  # Try to use admin's email
        }

        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user(self, client: TestClient, admin_user, test_user, db_session: AsyncSession):
        """Test deleting a user (soft delete)."""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 204

        # Verify user is soft deleted (deactivated)
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
        assert data["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_delete_user_self_forbidden(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test admin cannot delete their own account."""
        response = client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 400
        assert "own account" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_status(self, client: TestClient, admin_user, test_user, db_session: AsyncSession):
        """Test updating user status."""
        status_data = {
            "status": "suspended",
            "is_active": False,
            "reason": "Test suspension"
        }

        response = client.patch(
            f"/api/v1/users/{test_user.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == status_data["status"]
        assert data["is_active"] == status_data["is_active"]

    @pytest.mark.asyncio
    async def test_update_user_role(self, client: TestClient, admin_user, test_user, db_session: AsyncSession):
        """Test updating user role."""
        role_data = {
            "role": "manager",
            "permissions": ["manage_campaigns", "view_analytics"],
            "reason": "Promotion to manager"
        }

        response = client.patch(
            f"/api/v1/users/{test_user.id}/role",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == role_data["role"]
        assert set(data["permissions"]) == set(role_data["permissions"])

    @pytest.mark.asyncio
    async def test_bulk_user_action(self, client: TestClient, admin_user, test_users, db_session: AsyncSession):
        """Test bulk user actions."""
        user_ids = [user.id for user in test_users[:3]]
        bulk_data = {
            "user_ids": user_ids,
            "action": "deactivate",
            "reason": "Bulk deactivation test"
        }

        response = client.post(
            "/api/v1/users/bulk-action",
            json=bulk_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == len(user_ids)
        assert data["failed_count"] == 0
        assert set(data["updated_users"]) == set(user_ids)

    @pytest.mark.asyncio
    async def test_get_user_analytics(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test getting user analytics."""
        response = client.get(
            "/api/v1/users/analytics/summary",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "verified_users" in data
        assert "status_distribution" in data
        assert "role_distribution" in data
        assert "recent_registrations" in data
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_user(self, client: TestClient, test_user, db_session: AsyncSession):
        """Test non-admin user cannot create other users."""
        user_data = {
            "email": "restricted@example.com",
            "first_name": "Restricted",
            "last_name": "User"
        }

        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {test_user.token}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_view_all_users(self, client: TestClient, test_user, db_session: AsyncSession):
        """Test non-admin user cannot list all users."""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {test_user.token}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_user_can_view_own_profile(self, client: TestClient, test_user, db_session: AsyncSession):
        """Test user can view their own profile."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {test_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        # Non-admin should not see audit logs
        assert len(data["recent_audit_logs"]) == 0

    @pytest.mark.asyncio
    async def test_user_cannot_update_role(self, client: TestClient, test_user, db_session: AsyncSession):
        """Test user cannot update their own role."""
        update_data = {
            "role": "admin"  # Try to escalate privileges
        }

        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user.token}"}
        )

        # Should succeed but role should not be changed
        assert response.status_code == 200
        data = response.json()
        assert data["role"] != "admin"  # Role should remain unchanged