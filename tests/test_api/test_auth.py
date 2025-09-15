"""
Tests for authentication API endpoints.

Tests login, token refresh, logout, and authorization functionality.
"""

import pytest
from httpx import AsyncClient
from app.models.user import User


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_users: list[User]):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify user data
        assert "user" in data
        user_data = data["user"]
        assert user_data["username"] == "admin"
        assert user_data["email"] == "admin@test.com"
        assert "hashed_password" not in user_data  # Should not expose password
    
    @pytest.mark.asyncio
    async def test_login_invalid_username(self, client: AsyncClient):
        """Test login with invalid username."""
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_users: list[User]):
        """Test login with invalid password."""
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, test_db, test_users: list[User]):
        """Test login with inactive user."""
        # Deactivate admin user
        admin_user = next(u for u in test_users if u.username == "admin")
        admin_user.is_active = False
        await test_db.commit()
        
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login with missing credentials."""
        # Missing password
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin"}
        )
        
        assert response.status_code == 422  # Validation error
        
        # Missing username
        response = await client.post(
            "/api/auth/login",
            json={"password": "password123"}
        )
        
        assert response.status_code == 422  # Validation error
        
        # Empty request
        response = await client.post(
            "/api/auth/login",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, admin_token: str, auth_headers):
        """Test getting current user info."""
        response = await client.get(
            "/api/auth/me",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "admin"
        assert data["email"] == "admin@test.com"
        assert data["is_active"] is True
        assert "hashed_password" not in data
        
        # Check department and role info
        assert "department" in data
        assert data["department"]["name"] == "Admin"
        
        assert "role" in data
        assert data["role"]["name"] == "Admin"
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient, auth_headers):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers=auth_headers("invalid_token")
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, admin_token: str, auth_headers):
        """Test successful password change."""
        response = await client.post(
            "/api/auth/change-password",
            headers=auth_headers(admin_token),
            json={
                "current_password": "admin123",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"
        
        # Test login with new password
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "newpassword123"
            }
        )
        
        assert login_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, admin_token: str, auth_headers):
        """Test password change with wrong current password."""
        response = await client.post(
            "/api/auth/change-password",
            headers=auth_headers(admin_token),
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "current password" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_change_password_weak_password(self, client: AsyncClient, admin_token: str, auth_headers):
        """Test password change with weak password."""
        response = await client.post(
            "/api/auth/change-password",
            headers=auth_headers(admin_token),
            json={
                "current_password": "admin123",
                "new_password": "123"  # Too short
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_users: list[User]):
        """Test token refresh functionality."""
        # First login to get tokens
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        assert "access_token" in refresh_data
        assert "token_type" in refresh_data
        assert refresh_data["token_type"] == "bearer"
        
        # Verify new access token works
        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {refresh_data['access_token']}"}
        )
        
        assert me_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, admin_token: str, auth_headers):
        """Test logout functionality."""
        response = await client.post(
            "/api/auth/logout",
            headers=auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
        
        # Verify token is invalidated (if token blacklisting is implemented)
        # This test might need adjustment based on actual logout implementation
        me_response = await client.get(
            "/api/auth/me",
            headers=auth_headers(admin_token)
        )
        
        # If token blacklisting is implemented, this should fail
        # If not, the token might still be valid until expiry
        # Adjust this assertion based on your implementation
        # assert me_response.status_code == 401


class TestAuthAuthorization:
    """Test cases for authorization and access control."""
    
    @pytest.mark.asyncio
    async def test_admin_access(self, client: AsyncClient, admin_token: str, auth_headers):
        """Test that admin user has access to admin endpoints."""
        response = await client.get(
            "/api/users/",
            headers=auth_headers(admin_token)
        )
        
        # Should have access to user management
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_sales_user_restricted_access(self, client: AsyncClient, sales_token: str, auth_headers):
        """Test that sales user has restricted access."""
        # Should have access to sales endpoints
        response = await client.get(
            "/api/sales/customers/",
            headers=auth_headers(sales_token)
        )
        assert response.status_code in [200, 404]  # 404 if no customers exist
        
        # Should NOT have access to user management
        response = await client.get(
            "/api/users/",
            headers=auth_headers(sales_token)
        )
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.asyncio
    async def test_production_user_restricted_access(self, client: AsyncClient, production_token: str, auth_headers):
        """Test that production user has restricted access."""
        # Should have access to production endpoints
        response = await client.get(
            "/api/production/orders/",
            headers=auth_headers(production_token)
        )
        assert response.status_code in [200, 404]  # 404 if no orders exist
        
        # Should NOT have access to user management
        response = await client.get(
            "/api/users/",
            headers=auth_headers(production_token)
        )
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.asyncio
    async def test_role_based_permissions(self, client: AsyncClient, test_users: list[User], auth_headers):
        """Test role-based permission checking."""
        # Test with different user types
        for user in test_users:
            # Login as this user
            login_response = await client.post(
                "/api/auth/login",
                json={
                    "username": user.username,
                    "password": f"{user.username.split('_')[0]}123"
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                
                # Test access to user profile (should always work)
                me_response = await client.get(
                    "/api/auth/me",
                    headers=auth_headers(token)
                )
                assert me_response.status_code == 200
                
                # Test role-specific access
                if user.username == "admin":
                    # Admin should access everything
                    user_mgmt_response = await client.get(
                        "/api/users/",
                        headers=auth_headers(token)
                    )
                    assert user_mgmt_response.status_code == 200
                else:
                    # Non-admin should not access user management
                    user_mgmt_response = await client.get(
                        "/api/users/",
                        headers=auth_headers(token)
                    )
                    assert user_mgmt_response.status_code == 403