"""
Tests for social media data ingestion tasks.

This module contains tests for Celery tasks that handle
social media data synchronization and metrics updates.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.tasks.social_media_tasks import (
    sync_kol_profile,
    sync_content_metrics,
    bulk_sync_kol_profiles,
    bulk_sync_campaign_content,
    _fetch_platform_profile,
    _fetch_content_metrics
)
from app.models.kol import KOL
from app.models.campaign_content import CampaignContent, ContentStatus
from app.utils.datetime_utils import get_current_utc


class TestKOLProfileSync:
    """Tests for KOL profile synchronization."""

    @patch("app.tasks.social_media_tasks.get_db_session")
    @patch("app.tasks.social_media_tasks._fetch_platform_profile")
    def test_sync_kol_profile_success(self, mock_fetch, mock_db):
        """Test successful KOL profile sync."""
        # Mock database
        mock_session = MagicMock()
        mock_db.return_value = iter([mock_session])

        # Mock KOL
        kol = KOL(
            id=1,
            username="testkol",
            platform="instagram",
            followers_count=10000,
            engagement_rate=2.5
        )
        mock_session.query.return_value.filter.return_value.first.return_value = kol

        # Mock platform data
        mock_fetch.return_value = {
            "followers_count": 15000,
            "engagement_rate": 3.5,
            "posts_count": 150
        }

        # Execute
        result = sync_kol_profile(kol_id=1, platform="instagram")

        # Assert
        assert result["success"] is True
        assert result["kol_id"] == 1
        assert result["followers_count"] == 15000
        assert kol.followers_count == 15000
        assert kol.engagement_rate == 3.5

    @patch("app.tasks.social_media_tasks.get_db_session")
    def test_sync_kol_profile_not_found(self, mock_db):
        """Test sync fails when KOL not found."""
        mock_session = MagicMock()
        mock_db.return_value = iter([mock_session])
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="KOL not found"):
            sync_kol_profile(kol_id=999, platform="instagram")


class TestContentMetricsSync:
    """Tests for content metrics synchronization."""

    @patch("app.tasks.social_media_tasks.get_db_session")
    @patch("app.tasks.social_media_tasks._fetch_content_metrics")
    def test_sync_content_metrics_success(self, mock_fetch, mock_db):
        """Test successful content metrics sync."""
        mock_session = MagicMock()
        mock_db.return_value = iter([mock_session])

        # Mock content
        content = CampaignContent(
            id=1,
            platform="instagram",
            content_url="https://instagram.com/p/abc123",
            reach=5000,
            engagement_rate=2.0,
            metrics={}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = content

        # Mock metrics data
        mock_fetch.return_value = {
            "reach": 10000,
            "impressions": 15000,
            "engagement_count": 500,
            "likes": 350
        }

        # Execute
        result = sync_content_metrics(content_id=1)

        # Assert
        assert result["success"] is True
        assert result["content_id"] == 1
        assert result["reach"] == 10000

    @patch("app.tasks.social_media_tasks.get_db_session")
    def test_sync_content_metrics_no_url(self, mock_db):
        """Test sync fails when content has no URL."""
        mock_session = MagicMock()
        mock_db.return_value = iter([mock_session])

        content = CampaignContent(
            id=1,
            platform="instagram",
            content_url=None
        )
        mock_session.query.return_value.filter.return_value.first.return_value = content

        with pytest.raises(ValueError, match="Content URL not available"):
            sync_content_metrics(content_id=1)


class TestBulkSync:
    """Tests for bulk synchronization operations."""

    @patch("app.tasks.social_media_tasks.get_db_session")
    @patch("app.tasks.social_media_tasks.sync_kol_profile")
    def test_bulk_sync_kol_profiles(self, mock_sync, mock_db):
        """Test bulk KOL profile synchronization."""
        mock_session = MagicMock()
        mock_db.return_value = iter([mock_session])

        # Mock KOLs
        kols = [
            KOL(id=1, platform="instagram"),
            KOL(id=2, platform="tiktok"),
            KOL(id=3, platform="youtube"),
        ]

        def get_kol(kol_id):
            return next((k for k in kols if k.id == kol_id), None)

        mock_session.query.return_value.filter.return_value.first.side_effect = get_kol

        # Mock delay
        mock_sync.delay = MagicMock()

        # Execute
        result = bulk_sync_kol_profiles([1, 2, 3])

        # Assert
        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0
        assert mock_sync.delay.call_count == 3

    @patch("app.tasks.social_media_tasks.get_db_session")
    @patch("app.tasks.social_media_tasks.sync_content_metrics")
    def test_bulk_sync_campaign_content(self, mock_sync, mock_db):
        """Test bulk campaign content synchronization."""
        mock_session = MagicMock()
        mock_db.return_value = iter([mock_session])

        # Mock content
        content_list = [
            CampaignContent(id=1, status=ContentStatus.PUBLISHED),
            CampaignContent(id=2, status=ContentStatus.PUBLISHED),
        ]

        mock_session.query.return_value.filter.return_value.all.return_value = content_list

        # Mock delay
        mock_sync.delay = MagicMock()

        # Execute
        result = bulk_sync_campaign_content(campaign_id=1)

        # Assert
        assert result["campaign_id"] == 1
        assert result["total_content"] == 2
        assert result["synced"] == 2
        assert mock_sync.delay.call_count == 2


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_fetch_platform_profile(self):
        """Test fetching platform profile data."""
        result = _fetch_platform_profile("instagram", "testuser")

        assert "followers_count" in result
        assert "engagement_rate" in result
        assert isinstance(result["followers_count"], int)

    def test_fetch_content_metrics(self):
        """Test fetching content metrics."""
        result = _fetch_content_metrics("instagram", "https://instagram.com/p/abc123")

        assert "reach" in result
        assert "impressions" in result
        assert "engagement_count" in result
        assert isinstance(result["reach"], int)
