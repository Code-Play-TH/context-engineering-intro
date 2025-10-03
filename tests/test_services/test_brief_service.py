"""
Tests for brief service.

This module contains tests for campaign brief generation, templating,
versioning, and distribution functionality.
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.services.brief_service import BriefService, BriefTemplate
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_content import CampaignBrief, BriefStatus
from app.models.kol import KOL
from app.models.collaboration import Collaboration
from app.utils.datetime_utils import get_current_utc
from datetime import timedelta


@pytest.fixture
def db_session():
    """Mock database session fixture."""
    return MagicMock(spec=Session)


@pytest.fixture
def brief_service(db_session):
    """Brief service fixture."""
    return BriefService(db_session)


@pytest.fixture
def sample_campaign():
    """Sample campaign fixture."""
    now = get_current_utc()
    return Campaign(
        id=1,
        name="Summer Campaign",
        description="Summer collection promotion",
        budget=10000.0,
        currency="USD",
        start_date=now + timedelta(days=7),
        end_date=now + timedelta(days=37),
        status=CampaignStatus.DRAFT,
        created_by=1
    )


class TestBriefTemplates:
    """Tests for brief templates."""

    def test_standard_template_structure(self):
        """Test standard template has required sections."""
        template = BriefTemplate.get_standard_template()

        assert "sections" in template
        assert len(template["sections"]) == 6

        section_titles = [s["title"] for s in template["sections"]]
        assert "Campaign Overview" in section_titles
        assert "Target Audience" in section_titles
        assert "Content Requirements" in section_titles
        assert "Brand Guidelines" in section_titles
        assert "Deliverables" in section_titles
        assert "Compensation" in section_titles

    def test_detailed_template_has_extra_sections(self):
        """Test detailed template includes additional sections."""
        template = BriefTemplate.get_detailed_template()

        assert len(template["sections"]) > 6

        section_titles = [s["title"] for s in template["sections"]]
        assert "Performance Metrics" in section_titles
        assert "Legal & Compliance" in section_titles

    def test_minimal_template_is_shorter(self):
        """Test minimal template has fewer sections."""
        template = BriefTemplate.get_minimal_template()

        assert len(template["sections"]) == 3


class TestBriefCreation:
    """Tests for brief creation."""

    def test_create_brief_success(self, brief_service, db_session, sample_campaign):
        """Test successful brief creation."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign
        db_session.add = lambda x: setattr(x, 'id', 1)
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        brief = brief_service.create_brief(
            campaign_id=1,
            template_type=BriefTemplate.STANDARD,
            created_by=1
        )

        assert brief is not None
        assert brief.campaign_id == 1
        assert brief.status == BriefStatus.DRAFT
        assert brief.version == 1

    def test_create_brief_campaign_not_found(self, brief_service, db_session):
        """Test brief creation fails when campaign not found."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Campaign not found"):
            brief_service.create_brief(
                campaign_id=999,
                template_type=BriefTemplate.STANDARD,
                created_by=1
            )

    def test_create_brief_with_customization(self, brief_service, db_session, sample_campaign):
        """Test brief creation with custom fields."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_campaign
        db_session.add = lambda x: setattr(x, 'id', 1)
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        customization = {
            "tone": "Friendly and casual",
            "hashtags": ["#summer", "#fashion"],
            "posting_schedule": "3 times per week"
        }

        brief = brief_service.create_brief(
            campaign_id=1,
            template_type=BriefTemplate.STANDARD,
            customization=customization,
            created_by=1
        )

        assert brief is not None
        # Check that customization was applied
        assert "sections" in brief.content


class TestBriefUpdate:
    """Tests for brief updates."""

    def test_update_brief_without_versioning(self, brief_service, db_session):
        """Test updating brief in place."""
        existing_brief = CampaignBrief(
            id=1,
            campaign_id=1,
            title="Campaign Brief",
            content={"sections": []},
            template_type=BriefTemplate.STANDARD,
            version=1,
            status=BriefStatus.DRAFT
        )

        db_session.query.return_value.filter.return_value.first.return_value = existing_brief
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        updates = {"new_field": "new_value"}
        result = brief_service.update_brief(
            brief_id=1,
            updates=updates,
            create_new_version=False
        )

        assert result is not None
        assert "new_field" in result.content
        assert result.version == 1  # Version unchanged

    def test_update_brief_with_versioning(self, brief_service, db_session):
        """Test creating new version on update."""
        existing_brief = CampaignBrief(
            id=1,
            campaign_id=1,
            title="Campaign Brief",
            content={"sections": []},
            template_type=BriefTemplate.STANDARD,
            version=1,
            status=BriefStatus.PUBLISHED
        )

        db_session.query.return_value.filter.return_value.first.return_value = existing_brief
        db_session.add = lambda x: setattr(x, 'id', 2)
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        updates = {"new_field": "new_value"}
        result = brief_service.update_brief(
            brief_id=1,
            updates=updates,
            create_new_version=True
        )

        assert result is not None
        assert result.version == 2  # New version created

    def test_update_nonexistent_brief(self, brief_service, db_session):
        """Test updating non-existent brief."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = brief_service.update_brief(
            brief_id=999,
            updates={"field": "value"}
        )

        assert result is None


class TestBriefPublishing:
    """Tests for brief publishing."""

    def test_publish_brief_success(self, brief_service, db_session):
        """Test successful brief publishing."""
        draft_brief = CampaignBrief(
            id=1,
            campaign_id=1,
            title="Campaign Brief",
            content={"sections": []},
            template_type=BriefTemplate.STANDARD,
            version=1,
            status=BriefStatus.DRAFT
        )

        db_session.query.return_value.filter.return_value.first.return_value = draft_brief
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        result = brief_service.publish_brief(brief_id=1, published_by=1)

        assert result is not None
        assert result.status == BriefStatus.PUBLISHED
        assert result.published_at is not None

    def test_publish_already_published_brief(self, brief_service, db_session):
        """Test publishing already published brief fails."""
        published_brief = CampaignBrief(
            id=1,
            campaign_id=1,
            title="Campaign Brief",
            content={"sections": []},
            template_type=BriefTemplate.STANDARD,
            version=1,
            status=BriefStatus.PUBLISHED
        )

        db_session.query.return_value.filter.return_value.first.return_value = published_brief

        with pytest.raises(ValueError, match="Cannot publish brief"):
            brief_service.publish_brief(brief_id=1, published_by=1)


class TestBriefDistribution:
    """Tests for brief distribution."""

    def test_send_brief_to_kols(self, brief_service, db_session):
        """Test sending brief to KOLs."""
        published_brief = CampaignBrief(
            id=1,
            campaign_id=1,
            title="Campaign Brief",
            content={"sections": []},
            template_type=BriefTemplate.STANDARD,
            version=1,
            status=BriefStatus.PUBLISHED
        )

        kols = [
            KOL(id=1, name="KOL 1", email="kol1@example.com", platform="instagram"),
            KOL(id=2, name="KOL 2", email="kol2@example.com", platform="tiktok"),
        ]

        def mock_query(model):
            mock = MagicMock()
            if model == CampaignBrief:
                mock.filter.return_value.first.return_value = published_brief
            elif model == KOL:
                mock.filter.return_value.all.return_value = kols
            elif model == Collaboration:
                mock.filter.return_value.all.return_value = []
            return mock

        db_session.query = mock_query

        result = brief_service.send_brief_to_kols(
            brief_id=1,
            kol_ids=[1, 2]
        )

        assert result["total_kols"] == 2
        assert result["sent"] == 2
        assert result["failed"] == 0

    def test_send_unpublished_brief_fails(self, brief_service, db_session):
        """Test sending unpublished brief fails."""
        draft_brief = CampaignBrief(
            id=1,
            campaign_id=1,
            title="Campaign Brief",
            content={"sections": []},
            template_type=BriefTemplate.STANDARD,
            version=1,
            status=BriefStatus.DRAFT
        )

        db_session.query.return_value.filter.return_value.first.return_value = draft_brief

        with pytest.raises(ValueError, match="must be published"):
            brief_service.send_brief_to_kols(brief_id=1, kol_ids=[1])


class TestBriefVersioning:
    """Tests for brief versioning."""

    def test_get_brief_versions(self, brief_service, db_session):
        """Test getting all brief versions."""
        briefs = [
            CampaignBrief(id=1, campaign_id=1, version=1, status=BriefStatus.ARCHIVED),
            CampaignBrief(id=2, campaign_id=1, version=2, status=BriefStatus.ARCHIVED),
            CampaignBrief(id=3, campaign_id=1, version=3, status=BriefStatus.PUBLISHED),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = briefs[::-1]
        db_session.query.return_value = mock_query

        result = brief_service.get_brief_versions(campaign_id=1)

        assert len(result) == 3

    def test_get_latest_brief(self, brief_service, db_session):
        """Test getting latest published brief."""
        latest_brief = CampaignBrief(
            id=3,
            campaign_id=1,
            version=3,
            status=BriefStatus.PUBLISHED
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = latest_brief
        db_session.query.return_value = mock_query

        result = brief_service.get_latest_brief(campaign_id=1)

        assert result is not None
        assert result.version == 3
        assert result.status == BriefStatus.PUBLISHED


class TestBriefArchiving:
    """Tests for brief archiving."""

    def test_archive_brief_success(self, brief_service, db_session):
        """Test successful brief archiving."""
        brief = CampaignBrief(
            id=1,
            campaign_id=1,
            version=1,
            status=BriefStatus.PUBLISHED
        )

        db_session.query.return_value.filter.return_value.first.return_value = brief
        db_session.commit = lambda: None

        result = brief_service.archive_brief(brief_id=1)

        assert result is True
        assert brief.status == BriefStatus.ARCHIVED

    def test_archive_nonexistent_brief(self, brief_service, db_session):
        """Test archiving non-existent brief."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = brief_service.archive_brief(brief_id=999)

        assert result is False
