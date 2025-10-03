"""
Tests for content tracking service.

This module contains tests for content performance tracking,
checkpoint analytics, and automated reporting.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.services.content_tracking_service import (
    ContentTrackingService,
    CheckpointType
)
from app.models.campaign_content import CampaignContent, ContentStatus
from app.utils.datetime_utils import get_current_utc


@pytest.fixture
def db_session():
    """Mock database session fixture."""
    return MagicMock(spec=Session)


@pytest.fixture
def tracking_service(db_session):
    """Content tracking service fixture."""
    return ContentTrackingService(db_session)


@pytest.fixture
def sample_content():
    """Sample content fixture."""
    return CampaignContent(
        id=1,
        campaign_id=1,
        kol_id=1,
        platform="instagram",
        content_type="post",
        content_url="https://instagram.com/p/abc123",
        status=ContentStatus.PUBLISHED,
        published_at=get_current_utc() - timedelta(days=3),
        reach=10000,
        impressions=15000,
        engagement_rate=3.5,
        metrics={
            "reach": 10000,
            "impressions": 15000,
            "engagement_count": 350,
            "likes": 250,
            "comments": 50,
            "shares": 30,
            "saves": 20
        }
    )


class TestContentPublication:
    """Tests for content publication tracking."""

    def test_track_content_publication(self, tracking_service, db_session):
        """Test tracking content publication."""
        content = CampaignContent(
            id=1,
            campaign_id=1,
            kol_id=1,
            status=ContentStatus.APPROVED
        )

        db_session.query.return_value.filter.return_value.first.return_value = content
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        now = get_current_utc()
        initial_metrics = {"reach": 1000, "impressions": 1500}

        result = tracking_service.track_content_publication(
            content_id=1,
            publish_date=now,
            initial_metrics=initial_metrics
        )

        assert result is not None
        assert result.status == ContentStatus.PUBLISHED
        assert result.published_at == now
        assert result.metrics == initial_metrics

    def test_track_publication_content_not_found(self, tracking_service, db_session):
        """Test publication tracking fails for non-existent content."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = tracking_service.track_content_publication(
            content_id=999,
            publish_date=get_current_utc()
        )

        assert result is None


class TestMetricsUpdate:
    """Tests for metrics updates."""

    def test_update_content_metrics(self, tracking_service, db_session, sample_content):
        """Test updating content metrics."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_content
        db_session.commit = lambda: None
        db_session.refresh = lambda x: None

        new_metrics = {
            "reach": 12000,
            "impressions": 18000,
            "engagement_count": 420,
            "likes": 300
        }

        result = tracking_service.update_content_metrics(
            content_id=1,
            new_metrics=new_metrics
        )

        assert result is not None
        assert result.metrics["reach"] == 12000
        assert result.reach == 12000

    def test_update_metrics_content_not_found(self, tracking_service, db_session):
        """Test metrics update fails for non-existent content."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = tracking_service.update_content_metrics(
            content_id=999,
            new_metrics={"reach": 1000}
        )

        assert result is None


class TestCheckpointDetection:
    """Tests for checkpoint detection."""

    def test_get_checkpoint_content_d_plus_1(self, tracking_service, db_session):
        """Test getting content for D+1 checkpoint."""
        yesterday = get_current_utc() - timedelta(days=1)

        content_list = [
            CampaignContent(
                id=1,
                status=ContentStatus.PUBLISHED,
                published_at=yesterday - timedelta(hours=1)
            ),
            CampaignContent(
                id=2,
                status=ContentStatus.PUBLISHED,
                published_at=yesterday + timedelta(hours=1)
            )
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = content_list
        db_session.query.return_value = mock_query

        result = tracking_service.get_checkpoint_content(
            checkpoint_type=CheckpointType.D_PLUS_1,
            tolerance_hours=2
        )

        assert len(result) == 2

    def test_get_checkpoint_content_d_plus_7(self, tracking_service, db_session):
        """Test getting content for D+7 checkpoint."""
        week_ago = get_current_utc() - timedelta(days=7)

        content_list = [
            CampaignContent(
                id=1,
                status=ContentStatus.PUBLISHED,
                published_at=week_ago
            )
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = content_list
        db_session.query.return_value = mock_query

        result = tracking_service.get_checkpoint_content(
            checkpoint_type=CheckpointType.D_PLUS_7
        )

        assert len(result) == 1

    def test_get_checkpoint_unknown_type(self, tracking_service, db_session):
        """Test checkpoint with unknown type returns empty list."""
        result = tracking_service.get_checkpoint_content(
            checkpoint_type="unknown"
        )

        assert result == []


class TestCheckpointAnalysis:
    """Tests for checkpoint analysis."""

    def test_analyze_checkpoint_d_plus_3(self, tracking_service, db_session, sample_content):
        """Test D+3 checkpoint analysis."""
        db_session.query.return_value.filter.return_value.first.return_value = sample_content

        result = tracking_service.analyze_checkpoint(
            content_id=1,
            checkpoint_type=CheckpointType.D_PLUS_3
        )

        assert result["content_id"] == 1
        assert result["checkpoint"] == CheckpointType.D_PLUS_3
        assert result["metrics"]["reach"] == 10000
        assert result["metrics"]["engagement_rate"] == 3.5
        assert "performance_rating" in result

    def test_analyze_checkpoint_content_not_found(self, tracking_service, db_session):
        """Test checkpoint analysis for non-existent content."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = tracking_service.analyze_checkpoint(
            content_id=999,
            checkpoint_type=CheckpointType.D_PLUS_1
        )

        assert "error" in result


class TestPerformanceRating:
    """Tests for performance rating calculation."""

    def test_performance_rating_excellent(self, tracking_service):
        """Test excellent performance rating."""
        content = CampaignContent(
            id=1,
            engagement_rate=5.5
        )

        rating = tracking_service._calculate_performance_rating(
            content,
            CheckpointType.D_PLUS_1
        )

        assert rating == "excellent"

    def test_performance_rating_good(self, tracking_service):
        """Test good performance rating."""
        content = CampaignContent(
            id=1,
            engagement_rate=3.5
        )

        rating = tracking_service._calculate_performance_rating(
            content,
            CheckpointType.D_PLUS_1
        )

        assert rating == "good"

    def test_performance_rating_average(self, tracking_service):
        """Test average performance rating."""
        content = CampaignContent(
            id=1,
            engagement_rate=2.0
        )

        rating = tracking_service._calculate_performance_rating(
            content,
            CheckpointType.D_PLUS_1
        )

        assert rating == "average"

    def test_performance_rating_poor(self, tracking_service):
        """Test poor performance rating."""
        content = CampaignContent(
            id=1,
            engagement_rate=0.5
        )

        rating = tracking_service._calculate_performance_rating(
            content,
            CheckpointType.D_PLUS_1
        )

        assert rating == "poor"


class TestPerformanceTrend:
    """Tests for performance trend analysis."""

    def test_get_content_performance_trend(self, tracking_service, db_session):
        """Test getting performance trend."""
        published_date = get_current_utc() - timedelta(days=10)

        content = CampaignContent(
            id=1,
            status=ContentStatus.PUBLISHED,
            published_at=published_date,
            engagement_rate=3.5,
            metrics={"reach": 10000, "engagement_count": 350}
        )

        db_session.query.return_value.filter.return_value.first.return_value = content

        result = tracking_service.get_content_performance_trend(content_id=1)

        assert result["content_id"] == 1
        assert result["days_since_publish"] >= 10
        assert "checkpoints" in result
        assert "trend_summary" in result

    def test_calculate_trend_growing(self, tracking_service):
        """Test trend calculation - growing."""
        checkpoints = [
            {"metrics": {"engagement_rate": 2.0}},
            {"metrics": {"engagement_rate": 2.5}},
            {"metrics": {"engagement_rate": 3.0}}
        ]

        trend = tracking_service._calculate_trend_summary(checkpoints)

        assert trend["trend"] == "growing"
        assert trend["initial_engagement"] == 2.0
        assert trend["current_engagement"] == 3.0

    def test_calculate_trend_declining(self, tracking_service):
        """Test trend calculation - declining."""
        checkpoints = [
            {"metrics": {"engagement_rate": 4.0}},
            {"metrics": {"engagement_rate": 3.0}},
            {"metrics": {"engagement_rate": 2.0}}
        ]

        trend = tracking_service._calculate_trend_summary(checkpoints)

        assert trend["trend"] == "declining"

    def test_calculate_trend_stable(self, tracking_service):
        """Test trend calculation - stable."""
        checkpoints = [
            {"metrics": {"engagement_rate": 3.0}},
            {"metrics": {"engagement_rate": 3.1}},
            {"metrics": {"engagement_rate": 3.2}}
        ]

        trend = tracking_service._calculate_trend_summary(checkpoints)

        assert trend["trend"] == "stable"


class TestCampaignContentSummary:
    """Tests for campaign content summary."""

    def test_get_campaign_content_summary(self, tracking_service, db_session):
        """Test getting campaign content summary."""
        content_list = [
            CampaignContent(
                id=1,
                campaign_id=1,
                status=ContentStatus.PUBLISHED,
                reach=10000,
                impressions=15000,
                engagement_rate=3.5,
                published_at=get_current_utc() - timedelta(days=10),
                metrics={"engagement_count": 350}
            ),
            CampaignContent(
                id=2,
                campaign_id=1,
                status=ContentStatus.PUBLISHED,
                reach=8000,
                impressions=12000,
                engagement_rate=2.8,
                published_at=get_current_utc() - timedelta(days=8),
                metrics={"engagement_count": 224}
            ),
            CampaignContent(
                id=3,
                campaign_id=1,
                status=ContentStatus.PENDING_REVIEW
            )
        ]

        db_session.query.return_value.filter.return_value.all.return_value = content_list

        result = tracking_service.get_campaign_content_summary(campaign_id=1)

        assert result["campaign_id"] == 1
        assert result["total_content"] == 3
        assert result["published_content"] == 2
        assert result["pending_approval"] == 1
        assert result["aggregate_metrics"]["total_reach"] == 18000
        assert result["aggregate_metrics"]["total_impressions"] == 27000


class TestKOLContentPerformance:
    """Tests for KOL content performance."""

    def test_get_kol_content_performance(self, tracking_service, db_session):
        """Test getting KOL content performance."""
        content_list = [
            CampaignContent(
                id=1,
                kol_id=1,
                status=ContentStatus.PUBLISHED,
                content_type="post",
                engagement_rate=3.5,
                reach=10000,
                metrics={"engagement_count": 350}
            ),
            CampaignContent(
                id=2,
                kol_id=1,
                status=ContentStatus.PUBLISHED,
                content_type="story",
                engagement_rate=2.5,
                reach=8000,
                metrics={"engagement_count": 200}
            )
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = content_list
        db_session.query.return_value = mock_query

        result = tracking_service.get_kol_content_performance(kol_id=1)

        assert result["kol_id"] == 1
        assert result["published_content"] == 2
        assert result["performance"]["avg_engagement_rate"] == 3.0
        assert result["content_breakdown"]["posts"] == 1
        assert result["content_breakdown"]["stories"] == 1

    def test_get_kol_performance_no_content(self, tracking_service, db_session):
        """Test KOL performance with no published content."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        db_session.query.return_value = mock_query

        result = tracking_service.get_kol_content_performance(kol_id=1)

        assert result["published_content"] == 0
        assert "message" in result


class TestUnderperformingContent:
    """Tests for identifying underperforming content."""

    def test_identify_underperforming_content(self, tracking_service, db_session):
        """Test identifying underperforming content."""
        cutoff = get_current_utc() - timedelta(days=5)

        content_list = [
            CampaignContent(
                id=1,
                campaign_id=1,
                kol_id=1,
                status=ContentStatus.PUBLISHED,
                published_at=cutoff,
                engagement_rate=0.5,  # Poor
                reach=1000,
                content_url="https://instagram.com/p/abc123"
            ),
            CampaignContent(
                id=2,
                campaign_id=1,
                kol_id=2,
                status=ContentStatus.PUBLISHED,
                published_at=cutoff,
                engagement_rate=5.0,  # Excellent
                reach=10000,
                content_url="https://instagram.com/p/def456"
            )
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = content_list
        db_session.query.return_value = mock_query

        result = tracking_service.identify_underperforming_content(
            campaign_id=1,
            threshold_days=3
        )

        # Only content with poor/average rating should be returned
        assert len(result) == 1
        assert result[0]["content_id"] == 1
        assert result[0]["performance_rating"] in ["poor", "average"]
