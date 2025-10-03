"""
Tests for collaboration service.

This module contains tests for KOL-Campaign collaboration management,
content submission, approval workflows, and payment tracking.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from app.services.collaboration_service import CollaborationService
from app.models.collaboration import Collaboration, CollaborationStatus
from app.models.campaign_content import CampaignContent, ContentStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.kol import KOL
from app.utils.datetime_utils import get_current_utc


@pytest.fixture
def db_session():
    """Mock database session fixture."""
    return MagicMock(spec=Session)


@pytest.fixture
def collaboration_service(db_session):
    """Collaboration service fixture."""
    return CollaborationService(db_session)


@pytest.fixture
def sample_collaboration():
    """Sample collaboration fixture."""
    return Collaboration(
        id=1,
        campaign_id=1,
        kol_id=1,
        compensation=1500.0,
        deliverables={"posts": 3, "stories": 5, "total_posts": 8},
        status=CollaborationStatus.IN_PROGRESS
    )


@pytest.fixture
def sample_campaign():
    """Sample campaign fixture."""
    return Campaign(
        id=1,
        name="Test Campaign",
        budget=10000.0,
        currency="USD",
        status=CampaignStatus.ACTIVE,
        created_by=1
    )


class TestCollaborationRetrieval:
    """Tests for collaboration retrieval."""

    def test_get_collaboration_success(self, collaboration_service, db_session, sample_collaboration):
        """Test successful collaboration retrieval."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_collaboration

        result = collaboration_service.get_collaboration(collaboration_id=1)

        assert result is not None
        assert result.id == 1
        assert result.compensation == 1500.0

    def test_get_collaboration_not_found(self, collaboration_service, db_session):
        """Test retrieving non-existent collaboration."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = collaboration_service.get_collaboration(collaboration_id=999)

        assert result is None


class TestDeliverablesUpdate:
    """Tests for updating deliverables."""

    def test_update_deliverables_success(self, collaboration_service, db_session, sample_collaboration):
        """Test successful deliverables update."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_collaboration
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        new_deliverables = {"posts": 5, "stories": 10, "total_posts": 15}

        result = collaboration_service.update_deliverables(
            collaboration_id=1,
            deliverables=new_deliverables
        )

        assert result is not None
        assert result.deliverables == new_deliverables

    def test_update_deliverables_not_found(self, collaboration_service, db_session):
        """Test updating deliverables for non-existent collaboration."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = collaboration_service.update_deliverables(
            collaboration_id=999,
            deliverables={"posts": 5}
        )

        assert result is None


class TestContentSubmission:
    """Tests for content submission."""

    def test_submit_content_success(self, collaboration_service, db_session, sample_collaboration):
        """Test successful content submission."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_collaboration
        db_session.add = lambda x: None
        db_session.commit = lambda: None
        db_session.refresh = lambda x: setattr(x, 'id', 1)

        content = collaboration_service.submit_content(
            collaboration_id=1,
            content_type="post",
            content_url="https://instagram.com/p/abc123",
            platform="instagram",
            submitted_by=1,
            metadata={"caption": "Test post"}
        )

        assert content is not None
        assert content.content_type == "post"
        assert content.status == ContentStatus.PENDING_REVIEW

    def test_submit_content_invalid_status(self, collaboration_service, db_session, sample_collaboration):
        """Test submitting content for collaboration in invalid status."""
        sample_collaboration.status = CollaborationStatus.COMPLETED
        db_session.query.return_value.filter.return_value.first.return_value = sample_collaboration

        with pytest.raises(ValueError, match="Cannot submit content"):
            collaboration_service.submit_content(
                collaboration_id=1,
                content_type="post",
                content_url="https://instagram.com/p/abc123",
                platform="instagram",
                submitted_by=1
            )

    def test_submit_content_collaboration_not_found(self, collaboration_service, db_session):
        """Test submitting content for non-existent collaboration."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Collaboration not found"):
            collaboration_service.submit_content(
                collaboration_id=999,
                content_type="post",
                content_url="https://instagram.com/p/abc123",
                platform="instagram",
                submitted_by=1
            )


class TestContentApproval:
    """Tests for content approval workflow."""

    def test_approve_content_success(self, collaboration_service, db_session):
        """Test successful content approval."""
        content = CampaignContent(
            id=1,
            collaboration_id=1,
            campaign_id=1,
            kol_id=1,
            content_type="post",
            content_url="https://instagram.com/p/abc123",
            platform="instagram",
            status=ContentStatus.PENDING_REVIEW
        )

        db_session.query.return_value.filter.return_value.first.return_value = content
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        result = collaboration_service.approve_content(
            content_id=1,
            approved_by=1,
            notes="Looks great!"
        )

        assert result is not None
        assert result.status == ContentStatus.APPROVED
        assert result.approved_by == 1

    def test_approve_content_not_found(self, collaboration_service, db_session):
        """Test approving non-existent content."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = collaboration_service.approve_content(
            content_id=999,
            approved_by=1
        )

        assert result is None

    def test_reject_content_success(self, collaboration_service, db_session):
        """Test successful content rejection."""
        content = CampaignContent(
            id=1,
            collaboration_id=1,
            campaign_id=1,
            kol_id=1,
            content_type="post",
            content_url="https://instagram.com/p/abc123",
            platform="instagram",
            status=ContentStatus.PENDING_REVIEW,
            metadata={}
        )

        db_session.query.return_value.filter.return_value.first.return_value = content
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        result = collaboration_service.reject_content(
            content_id=1,
            rejected_by=1,
            reason="Does not match brand guidelines"
        )

        assert result is not None
        assert result.status == ContentStatus.REJECTED
        assert "rejection_reason" in result.metadata


class TestCollaborationProgress:
    """Tests for collaboration progress tracking."""

    def test_get_collaboration_progress(self, collaboration_service, db_session, sample_collaboration):
        """Test getting collaboration progress."""
        # Mock content
        content_list = [
            CampaignContent(id=1, collaboration_id=1, status=ContentStatus.PUBLISHED),
            CampaignContent(id=2, collaboration_id=1, status=ContentStatus.PUBLISHED),
            CampaignContent(id=3, collaboration_id=1, status=ContentStatus.APPROVED),
            CampaignContent(id=4, collaboration_id=1, status=ContentStatus.PENDING_REVIEW),
        ]

        def mock_query(model):
            mock = MagicMock()
            if model == Collaboration:
                mock.filter.return_value.first.return_value = sample_collaboration
            elif model == CampaignContent:
                mock.filter.return_value.order_by.return_value.all.return_value = content_list
            return mock

        db_session.query = mock_query

        progress = collaboration_service.get_collaboration_progress(collaboration_id=1)

        assert progress["content"]["total"] == 4
        assert progress["content"]["published"] == 2
        assert progress["content"]["approved"] == 1
        assert progress["content"]["pending"] == 1
        assert progress["expected_count"] == 8
        assert progress["completion_percentage"] == 25.0  # 2 published out of 8 expected


class TestCollaborationCompletion:
    """Tests for marking collaboration as complete."""

    def test_mark_collaboration_complete_success(self, collaboration_service, db_session, sample_collaboration):
        """Test successfully marking collaboration as complete."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_collaboration
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        # Mock progress at 100%
        collaboration_service.get_collaboration_progress = lambda x: {"completion_percentage": 100}

        result = collaboration_service.mark_collaboration_complete(
            collaboration_id=1,
            completed_by=1
        )

        assert result is not None
        assert result.status == CollaborationStatus.COMPLETED

    def test_mark_collaboration_complete_incomplete_deliverables(self, collaboration_service, db_session, sample_collaboration):
        """Test marking collaboration complete with incomplete deliverables."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_collaboration

        # Mock progress at 50%
        collaboration_service.get_collaboration_progress = lambda x: {"completion_percentage": 50}

        with pytest.raises(ValueError, match="Cannot complete collaboration"):
            collaboration_service.mark_collaboration_complete(
                collaboration_id=1,
                completed_by=1
            )

    def test_mark_collaboration_complete_not_found(self, collaboration_service, db_session):
        """Test marking non-existent collaboration as complete."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Collaboration not found"):
            collaboration_service.mark_collaboration_complete(
                collaboration_id=999,
                completed_by=1
            )


class TestKOLCollaborations:
    """Tests for getting KOL collaborations."""

    def test_get_kol_collaborations(self, collaboration_service, db_session):
        """Test getting all collaborations for a KOL."""
        collaborations = [
            (
                Collaboration(id=1, campaign_id=1, kol_id=1, compensation=1500.0, status=CollaborationStatus.IN_PROGRESS),
                Campaign(id=1, name="Campaign 1", status=CampaignStatus.ACTIVE)
            ),
            (
                Collaboration(id=2, campaign_id=2, kol_id=1, compensation=2000.0, status=CollaborationStatus.COMPLETED),
                Campaign(id=2, name="Campaign 2", status=CampaignStatus.COMPLETED)
            ),
        ]

        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = collaborations
        db_session.query.return_value = mock_query

        result = collaboration_service.get_kol_collaborations(kol_id=1)

        assert len(result) == 2
        assert result[0]["collaboration_id"] == 1
        assert result[0]["campaign"]["name"] == "Campaign 1"
        assert result[1]["collaboration_id"] == 2


class TestPaymentSummary:
    """Tests for payment summary."""

    def test_get_payment_summary_completed(self, collaboration_service, db_session, sample_collaboration, sample_campaign):
        """Test payment summary for completed collaboration."""
        sample_collaboration.status = CollaborationStatus.COMPLETED

        def mock_query(model):
            mock = MagicMock()
            if model == Collaboration:
                mock.filter.return_value.first.return_value = sample_collaboration
            elif model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            return mock

        db_session.query = mock_query

        summary = collaboration_service.get_payment_summary(collaboration_id=1)

        assert summary["compensation"] == 1500.0
        assert summary["currency"] == "USD"
        assert summary["payment_status"] == "ready_for_payment"

    def test_get_payment_summary_cancelled(self, collaboration_service, db_session, sample_collaboration, sample_campaign):
        """Test payment summary for cancelled collaboration."""
        sample_collaboration.status = CollaborationStatus.CANCELLED

        def mock_query(model):
            mock = MagicMock()
            if model == Collaboration:
                mock.filter.return_value.first.return_value = sample_collaboration
            elif model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            return mock

        db_session.query = mock_query

        summary = collaboration_service.get_payment_summary(collaboration_id=1)

        assert summary["payment_status"] == "cancelled"
