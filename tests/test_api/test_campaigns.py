"""
Tests for Campaign API endpoints

Comprehensive tests for campaign management API functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.campaign import Campaign, CampaignStatus
from app.models.kol import KOL, KOLStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "name": "Summer Fashion Campaign",
        "description": "Summer collection promotion with fashion influencers",
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "budget": 10000.00,
        "target_kpis": {
            "total_reach": 1000000,
            "engagement_rate": 0.05,
            "roi_percentage": 200
        },
        "required_keywords": ["summer", "fashion", "style"],
        "required_hashtags": ["#summerstyle", "#fashiontrends"],
        "brand_names": ["FashionBrand"],
        "industry": "fashion"
    }


@pytest.fixture
def sample_kol():
    """Sample KOL for testing."""
    return KOL(
        id=1,
        name="Fashion Influencer",
        email="influencer@example.com",
        social_media_accounts={
            "instagram": {"handle": "fashion_influencer", "verified": True}
        },
        niche=["fashion", "lifestyle"],
        status=KOLStatus.ACTIVE,
        follower_counts={"instagram": 50000},
        engagement_rates={"instagram": 0.05}
    )


class TestCampaignAPI:
    """Test cases for Campaign API endpoints."""

    @patch('app.api.endpoints.campaigns.get_db')
    def test_create_campaign_success(self, mock_get_db, client, mock_db, sample_campaign_data):
        """Test successful campaign creation."""
        mock_get_db.return_value = mock_db

        # Mock database operations
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock campaign creation
        created_campaign = Campaign(
            id=1,
            **sample_campaign_data,
            status=CampaignStatus.DRAFT,
            created_at=datetime.utcnow()
        )

        with patch('app.api.endpoints.campaigns.Campaign', return_value=created_campaign):
            response = client.post("/api/v1/campaigns", json=sample_campaign_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == sample_campaign_data["name"]
        assert response_data["status"] == "draft"

    def test_create_campaign_invalid_data(self, client):
        """Test campaign creation with invalid data."""
        invalid_data = {
            "name": "",  # Invalid: empty name
            "description": "Test campaign"
            # Missing required fields
        }

        response = client.post("/api/v1/campaigns", json=invalid_data)

        assert response.status_code == 422  # Validation error

    @patch('app.api.endpoints.campaigns.get_db')
    def test_get_campaign_by_id_success(self, mock_get_db, client, mock_db):
        """Test successful campaign retrieval by ID."""
        mock_get_db.return_value = mock_db

        # Mock campaign
        campaign = Campaign(
            id=1,
            name="Test Campaign",
            description="Test description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.ACTIVE
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = campaign
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/campaigns/1")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == 1
        assert response_data["name"] == "Test Campaign"

    @patch('app.api.endpoints.campaigns.get_db')
    def test_get_campaign_not_found(self, mock_get_db, client, mock_db):
        """Test campaign retrieval with non-existent ID."""
        mock_get_db.return_value = mock_db

        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/campaigns/999")

        assert response.status_code == 404

    @patch('app.api.endpoints.campaigns.get_db')
    def test_list_campaigns_success(self, mock_get_db, client, mock_db):
        """Test successful campaign listing."""
        mock_get_db.return_value = mock_db

        # Mock campaigns
        campaigns = [
            Campaign(
                id=1,
                name="Campaign 1",
                description="Description 1",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                status=CampaignStatus.ACTIVE
            ),
            Campaign(
                id=2,
                name="Campaign 2",
                description="Description 2",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=60),
                status=CampaignStatus.DRAFT
            )
        ]

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = campaigns
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/campaigns")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["name"] == "Campaign 1"
        assert response_data[1]["name"] == "Campaign 2"

    @patch('app.api.endpoints.campaigns.get_db')
    def test_list_campaigns_with_filters(self, mock_get_db, client, mock_db):
        """Test campaign listing with status filter."""
        mock_get_db.return_value = mock_db

        # Mock active campaigns only
        active_campaigns = [
            Campaign(
                id=1,
                name="Active Campaign",
                description="Active description",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                status=CampaignStatus.ACTIVE
            )
        ]

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = active_campaigns
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/campaigns?status=active")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["status"] == "active"

    @patch('app.api.endpoints.campaigns.get_db')
    def test_update_campaign_success(self, mock_get_db, client, mock_db):
        """Test successful campaign update."""
        mock_get_db.return_value = mock_db

        # Mock existing campaign
        existing_campaign = Campaign(
            id=1,
            name="Original Campaign",
            description="Original description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.DRAFT
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_campaign
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        update_data = {
            "name": "Updated Campaign",
            "description": "Updated description",
            "status": "active"
        }

        response = client.put("/api/v1/campaigns/1", json=update_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "Updated Campaign"
        assert response_data["status"] == "active"

    @patch('app.api.endpoints.campaigns.get_db')
    def test_update_campaign_not_found(self, mock_get_db, client, mock_db):
        """Test campaign update with non-existent ID."""
        mock_get_db.return_value = mock_db

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        update_data = {"name": "Updated Campaign"}

        response = client.put("/api/v1/campaigns/999", json=update_data)

        assert response.status_code == 404

    @patch('app.api.endpoints.campaigns.get_db')
    def test_delete_campaign_success(self, mock_get_db, client, mock_db):
        """Test successful campaign deletion."""
        mock_get_db.return_value = mock_db

        # Mock existing campaign
        existing_campaign = Campaign(
            id=1,
            name="Campaign to Delete",
            description="Description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.DRAFT
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_campaign
        mock_db.execute.return_value = mock_result
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        response = client.delete("/api/v1/campaigns/1")

        assert response.status_code == 204

    @patch('app.api.endpoints.campaigns.get_db')
    def test_delete_campaign_not_found(self, mock_get_db, client, mock_db):
        """Test campaign deletion with non-existent ID."""
        mock_get_db.return_value = mock_db

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.delete("/api/v1/campaigns/999")

        assert response.status_code == 404

    @patch('app.api.endpoints.campaigns.get_db')
    def test_assign_kol_to_campaign_success(self, mock_get_db, client, mock_db, sample_kol):
        """Test successful KOL assignment to campaign."""
        mock_get_db.return_value = mock_db

        # Mock campaign and KOL
        campaign = Campaign(
            id=1,
            name="Test Campaign",
            description="Test description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.ACTIVE
        )

        # Mock database queries
        campaign_result = AsyncMock()
        campaign_result.scalar_one_or_none.return_value = campaign
        kol_result = AsyncMock()
        kol_result.scalar_one_or_none.return_value = sample_kol

        mock_db.execute.side_effect = [campaign_result, kol_result]
        mock_db.commit.return_value = None

        assignment_data = {
            "kol_id": 1,
            "compensation": 1000.00,
            "currency": "USD",
            "deliverables_total": 3
        }

        response = client.post("/api/v1/campaigns/1/assign-kol", json=assignment_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["kol_id"] == 1
        assert response_data["compensation"] == 1000.00

    @patch('app.api.endpoints.campaigns.get_db')
    def test_assign_kol_campaign_not_found(self, mock_get_db, client, mock_db):
        """Test KOL assignment to non-existent campaign."""
        mock_get_db.return_value = mock_db

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        assignment_data = {"kol_id": 1, "compensation": 1000.00}

        response = client.post("/api/v1/campaigns/999/assign-kol", json=assignment_data)

        assert response.status_code == 404

    @patch('app.api.endpoints.campaigns.get_db')
    def test_get_campaign_performance_success(self, mock_get_db, client, mock_db):
        """Test successful campaign performance retrieval."""
        mock_get_db.return_value = mock_db

        # Mock campaign
        campaign = Campaign(
            id=1,
            name="Test Campaign",
            description="Test description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.ACTIVE
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = campaign
        mock_db.execute.return_value = mock_result

        # Mock performance calculation
        with patch('app.api.endpoints.campaigns.calculate_campaign_performance') as mock_calc:
            mock_calc.return_value = {
                "total_reach": 100000,
                "total_engagement": 5000,
                "engagement_rate": 0.05,
                "roi_percentage": 150.0,
                "total_posts": 10
            }

            response = client.get("/api/v1/campaigns/1/performance")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_reach"] == 100000
        assert response_data["engagement_rate"] == 0.05

    @patch('app.api.endpoints.campaigns.get_db')
    def test_get_campaign_content_success(self, mock_get_db, client, mock_db):
        """Test successful campaign content retrieval."""
        mock_get_db.return_value = mock_db

        # Mock campaign
        campaign = Campaign(
            id=1,
            name="Test Campaign",
            description="Test description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.ACTIVE
        )

        campaign_result = AsyncMock()
        campaign_result.scalar_one_or_none.return_value = campaign

        # Mock content posts
        content_posts = []  # Would be actual ContentPost objects

        content_result = AsyncMock()
        content_result.scalars.return_value.all.return_value = content_posts

        mock_db.execute.side_effect = [campaign_result, content_result]

        response = client.get("/api/v1/campaigns/1/content")

        assert response.status_code == 200
        response_data = response.json()
        assert isinstance(response_data, list)

    @patch('app.api.endpoints.campaigns.get_db')
    def test_generate_campaign_report_success(self, mock_get_db, client, mock_db):
        """Test successful campaign report generation."""
        mock_get_db.return_value = mock_db

        # Mock campaign
        campaign = Campaign(
            id=1,
            name="Test Campaign",
            description="Test description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.ACTIVE
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = campaign
        mock_db.execute.return_value = mock_result

        # Mock report generation
        with patch('app.api.endpoints.campaigns.generate_campaign_report') as mock_gen:
            mock_gen.return_value = {
                "report_id": "report_123",
                "campaign_id": 1,
                "generated_at": datetime.utcnow().isoformat(),
                "sections": {
                    "executive_summary": {},
                    "performance_metrics": {},
                    "recommendations": []
                }
            }

            report_request = {
                "report_type": "comprehensive",
                "include_comparisons": True,
                "format": "json"
            }

            response = client.post("/api/v1/campaigns/1/generate-report", json=report_request)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["campaign_id"] == 1
        assert "executive_summary" in response_data["sections"]

    def test_create_campaign_validation_errors(self, client):
        """Test campaign creation with various validation errors."""
        # Test missing required fields
        response = client.post("/api/v1/campaigns", json={})
        assert response.status_code == 422

        # Test invalid date range
        invalid_date_data = {
            "name": "Invalid Campaign",
            "description": "Test",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # End before start
            "budget": 1000
        }
        response = client.post("/api/v1/campaigns", json=invalid_date_data)
        assert response.status_code == 422

        # Test negative budget
        negative_budget_data = {
            "name": "Negative Budget Campaign",
            "description": "Test",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "budget": -1000  # Negative budget
        }
        response = client.post("/api/v1/campaigns", json=negative_budget_data)
        assert response.status_code == 422

    @patch('app.api.endpoints.campaigns.get_db')
    def test_campaign_status_transitions(self, mock_get_db, client, mock_db):
        """Test valid campaign status transitions."""
        mock_get_db.return_value = mock_db

        # Mock campaign in DRAFT status
        campaign = Campaign(
            id=1,
            name="Draft Campaign",
            description="Test description",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.DRAFT
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = campaign
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        # Test valid transition: DRAFT -> ACTIVE
        response = client.put("/api/v1/campaigns/1", json={"status": "active"})
        assert response.status_code == 200

        # Test valid transition: ACTIVE -> PAUSED
        campaign.status = CampaignStatus.ACTIVE
        response = client.put("/api/v1/campaigns/1", json={"status": "paused"})
        assert response.status_code == 200

        # Test valid transition: PAUSED -> COMPLETED
        campaign.status = CampaignStatus.PAUSED
        response = client.put("/api/v1/campaigns/1", json={"status": "completed"})
        assert response.status_code == 200