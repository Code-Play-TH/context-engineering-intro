"""
Tests for campaign service.

This module contains comprehensive tests for campaign lifecycle management,
KOL assignment, budget tracking, and status transitions.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.campaign_service import CampaignService
from app.models.campaign import Campaign, CampaignStatus
from app.models.collaboration import Collaboration, CollaborationStatus
from app.models.kol import KOL
from app.models.user import User, UserRole
from app.utils.datetime_utils import get_current_utc


@pytest.fixture
def db_session():
    """Mock database session fixture."""
    # In real tests, use a test database session
    from unittest.mock import MagicMock
    return MagicMock(spec=Session)


@pytest.fixture
def campaign_service(db_session):
    """Campaign service fixture."""
    return CampaignService(db_session)


@pytest.fixture
def sample_user():
    """Sample user fixture."""
    return User(
        id=1,
        email="manager@example.com",
        username="manager",
        role=UserRole.MANAGER,
        is_active=True
    )


@pytest.fixture
def sample_kol():
    """Sample KOL fixture."""
    return KOL(
        id=1,
        name="Test KOL",
        platform="instagram",
        username="testkol",
        followers_count=50000,
        engagement_rate=3.5,
        niche="Fashion"
    )


@pytest.fixture
def sample_campaign():
    """Sample campaign fixture."""
    now = get_current_utc()
    return Campaign(
        id=1,
        name="Summer Fashion Campaign",
        description="Promote summer collection",
        budget=10000.0,
        currency="USD",
        start_date=now + timedelta(days=7),
        end_date=now + timedelta(days=37),
        created_by=1,
        status=CampaignStatus.DRAFT
    )


class TestCampaignCreation:
    """Tests for campaign creation."""

    def test_create_campaign_success(self, campaign_service, db_session):
        """Test successful campaign creation."""
        now = get_current_utc()
        start_date = now + timedelta(days=7)
        end_date = now + timedelta(days=37)

        # Mock DB operations
        db_session.add = lambda x: None
        db_session.commit = lambda: None
        db_session.refresh = lambda x: setattr(x, 'id', 1)

        campaign = campaign_service.create_campaign(
            name="Test Campaign",
            description="Test Description",
            budget=5000.0,
            currency="USD",
            start_date=start_date,
            end_date=end_date,
            created_by=1
        )

        assert campaign is not None
        assert campaign.name == "Test Campaign"
        assert campaign.budget == 5000.0
        assert campaign.status == CampaignStatus.DRAFT

    def test_create_campaign_invalid_dates(self, campaign_service):
        """Test campaign creation with invalid dates."""
        now = get_current_utc()
        start_date = now + timedelta(days=7)
        end_date = now + timedelta(days=3)  # Before start date

        with pytest.raises(ValueError, match="End date must be after start date"):
            campaign_service.create_campaign(
                name="Test Campaign",
                description="Test Description",
                budget=5000.0,
                currency="USD",
                start_date=start_date,
                end_date=end_date,
                created_by=1
            )


class TestCampaignStatusTransitions:
    """Tests for campaign status transitions."""

    def test_valid_status_transition(self, campaign_service, db_session, sample_campaign):
        """Test valid status transition."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        updated = campaign_service.change_status(
            campaign_id=1,
            new_status=CampaignStatus.PENDING_APPROVAL,
            changed_by=1
        )

        assert updated.status == CampaignStatus.PENDING_APPROVAL

    def test_invalid_status_transition(self, campaign_service, db_session, sample_campaign):
        """Test invalid status transition."""
        sample_campaign.status = CampaignStatus.COMPLETED
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign

        with pytest.raises(ValueError, match="Invalid status transition"):
            campaign_service.change_status(
                campaign_id=1,
                new_status=CampaignStatus.ACTIVE,
                changed_by=1
            )

    def test_status_transition_campaign_not_found(self, campaign_service, db_session):
        """Test status transition for non-existent campaign."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = campaign_service.change_status(
            campaign_id=999,
            new_status=CampaignStatus.ACTIVE,
            changed_by=1
        )

        assert result is None


class TestKOLAssignment:
    """Tests for KOL assignment to campaigns."""

    def test_assign_kol_success(self, campaign_service, db_session, sample_campaign, sample_kol):
        """Test successful KOL assignment."""
        # Mock DB queries
        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == KOL:
                mock.filter.return_value.first.return_value = sample_kol
            elif model == Collaboration:
                mock.filter.return_value.first.return_value = None  # No existing collaboration
            return mock

        db_session.query = mock_query
        db_session.add = lambda x: None
        db_session.commit = lambda: None
        db_session.refresh = lambda x: setattr(x, 'id', 1)

        collaboration = campaign_service.assign_kol(
            campaign_id=1,
            kol_id=1,
            compensation=1000.0,
            deliverables={"posts": 3, "stories": 5},
            assigned_by=1
        )

        assert collaboration is not None
        assert collaboration.compensation == 1000.0
        assert collaboration.status == CollaborationStatus.PENDING

    def test_assign_kol_insufficient_budget(self, campaign_service, db_session, sample_campaign, sample_kol):
        """Test KOL assignment with insufficient budget."""
        # Mock campaign with low budget
        sample_campaign.budget = 500.0

        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == KOL:
                mock.filter.return_value.first.return_value = sample_kol
            elif model == Collaboration:
                mock.filter.return_value.first.return_value = None
            return mock

        db_session.query = mock_query

        # Mock get_allocated_budget to return 0
        campaign_service.get_allocated_budget = lambda x: 0

        with pytest.raises(ValueError, match="Insufficient budget"):
            campaign_service.assign_kol(
                campaign_id=1,
                kol_id=1,
                compensation=1000.0,  # More than budget
                deliverables={"posts": 3},
                assigned_by=1
            )

    def test_assign_kol_already_assigned(self, campaign_service, db_session, sample_campaign, sample_kol):
        """Test assigning KOL that's already assigned."""
        existing_collab = Collaboration(
            id=1,
            campaign_id=1,
            kol_id=1,
            compensation=1000.0,
            status=CollaborationStatus.ACCEPTED
        )

        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == KOL:
                mock.filter.return_value.first.return_value = sample_kol
            elif model == Collaboration:
                mock.filter.return_value.first.return_value = existing_collab
            return mock

        db_session.query = mock_query

        with pytest.raises(ValueError, match="already assigned"):
            campaign_service.assign_kol(
                campaign_id=1,
                kol_id=1,
                compensation=500.0,
                deliverables={"posts": 2},
                assigned_by=1
            )


class TestBudgetManagement:
    """Tests for budget management."""

    def test_get_allocated_budget(self, campaign_service, db_session):
        """Test getting allocated budget."""
        # Mock sum query
        mock_query = MagicMock()
        mock_query.filter.return_value.scalar.return_value = 3500.0
        db_session.query.return_value = mock_query

        allocated = campaign_service.get_allocated_budget(campaign_id=1)

        assert allocated == 3500.0

    def test_get_budget_summary(self, campaign_service, db_session, sample_campaign):
        """Test getting budget summary."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign
        campaign_service.get_allocated_budget = lambda x: 6000.0

        summary = campaign_service.get_budget_summary(campaign_id=1)

        assert summary["total_budget"] == 10000.0
        assert summary["allocated"] == 6000.0
        assert summary["available"] == 4000.0
        assert summary["utilization_rate"] == 60.0
        assert summary["status"] == "healthy"

    def test_get_budget_summary_over_budget(self, campaign_service, db_session, sample_campaign):
        """Test budget summary when over budget."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign
        campaign_service.get_allocated_budget = lambda x: 11000.0

        summary = campaign_service.get_budget_summary(campaign_id=1)

        assert summary["utilization_rate"] == 110.0
        assert summary["status"] == "over_budget"


class TestTimelineTracking:
    """Tests for timeline tracking."""

    def test_get_campaign_timeline(self, campaign_service, db_session):
        """Test getting campaign timeline."""
        now = get_current_utc()
        campaign = Campaign(
            id=1,
            name="Test Campaign",
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            status=CampaignStatus.ACTIVE,
            budget=5000.0,
            currency="USD",
            created_by=1
        )

        db_session.query.return_value.filter.return_value.first.return_value = campaign

        timeline = campaign_service.get_campaign_timeline(campaign_id=1)

        assert timeline["total_days"] == 30
        assert timeline["elapsed_days"] == 10
        assert timeline["remaining_days"] == 20
        assert timeline["is_started"] is True
        assert timeline["is_ended"] is False
        assert 30 <= timeline["progress_percentage"] <= 35


class TestCampaignPerformance:
    """Tests for campaign performance metrics."""

    def test_get_campaign_performance(self, campaign_service, db_session, sample_campaign):
        """Test getting campaign performance."""
        # Mock collaborations
        collaborations = [
            Collaboration(id=1, campaign_id=1, kol_id=1, compensation=1000.0, status=CollaborationStatus.IN_PROGRESS),
            Collaboration(id=2, campaign_id=1, kol_id=2, compensation=1500.0, status=CollaborationStatus.COMPLETED),
            Collaboration(id=3, campaign_id=1, kol_id=3, compensation=800.0, status=CollaborationStatus.PENDING),
        ]

        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == Collaboration:
                mock.filter.return_value.all.return_value = collaborations
            return mock

        db_session.query = mock_query

        # Mock helper methods
        campaign_service.get_campaign_timeline = lambda x: {"progress_percentage": 50}
        campaign_service.get_budget_summary = lambda x: {"allocated": 3300.0}

        performance = campaign_service.get_campaign_performance(campaign_id=1)

        assert performance["kols"]["total"] == 3
        assert performance["kols"]["active"] == 1
        assert performance["kols"]["completed"] == 1
        assert performance["total_compensation"] == 3300.0


class TestCampaignDeletion:
    """Tests for campaign deletion."""

    def test_delete_draft_campaign(self, campaign_service, db_session, sample_campaign):
        """Test deleting draft campaign."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign
        db_session.commit = lambda: None

        result = campaign_service.delete_campaign(campaign_id=1)

        assert result is True
        assert sample_campaign.status == CampaignStatus.CANCELLED

    def test_delete_active_campaign_fails(self, campaign_service, db_session, sample_campaign):
        """Test that active campaigns cannot be deleted."""
        sample_campaign.status = CampaignStatus.ACTIVE
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign

        result = campaign_service.delete_campaign(campaign_id=1)

        assert result is False

    def test_delete_nonexistent_campaign(self, campaign_service, db_session):
        """Test deleting non-existent campaign."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = campaign_service.delete_campaign(campaign_id=999)

        assert result is False
