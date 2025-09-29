"""
Tests for Content Monitoring Service

Tests the core content detection and monitoring functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content_monitoring.content_monitor import ContentMonitorService
from app.models.kol import KOL, KOLStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.content import ContentPost, VerificationStatus
from app.schemas.content_monitoring import (
    PlatformPost, ContentMatchResult, SocialPlatform
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def content_monitor_service(mock_db):
    """Content monitor service with mocked dependencies."""
    with patch('app.services.content_monitoring.content_monitor.AIContentAnalyzer') as mock_ai, \
         patch('app.services.content_monitoring.content_monitor.SocialMediaServiceFactory') as mock_factory:

        service = ContentMonitorService(mock_db)
        service.ai_analyzer = AsyncMock()
        service.social_media_factory = mock_factory.return_value
        return service


@pytest.fixture
def sample_kol():
    """Sample KOL for testing."""
    return KOL(
        id=1,
        name="Test KOL",
        email="test@example.com",
        social_media_accounts={
            "instagram": {
                "handle": "test_kol",
                "id": "123456789",
                "verified": True
            }
        },
        niche=["fashion", "lifestyle"],
        status=KOLStatus.ACTIVE,
        follower_counts={"instagram": 10000},
        engagement_rates={"instagram": 0.05}
    )


@pytest.fixture
def sample_campaign():
    """Sample campaign for testing."""
    return Campaign(
        id=1,
        name="Test Campaign",
        description="Test campaign description",
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        status=CampaignStatus.ACTIVE,
        required_keywords=["brand", "product"],
        required_hashtags=["#brandname"],
        brand_names=["BrandName"],
        target_keywords=["fashion", "style"]
    )


@pytest.fixture
def sample_platform_post():
    """Sample platform post for testing."""
    return PlatformPost(
        id="post_123",
        content="Check out this amazing #brandname product! So stylish and perfect for fashion lovers. @brandname",
        url="https://instagram.com/p/post_123",
        hashtags=["brandname", "fashion", "style"],
        mentions=["brandname"],
        created_at=datetime.utcnow(),
        likes=100,
        comments=20,
        shares=5
    )


class TestContentMonitorService:
    """Test cases for ContentMonitorService."""

    @pytest.mark.asyncio
    async def test_detect_new_content_success(
        self,
        content_monitor_service,
        sample_kol,
        sample_campaign,
        sample_platform_post
    ):
        """Test successful content detection."""
        # Mock social media service
        mock_service = AsyncMock()
        mock_service.get_recent_posts.return_value = [sample_platform_post]
        content_monitor_service.social_media_factory.get_service.return_value = mock_service

        # Mock content match analysis
        content_monitor_service._analyze_content_match = AsyncMock(
            return_value=ContentMatchResult(
                is_match=True,
                confidence=0.85,
                matched_criteria=["keywords", "brand_mentions"],
                analysis_details={"keyword_score": 0.8, "brand_score": 0.9}
            )
        )

        # Mock existing post check
        content_monitor_service._check_existing_post = AsyncMock(return_value=None)

        # Mock stats scheduling
        content_monitor_service._schedule_stats_collection = AsyncMock()

        # Mock notification
        content_monitor_service._send_content_detected_notification = AsyncMock()

        # Execute
        result = await content_monitor_service.detect_new_content(sample_kol, sample_campaign)

        # Assertions
        assert len(result) == 1
        content_post = result[0]
        assert content_post.kol_id == sample_kol.id
        assert content_post.campaign_id == sample_campaign.id
        assert content_post.platform == "instagram"
        assert content_post.confidence_score == 0.85
        assert content_post.verification_status == VerificationStatus.PENDING

        # Verify service calls
        mock_service.get_recent_posts.assert_called_once()
        content_monitor_service._schedule_stats_collection.assert_called_once()
        content_monitor_service._send_content_detected_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_new_content_no_match(
        self,
        content_monitor_service,
        sample_kol,
        sample_campaign,
        sample_platform_post
    ):
        """Test content detection with no matching content."""
        # Mock social media service
        mock_service = AsyncMock()
        mock_service.get_recent_posts.return_value = [sample_platform_post]
        content_monitor_service.social_media_factory.get_service.return_value = mock_service

        # Mock content match analysis - no match
        content_monitor_service._analyze_content_match = AsyncMock(
            return_value=ContentMatchResult(
                is_match=False,
                confidence=0.3,
                matched_criteria=[],
                analysis_details={"keyword_score": 0.2, "brand_score": 0.1}
            )
        )

        # Mock existing post check
        content_monitor_service._check_existing_post = AsyncMock(return_value=None)

        # Execute
        result = await content_monitor_service.detect_new_content(sample_kol, sample_campaign)

        # Assertions
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_analyze_content_match_high_confidence(
        self,
        content_monitor_service,
        sample_platform_post,
        sample_campaign
    ):
        """Test content matching analysis with high confidence."""
        # Mock individual analysis methods
        content_monitor_service._check_keyword_match = AsyncMock(return_value=0.9)
        content_monitor_service._check_brand_mentions = AsyncMock(return_value=0.8)
        content_monitor_service._ai_content_analysis = AsyncMock(return_value=0.7)
        content_monitor_service._check_timing_relevance = MagicMock(return_value=1.0)

        # Execute
        result = await content_monitor_service._analyze_content_match(
            sample_platform_post, sample_campaign
        )

        # Assertions
        assert result.is_match is True
        assert result.confidence > 0.8
        assert "keywords" in result.matched_criteria
        assert "brand_mentions" in result.matched_criteria
        assert "ai_content_analysis" in result.matched_criteria
        assert "timing" in result.matched_criteria

    @pytest.mark.asyncio
    async def test_analyze_content_match_low_confidence(
        self,
        content_monitor_service,
        sample_platform_post,
        sample_campaign
    ):
        """Test content matching analysis with low confidence."""
        # Mock individual analysis methods with low scores
        content_monitor_service._check_keyword_match = AsyncMock(return_value=0.2)
        content_monitor_service._check_brand_mentions = AsyncMock(return_value=0.1)
        content_monitor_service._ai_content_analysis = AsyncMock(return_value=0.3)
        content_monitor_service._check_timing_relevance = MagicMock(return_value=0.4)

        # Execute
        result = await content_monitor_service._analyze_content_match(
            sample_platform_post, sample_campaign
        )

        # Assertions
        assert result.is_match is False
        assert result.confidence < content_monitor_service.confidence_threshold

    @pytest.mark.asyncio
    async def test_check_keyword_match_success(
        self,
        content_monitor_service,
        sample_platform_post,
        sample_campaign
    ):
        """Test keyword matching with successful match."""
        # Execute
        score = await content_monitor_service._check_keyword_match(
            sample_platform_post, sample_campaign
        )

        # Assertions
        assert score > 0.5  # Should match required keywords and hashtags

    @pytest.mark.asyncio
    async def test_check_keyword_match_failure(
        self,
        content_monitor_service,
        sample_campaign
    ):
        """Test keyword matching with failed match."""
        # Create post without matching keywords
        post = PlatformPost(
            id="post_456",
            content="Random content without any matching terms",
            url="https://instagram.com/p/post_456",
            hashtags=["random"],
            mentions=[],
            created_at=datetime.utcnow()
        )

        # Execute
        score = await content_monitor_service._check_keyword_match(post, sample_campaign)

        # Assertions
        assert score == 0.0  # Should fail due to missing required keywords

    @pytest.mark.asyncio
    async def test_check_brand_mentions_success(
        self,
        content_monitor_service,
        sample_platform_post,
        sample_campaign
    ):
        """Test brand mention detection with successful match."""
        # Execute
        score = await content_monitor_service._check_brand_mentions(
            sample_platform_post, sample_campaign
        )

        # Assertions
        assert score > 0.0  # Should detect brand mentions

    @pytest.mark.asyncio
    async def test_ai_content_analysis(
        self,
        content_monitor_service,
        sample_platform_post,
        sample_campaign
    ):
        """Test AI content analysis."""
        # Mock AI analyzer response
        content_monitor_service.ai_analyzer.analyze_content.return_value = {
            "topics": ["fashion", "style"],
            "sentiment_score": 0.8,
            "quality_score": 0.7
        }

        # Execute
        score = await content_monitor_service._ai_content_analysis(
            sample_platform_post, sample_campaign
        )

        # Assertions
        assert 0.0 <= score <= 1.0
        content_monitor_service.ai_analyzer.analyze_content.assert_called_once()

    def test_check_timing_relevance_within_period(
        self,
        content_monitor_service,
        sample_platform_post,
        sample_campaign
    ):
        """Test timing relevance check within campaign period."""
        # Execute
        score = content_monitor_service._check_timing_relevance(
            sample_platform_post, sample_campaign
        )

        # Assertions
        assert score > 0.0  # Should have positive score for recent post

    def test_check_timing_relevance_outside_period(
        self,
        content_monitor_service,
        sample_campaign
    ):
        """Test timing relevance check outside campaign period."""
        # Create post outside campaign period
        post = PlatformPost(
            id="post_old",
            content="Old content",
            url="https://instagram.com/p/post_old",
            hashtags=[],
            mentions=[],
            created_at=datetime.utcnow() - timedelta(days=60)  # Before campaign
        )

        # Execute
        score = content_monitor_service._check_timing_relevance(post, sample_campaign)

        # Assertions
        assert score == 0.0  # Should be zero for posts outside campaign period

    @pytest.mark.asyncio
    async def test_verify_content_manually_success(
        self,
        content_monitor_service,
        mock_db
    ):
        """Test manual content verification."""
        # Mock content post
        content_post = ContentPost(
            id=1,
            verification_status=VerificationStatus.PENDING
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = content_post
        mock_db.execute.return_value = mock_result

        # Execute
        result = await content_monitor_service.verify_content_manually(
            1, VerificationStatus.VERIFIED, "Manually verified"
        )

        # Assertions
        assert result.verification_status == VerificationStatus.VERIFIED
        assert result.verification_notes == "Manually verified"
        assert result.verified_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_content_manually_not_found(
        self,
        content_monitor_service,
        mock_db
    ):
        """Test manual content verification with non-existent post."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Execute and assert exception
        with pytest.raises(ValueError, match="Content post 999 not found"):
            await content_monitor_service.verify_content_manually(
                999, VerificationStatus.VERIFIED
            )

    @pytest.mark.asyncio
    async def test_get_campaign_content_summary(
        self,
        content_monitor_service,
        mock_db
    ):
        """Test campaign content summary generation."""
        # Mock content posts
        content_posts = [
            ContentPost(
                id=1,
                verification_status=VerificationStatus.VERIFIED,
                platform="instagram",
                confidence_score=0.85
            ),
            ContentPost(
                id=2,
                verification_status=VerificationStatus.PENDING,
                platform="youtube",
                confidence_score=0.75
            ),
            ContentPost(
                id=3,
                verification_status=VerificationStatus.REJECTED,
                platform="instagram",
                confidence_score=0.65
            )
        ]

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = content_posts
        mock_db.execute.return_value = mock_result

        # Execute
        summary = await content_monitor_service.get_campaign_content_summary(1)

        # Assertions
        assert summary["total_posts"] == 3
        assert summary["verified_posts"] == 1
        assert summary["pending_posts"] == 1
        assert summary["rejected_posts"] == 1
        assert summary["platforms"]["instagram"] == 2
        assert summary["platforms"]["youtube"] == 1
        assert summary["average_confidence"] == 0.75

    @pytest.mark.asyncio
    async def test_get_campaign_content_summary_empty(
        self,
        content_monitor_service,
        mock_db
    ):
        """Test campaign content summary with no content."""
        # Mock empty result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Execute
        summary = await content_monitor_service.get_campaign_content_summary(1)

        # Assertions
        assert summary["total_posts"] == 0
        assert summary["verified_posts"] == 0
        assert summary["pending_posts"] == 0
        assert summary["rejected_posts"] == 0
        assert summary["platforms"] == {}
        assert summary["average_confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_detect_content_platform_error(
        self,
        content_monitor_service,
        sample_kol,
        sample_campaign
    ):
        """Test content detection with platform error."""
        # Mock social media service that raises exception
        mock_service = AsyncMock()
        mock_service.get_recent_posts.side_effect = Exception("API Error")
        content_monitor_service.social_media_factory.get_service.return_value = mock_service

        # Mock error recording
        content_monitor_service._record_platform_error = AsyncMock()

        # Execute
        result = await content_monitor_service.detect_new_content(sample_kol, sample_campaign)

        # Assertions
        assert len(result) == 0  # Should return empty list on error
        content_monitor_service._record_platform_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_content_existing_post(
        self,
        content_monitor_service,
        sample_kol,
        sample_campaign,
        sample_platform_post
    ):
        """Test content detection skipping existing posts."""
        # Mock social media service
        mock_service = AsyncMock()
        mock_service.get_recent_posts.return_value = [sample_platform_post]
        content_monitor_service.social_media_factory.get_service.return_value = mock_service

        # Mock existing post check - return existing post
        existing_post = ContentPost(id=1, platform_post_id=sample_platform_post.id)
        content_monitor_service._check_existing_post = AsyncMock(
            return_value=existing_post
        )

        # Execute
        result = await content_monitor_service.detect_new_content(sample_kol, sample_campaign)

        # Assertions
        assert len(result) == 0  # Should skip existing posts
        content_monitor_service._check_existing_post.assert_called_once_with(
            sample_platform_post.id, "instagram"
        )