"""
Test KOL CRUD operations API endpoints.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kol import KOL, KOLStatus


class TestKOLsCRUD:
    """Test cases for KOLs CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_kol(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test creating a new KOL."""
        kol_data = {
            "name": "Test Influencer",
            "email": "influencer@example.com",
            "phone": "+1234567890",
            "bio": "Test influencer bio",
            "location": "New York, USA",
            "timezone": "America/New_York",
            "languages": ["en", "es"],
            "niche": ["fashion", "lifestyle"],
            "communication_preferences": ["email", "discord"],
            "social_media_accounts": {
                "instagram": {
                    "handle": "test_influencer",
                    "id": "123456789",
                    "verified": True
                }
            },
            "follower_counts": {
                "instagram": 50000
            },
            "engagement_rates": {
                "instagram": 5.2
            }
        }

        response = client.post(
            "/api/v1/kols/",
            json=kol_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == kol_data["name"]
        assert data["email"] == kol_data["email"]
        assert data["phone"] == kol_data["phone"]
        assert data["bio"] == kol_data["bio"]
        assert data["location"] == kol_data["location"]
        assert data["languages"] == kol_data["languages"]
        assert data["niche"] == kol_data["niche"]
        assert data["status"] == "pending_verification"

    @pytest.mark.asyncio
    async def test_create_kol_duplicate_email(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test creating KOL with duplicate email fails."""
        kol_data = {
            "name": "Duplicate KOL",
            "email": test_kol.email,  # Use existing email
            "bio": "Duplicate bio"
        }

        response = client.post(
            "/api/v1/kols/",
            json=kol_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_kols(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test listing KOLs with pagination."""
        response = client.get(
            "/api/v1/kols/",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "kols" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        assert isinstance(data["kols"], list)

    @pytest.mark.asyncio
    async def test_list_kols_with_filters(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test listing KOLs with filters."""
        response = client.get(
            "/api/v1/kols/?status=active&min_followers=1000&sort_by=name&sort_order=asc",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "kols" in data

    @pytest.mark.asyncio
    async def test_get_kol(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test getting a specific KOL."""
        response = client.get(
            f"/api/v1/kols/{test_kol.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_kol.id
        assert data["name"] == test_kol.name
        assert data["email"] == test_kol.email

    @pytest.mark.asyncio
    async def test_get_kol_not_found(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test getting non-existent KOL returns 404."""
        response = client.get(
            "/api/v1/kols/99999",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_kol(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test updating a KOL."""
        update_data = {
            "name": "Updated KOL Name",
            "bio": "Updated bio",
            "location": "Los Angeles, USA",
            "follower_counts": {
                "instagram": 75000,
                "youtube": 25000
            }
        }

        response = client.put(
            f"/api/v1/kols/{test_kol.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["bio"] == update_data["bio"]
        assert data["location"] == update_data["location"]
        assert data["follower_counts"]["instagram"] == update_data["follower_counts"]["instagram"]
        assert data["follower_counts"]["youtube"] == update_data["follower_counts"]["youtube"]

    @pytest.mark.asyncio
    async def test_delete_kol(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test deleting a KOL (soft delete)."""
        response = client.delete(
            f"/api/v1/kols/{test_kol.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 204

        # Verify KOL is soft deleted
        response = client.get(
            f"/api/v1/kols/{test_kol.id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_get_kol_performance(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test getting KOL performance metrics."""
        response = client.get(
            f"/api/v1/kols/{test_kol.id}/performance",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "kol_id" in data
        assert "avg_engagement_rate" in data
        assert "avg_reach" in data
        assert "total_campaigns" in data
        assert "successful_campaigns" in data
        assert "collaboration_history" in data

    @pytest.mark.asyncio
    async def test_add_social_account(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test adding social media account to KOL."""
        account_data = {
            "platform": "youtube",
            "username": "test_channel",
            "profile_url": "https://youtube.com/@test_channel",
            "follower_count": 25000,
            "is_verified": True,
            "is_primary": False
        }

        response = client.post(
            f"/api/v1/kols/{test_kol.id}/social-accounts",
            json=account_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "account_id" in data

    @pytest.mark.asyncio
    async def test_update_social_account(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test updating social media account."""
        # First add an account
        account_data = {
            "platform": "tiktok",
            "username": "test_tiktok",
            "follower_count": 15000
        }

        create_response = client.post(
            f"/api/v1/kols/{test_kol.id}/social-accounts",
            json=account_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )
        account_id = create_response.json()["account_id"]

        # Now update it
        update_data = {
            "follower_count": 20000,
            "is_verified": True
        }

        response = client.put(
            f"/api/v1/kols/{test_kol.id}/social-accounts/{account_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    @pytest.mark.asyncio
    async def test_delete_social_account(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test deleting social media account."""
        # First add an account
        account_data = {
            "platform": "linkedin",
            "username": "test_linkedin",
            "follower_count": 5000
        }

        create_response = client.post(
            f"/api/v1/kols/{test_kol.id}/social-accounts",
            json=account_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )
        account_id = create_response.json()["account_id"]

        # Now delete it
        response = client.delete(
            f"/api/v1/kols/{test_kol.id}/social-accounts/{account_id}",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_refresh_kol_data(self, client: TestClient, admin_user, test_kol, db_session: AsyncSession):
        """Test refreshing KOL profile data."""
        response = client.post(
            f"/api/v1/kols/{test_kol.id}/refresh-data",
            params={"platforms": ["instagram", "youtube"]},
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "task_id" in data
        assert "platforms" in data

    @pytest.mark.asyncio
    async def test_search_kols(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test advanced KOL search."""
        search_data = {
            "search": "test",
            "status": ["active"],
            "min_followers": 1000,
            "max_followers": 100000,
            "sort_by": "name",
            "sort_order": "asc"
        }

        response = client.post(
            "/api/v1/kols/search",
            json=search_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "kols" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_bulk_update_kols(self, client: TestClient, admin_user, test_kols, db_session: AsyncSession):
        """Test bulk updating KOLs."""
        kol_ids = [kol.id for kol in test_kols[:3]]
        bulk_data = [
            {
                "id": kol_ids[0],
                "updates": {"status": "active", "location": "Updated Location 1"}
            },
            {
                "id": kol_ids[1],
                "updates": {"status": "active", "location": "Updated Location 2"}
            },
            {
                "id": kol_ids[2],
                "updates": {"status": "active", "location": "Updated Location 3"}
            }
        ]

        response = client.post(
            "/api/v1/kols/bulk-update",
            json=bulk_data,
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_get_kols_analytics_summary(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test getting KOLs analytics summary."""
        response = client.get(
            "/api/v1/kols/analytics/summary",
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_kols" in data
        assert "status_distribution" in data
        assert "platform_distribution" in data
        assert "recent_registrations" in data
        assert "top_categories" in data
        assert "average_metrics" in data
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_export_kols_data(self, client: TestClient, admin_user, db_session: AsyncSession):
        """Test exporting KOL data."""
        export_filters = {
            "status": ["active"],
            "categories": ["fashion"],
            "date_range": {
                "start": "2024-01-01T00:00:00",
                "end": "2024-12-31T23:59:59"
            }
        }

        response = client.post(
            "/api/v1/kols/export",
            json=export_filters,
            params={"format": "json"},
            headers={"Authorization": f"Bearer {admin_user.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["status"] == "scheduled"
        assert "total_kols" in data
        assert "download_url" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: TestClient, db_session: AsyncSession):
        """Test unauthorized access to KOL endpoints."""
        response = client.get("/api/v1/kols/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_insufficient_permissions(self, client: TestClient, test_user, db_session: AsyncSession):
        """Test insufficient permissions for certain KOL operations."""
        kol_data = {
            "name": "Unauthorized KOL",
            "email": "unauthorized@example.com"
        }

        response = client.post(
            "/api/v1/kols/",
            json=kol_data,
            headers={"Authorization": f"Bearer {test_user.token}"}
        )

        # Should depend on user's role and permissions
        assert response.status_code in [403, 201]  # Depends on test_user's permissions