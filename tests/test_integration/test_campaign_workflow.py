"""
Integration Tests for Campaign Workflow

End-to-end tests for complete campaign management workflows.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.campaigns.collaboration_manager import CollaborationManager
from app.services.content_monitoring.content_monitor import ContentMonitorService
from app.services.analytics.roi_calculator import ROICalculator
from app.models.kol import KOL, KOLStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.content import ContentPost, VerificationStatus
from app.schemas.content_monitoring import PlatformPost, SocialPlatform


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def collaboration_manager(mock_db):
    """Collaboration manager with mocked dependencies."""
    return CollaborationManager(mock_db)


@pytest.fixture
def content_monitor(mock_db):
    """Content monitor with mocked dependencies."""
    with patch('app.services.content_monitoring.content_monitor.AIContentAnalyzer'), \
         patch('app.services.content_monitoring.content_monitor.SocialMediaServiceFactory'):
        return ContentMonitorService(mock_db)


@pytest.fixture
def roi_calculator():
    """ROI calculator instance."""
    return ROICalculator()


@pytest.fixture
def sample_kols():
    """Sample KOLs for testing."""
    return [
        KOL(
            id=1,
            name="Fashion Influencer A",
            email="fashion_a@example.com",
            social_media_accounts={
                "instagram": {"handle": "fashion_a", "verified": True},
                "youtube": {"handle": "fashion_a_yt", "verified": False}
            },
            niche=["fashion", "lifestyle"],
            status=KOLStatus.ACTIVE,
            follower_counts={"instagram": 100000, "youtube": 50000},
            engagement_rates={"instagram": 0.05, "youtube": 0.03}
        ),
        KOL(
            id=2,
            name="Beauty Influencer B",
            email="beauty_b@example.com",
            social_media_accounts={
                "instagram": {"handle": "beauty_b", "verified": True},
                "tiktok": {"handle": "beauty_b_tiktok", "verified": True}
            },
            niche=["beauty", "skincare"],
            status=KOLStatus.ACTIVE,
            follower_counts={"instagram": 75000, "tiktok": 120000},
            engagement_rates={"instagram": 0.06, "tiktok": 0.08}
        )
    ]


@pytest.fixture
def sample_campaign():
    """Sample campaign for testing."""
    return Campaign(
        id=1,
        name="Summer Beauty Campaign",
        description="Summer skincare and beauty products promotion",
        start_date=datetime.utcnow() - timedelta(days=7),
        end_date=datetime.utcnow() + timedelta(days=23),
        budget=Decimal('15000.00'),
        status=CampaignStatus.ACTIVE,
        target_kpis={
            "total_reach": 500000,
            "engagement_rate": 0.05,
            "roi_percentage": 250
        },
        required_keywords=["summer", "skincare", "beauty"],
        required_hashtags=["#summerskincare", "#beautyessentials"],
        brand_names=["BeautyBrand"],
        industry="beauty"
    )


class TestCampaignWorkflowIntegration:
    """Integration tests for complete campaign workflows."""

    @pytest.mark.asyncio
    async def test_complete_campaign_lifecycle(
        self,
        collaboration_manager,
        content_monitor,
        roi_calculator,
        sample_kols,
        sample_campaign,
        mock_db
    ):
        """Test complete campaign lifecycle from creation to completion."""

        # Phase 1: Campaign Setup and KOL Assignment
        await self._test_campaign_setup(
            collaboration_manager, sample_campaign, sample_kols, mock_db
        )

        # Phase 2: Content Detection and Monitoring
        detected_content = await self._test_content_detection(
            content_monitor, sample_kols, sample_campaign
        )

        # Phase 3: Performance Tracking and Analytics
        await self._test_performance_tracking(
            sample_campaign, detected_content
        )

        # Phase 4: ROI Calculation and Reporting
        await self._test_roi_calculation(
            roi_calculator, sample_campaign, detected_content
        )

        # Phase 5: Campaign Completion
        await self._test_campaign_completion(
            collaboration_manager, sample_campaign, mock_db
        )

    async def _test_campaign_setup(
        self,
        collaboration_manager,
        campaign,
        kols,
        mock_db
    ):
        """Test campaign setup and KOL assignment phase."""

        # Mock KOL assignment
        for kol in kols:
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = kol
            mock_db.execute.return_value = mock_result

            # Assign KOL to campaign
            assignment = await collaboration_manager.assign_kol_to_campaign(
                campaign_id=campaign.id,
                kol_id=kol.id,
                compensation=Decimal('2500.00'),
                deliverables_total=3
            )

            assert assignment.kol_id == kol.id
            assert assignment.campaign_id == campaign.id
            assert assignment.compensation == Decimal('2500.00')

    async def _test_content_detection(
        self,
        content_monitor,
        kols,
        campaign
    ):
        """Test content detection and monitoring phase."""
        detected_content = []

        # Mock social media posts
        sample_posts = [
            PlatformPost(
                id="insta_post_1",
                content="Loving this new #summerskincare routine! Perfect for the season. @BeautyBrand",
                url="https://instagram.com/p/sample1",
                hashtags=["summerskincare", "beautyessentials", "skincare"],
                mentions=["BeautyBrand"],
                created_at=datetime.utcnow() - timedelta(days=2),
                likes=1500,
                comments=80,
                shares=25
            ),
            PlatformPost(
                id="tiktok_post_1",
                content="Summer beauty tips! Try this amazing skincare routine #summerskincare",
                url="https://tiktok.com/@user/video/sample1",
                hashtags=["summerskincare", "beautytips"],
                mentions=[],
                created_at=datetime.utcnow() - timedelta(days=1),
                likes=3000,
                comments=120,
                shares=150
            )
        ]

        # Mock social media service
        with patch.object(content_monitor, '_check_platform_content') as mock_check:
            mock_content_posts = []
            for i, post in enumerate(sample_posts):
                content_post = ContentPost(
                    id=i + 1,
                    kol_id=kols[i % len(kols)].id,
                    campaign_id=campaign.id,
                    platform="instagram" if i == 0 else "tiktok",
                    platform_post_id=post.id,
                    url=post.url,
                    content=post.content,
                    hashtags=post.hashtags,
                    mentions=post.mentions,
                    posted_at=post.created_at,
                    detected_at=datetime.utcnow(),
                    verification_status=VerificationStatus.PENDING,
                    confidence_score=0.85
                )
                mock_content_posts.append(content_post)

            mock_check.return_value = mock_content_posts

            # Detect content for each KOL
            for kol in kols:
                posts = await content_monitor.detect_new_content(kol, campaign)
                detected_content.extend(posts)

        assert len(detected_content) > 0
        return detected_content

    async def _test_performance_tracking(self, campaign, detected_content):
        """Test performance tracking and statistics collection."""

        # Mock performance data collection
        for content_post in detected_content:
            # Simulate stats collection at different intervals
            stats_intervals = ["24hr", "3day", "5day"]

            for interval in stats_intervals:
                # Mock collecting statistics
                performance_data = {
                    "likes": content_post.platform_post_id == "insta_post_1" and 1500 or 3000,
                    "comments": content_post.platform_post_id == "insta_post_1" and 80 or 120,
                    "shares": content_post.platform_post_id == "insta_post_1" and 25 or 150,
                    "views": content_post.platform_post_id == "insta_post_1" and 15000 or 30000,
                    "reach": content_post.platform_post_id == "insta_post_1" and 12000 or 25000,
                    "engagement_rate": 0.08 if content_post.platform == "tiktok" else 0.05
                }

                assert performance_data["likes"] > 0
                assert performance_data["engagement_rate"] > 0

        # Verify campaign performance aggregation
        total_reach = sum(
            12000 if post.platform == "instagram" else 25000
            for post in detected_content
        )
        total_engagement = sum(
            1605 if post.platform == "instagram" else 3270  # likes + comments + shares
            for post in detected_content
        )

        assert total_reach > 0
        assert total_engagement > 0

    async def _test_roi_calculation(self, roi_calculator, campaign, detected_content):
        """Test ROI calculation and financial analysis."""

        # Prepare campaign data for ROI calculation
        campaign_data = {
            "campaign_id": campaign.id,
            "industry": campaign.industry,
            "kol_payments": [
                {"amount": 2500, "currency_rate": 1.0},
                {"amount": 2500, "currency_rate": 1.0}
            ],
            "product_costs": [
                {"value": 300},
                {"value": 250}
            ],
            "platform_costs": 200,
            "advertising_costs": 500,
            "management_fees": 300,
            "content_posts": [
                {
                    "platform": post.platform,
                    "likes": 1500 if post.platform == "instagram" else 3000,
                    "comments": 80 if post.platform == "instagram" else 120,
                    "shares": 25 if post.platform == "instagram" else 150,
                    "saves": 60 if post.platform == "instagram" else 90,
                    "reach": 12000 if post.platform == "instagram" else 25000,
                    "posted_at": post.posted_at
                }
                for post in detected_content
            ],
            "direct_sales": [
                {"value": 3500},
                {"value": 2800}
            ],
            "leads_generated": 45,
            "average_lead_value": 15,
            "total_clicks": 180,
            "brand_mentions": 30,
            "hashtag_reach": 75000,
            "average_sentiment": 0.75
        }

        # Calculate ROI
        roi_result = await roi_calculator.calculate_campaign_roi(
            campaign_data,
            include_soft_metrics=True
        )

        # Verify ROI calculation results
        assert roi_result.campaign_id == campaign.id
        assert roi_result.total_investment > 0
        assert roi_result.total_value_generated > 0
        assert roi_result.roi_metrics["roi_percentage"] is not None
        assert roi_result.confidence_score > 0.5

        # Verify expected ROI performance
        expected_roi = roi_result.roi_metrics["roi_percentage"]
        assert expected_roi > 100  # Should exceed 100% ROI for good campaign

    async def _test_campaign_completion(self, collaboration_manager, campaign, mock_db):
        """Test campaign completion and final analysis."""

        # Mock campaign update to completed status
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = campaign
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None

        # Update campaign status to completed
        campaign.status = CampaignStatus.COMPLETED
        campaign.end_date = datetime.utcnow()

        # Verify campaign completion
        assert campaign.status == CampaignStatus.COMPLETED
        assert campaign.end_date <= datetime.utcnow()

    @pytest.mark.asyncio
    async def test_multi_platform_content_workflow(
        self,
        content_monitor,
        sample_kols,
        sample_campaign
    ):
        """Test content detection workflow across multiple platforms."""

        # Mock different platform content
        platform_scenarios = [
            {
                "platform": "instagram",
                "posts": [
                    PlatformPost(
                        id="ig_1",
                        content="Summer glow with #summerskincare essentials! @BeautyBrand",
                        url="https://instagram.com/p/ig_1",
                        hashtags=["summerskincare", "glowup"],
                        mentions=["BeautyBrand"],
                        created_at=datetime.utcnow(),
                        likes=2000,
                        comments=150,
                        shares=40
                    )
                ]
            },
            {
                "platform": "tiktok",
                "posts": [
                    PlatformPost(
                        id="tt_1",
                        content="Get ready with me using summer beauty products! #summerskincare",
                        url="https://tiktok.com/@user/video/tt_1",
                        hashtags=["summerskincare", "grwm"],
                        mentions=[],
                        created_at=datetime.utcnow(),
                        likes=5000,
                        comments=300,
                        shares=200
                    )
                ]
            },
            {
                "platform": "youtube",
                "posts": [
                    PlatformPost(
                        id="yt_1",
                        content="Complete Summer Skincare Routine | BeautyBrand Review",
                        url="https://youtube.com/watch?v=yt_1",
                        hashtags=["summerskincare"],
                        mentions=["BeautyBrand"],
                        created_at=datetime.utcnow(),
                        likes=800,
                        comments=120,
                        shares=60
                    )
                ]
            }
        ]

        total_detected = 0

        for scenario in platform_scenarios:
            with patch.object(content_monitor, '_check_platform_content') as mock_check:
                mock_posts = []
                for post in scenario["posts"]:
                    content_post = ContentPost(
                        id=total_detected + 1,
                        kol_id=sample_kols[0].id,
                        campaign_id=sample_campaign.id,
                        platform=scenario["platform"],
                        platform_post_id=post.id,
                        url=post.url,
                        content=post.content,
                        verification_status=VerificationStatus.PENDING,
                        confidence_score=0.9
                    )
                    mock_posts.append(content_post)

                mock_check.return_value = mock_posts

                detected = await content_monitor.detect_new_content(
                    sample_kols[0], sample_campaign, [SocialPlatform(scenario["platform"])]
                )

                total_detected += len(detected)
                assert len(detected) == len(scenario["posts"])

        assert total_detected == 3  # Should detect content from all 3 platforms

    @pytest.mark.asyncio
    async def test_performance_attribution_workflow(
        self,
        roi_calculator,
        sample_campaign
    ):
        """Test performance attribution across different KOLs and content types."""

        # Create multi-KOL campaign data
        campaign_data = {
            "campaign_id": sample_campaign.id,
            "industry": "beauty",
            "kol_payments": [
                {"amount": 3000, "currency_rate": 1.0, "kol_id": 1},
                {"amount": 2500, "currency_rate": 1.0, "kol_id": 2}
            ],
            "content_posts": [
                {
                    "kol_id": 1,
                    "platform": "instagram",
                    "content_type": "product_review",
                    "likes": 2500,
                    "comments": 200,
                    "shares": 80,
                    "reach": 20000,
                    "posted_at": datetime.utcnow() - timedelta(days=5)
                },
                {
                    "kol_id": 1,
                    "platform": "youtube",
                    "content_type": "tutorial",
                    "likes": 1200,
                    "comments": 150,
                    "shares": 60,
                    "reach": 35000,
                    "posted_at": datetime.utcnow() - timedelta(days=3)
                },
                {
                    "kol_id": 2,
                    "platform": "tiktok",
                    "content_type": "unboxing",
                    "likes": 4000,
                    "comments": 300,
                    "shares": 200,
                    "reach": 50000,
                    "posted_at": datetime.utcnow() - timedelta(days=1)
                }
            ],
            "direct_sales": [
                {"value": 2000, "attributed_kol_id": 1},
                {"value": 1800, "attributed_kol_id": 2},
                {"value": 1500, "attributed_kol_id": 1}
            ]
        }

        # Test different attribution models
        attribution_models = [
            AttributionModel.LINEAR,
            AttributionModel.FIRST_TOUCH,
            AttributionModel.LAST_TOUCH,
            AttributionModel.TIME_DECAY
        ]

        results = {}
        for model in attribution_models:
            roi_result = await roi_calculator.calculate_campaign_roi(
                campaign_data, attribution_model=model
            )
            results[model] = roi_result

            # Verify each model produces valid results
            assert roi_result.total_value_generated > 0
            assert roi_result.roi_metrics["roi_percentage"] is not None

        # Compare attribution models
        linear_roi = results[AttributionModel.LINEAR].roi_metrics["roi_percentage"]
        first_touch_roi = results[AttributionModel.FIRST_TOUCH].roi_metrics["roi_percentage"]
        last_touch_roi = results[AttributionModel.LAST_TOUCH].roi_metrics["roi_percentage"]

        # All models should produce positive ROI for this scenario
        assert linear_roi > 0
        assert first_touch_roi > 0
        assert last_touch_roi > 0

    @pytest.mark.asyncio
    async def test_campaign_optimization_workflow(
        self,
        collaboration_manager,
        content_monitor,
        roi_calculator,
        sample_campaign,
        mock_db
    ):
        """Test campaign optimization based on performance data."""

        # Simulate underperforming campaign scenario
        underperforming_data = {
            "campaign_id": sample_campaign.id,
            "industry": "beauty",
            "kol_payments": [{"amount": 5000, "currency_rate": 1.0}],
            "content_posts": [
                {
                    "platform": "instagram",
                    "likes": 200,  # Low engagement
                    "comments": 10,
                    "shares": 2,
                    "reach": 5000,  # Low reach
                    "posted_at": datetime.utcnow()
                }
            ],
            "direct_sales": [{"value": 800}]  # Low sales
        }

        # Calculate initial ROI
        initial_roi = await roi_calculator.calculate_campaign_roi(underperforming_data)

        # Verify it's underperforming
        assert initial_roi.roi_metrics["roi_percentage"] < 100

        # Check recommendations
        recommendations = initial_roi.recommendations
        assert len(recommendations) > 0
        assert any("optimizing" in rec.lower() for rec in recommendations)

        # Simulate optimization actions
        optimized_data = underperforming_data.copy()
        optimized_data["content_posts"] = [
            {
                "platform": "instagram",
                "likes": 1500,  # Improved engagement
                "comments": 120,
                "shares": 45,
                "reach": 15000,  # Improved reach
                "posted_at": datetime.utcnow()
            },
            {
                "platform": "tiktok",  # Added new platform
                "likes": 3000,
                "comments": 200,
                "shares": 150,
                "reach": 25000,
                "posted_at": datetime.utcnow()
            }
        ]
        optimized_data["direct_sales"] = [
            {"value": 2500},  # Improved sales
            {"value": 1800}
        ]

        # Calculate optimized ROI
        optimized_roi = await roi_calculator.calculate_campaign_roi(optimized_data)

        # Verify improvement
        assert optimized_roi.roi_metrics["roi_percentage"] > initial_roi.roi_metrics["roi_percentage"]
        assert optimized_roi.roi_metrics["roi_percentage"] > 100  # Should now be profitable