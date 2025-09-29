"""
Tests for ROI Calculator Service

Tests the comprehensive ROI calculation functionality with various scenarios.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.analytics.roi_calculator import ROICalculator, CostType, ValueMetric
from app.schemas.analytics import AttributionModel, ROIResult


@pytest.fixture
def roi_calculator():
    """ROI Calculator instance for testing."""
    return ROICalculator()


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        'campaign_id': 1,
        'industry': 'fashion',
        'kol_payments': [
            {'amount': 1000, 'currency_rate': 1.0},
            {'amount': 1500, 'currency_rate': 1.0}
        ],
        'product_costs': [
            {'value': 200},
            {'value': 150}
        ],
        'platform_costs': 100,
        'advertising_costs': 200,
        'management_fees': 150,
        'other_costs': [
            {'amount': 50}
        ],
        'content_posts': [
            {
                'platform': 'instagram',
                'likes': 1000,
                'comments': 100,
                'shares': 50,
                'saves': 75,
                'reach': 10000,
                'posted_at': datetime.utcnow()
            },
            {
                'platform': 'youtube',
                'likes': 500,
                'comments': 80,
                'shares': 30,
                'saves': 40,
                'reach': 15000,
                'posted_at': datetime.utcnow() - timedelta(days=1)
            }
        ],
        'direct_sales': [
            {'value': 2000},
            {'value': 1500}
        ],
        'leads_generated': 50,
        'average_lead_value': 10,
        'total_clicks': 200,
        'brand_mentions': 25,
        'hashtag_reach': 50000,
        'average_sentiment': 0.8
    }


class TestROICalculator:
    """Test cases for ROI Calculator."""

    def test_calculate_total_costs(self, roi_calculator, sample_campaign_data):
        """Test total cost calculation."""
        total_costs = roi_calculator._calculate_total_costs(sample_campaign_data)

        expected_costs = (
            1000 + 1500 +  # KOL payments
            200 + 150 +    # Product costs
            100 +          # Platform costs
            200 +          # Advertising costs
            150 +          # Management fees
            50             # Other costs
        )

        assert total_costs == Decimal(str(expected_costs))

    def test_calculate_total_costs_empty_data(self, roi_calculator):
        """Test total cost calculation with empty data."""
        empty_data = {}
        total_costs = roi_calculator._calculate_total_costs(empty_data)
        assert total_costs == Decimal('0.00')

    @pytest.mark.asyncio
    async def test_calculate_engagement_value_linear_attribution(
        self,
        roi_calculator,
        sample_campaign_data
    ):
        """Test engagement value calculation with linear attribution."""
        engagement_value = await roi_calculator._calculate_engagement_value(
            sample_campaign_data, AttributionModel.LINEAR
        )

        # Calculate expected value
        post1_value = (
            1000 * 0.01 +  # likes
            100 * 0.05 +   # comments
            50 * 0.10 +    # shares
            75 * 0.08      # saves
        ) * 1.0 * 0.5  # Instagram multiplier * linear attribution

        post2_value = (
            500 * 0.01 +   # likes
            80 * 0.05 +    # comments
            30 * 0.10 +    # shares
            40 * 0.08      # saves
        ) * 1.5 * 0.5  # YouTube multiplier * linear attribution

        expected_value = post1_value + post2_value

        assert abs(float(engagement_value) - expected_value) < 0.01

    def test_calculate_reach_value(self, roi_calculator, sample_campaign_data):
        """Test reach value calculation."""
        reach_value = roi_calculator._calculate_reach_value(sample_campaign_data)

        # Expected value based on fashion industry CPM (5.50)
        total_reach = 10000 + 15000  # 25,000 total reach
        expected_value = (25000 / 1000) * 5.50  # CPM calculation

        assert abs(float(reach_value) - expected_value) < 0.01

    def test_calculate_conversion_value(self, roi_calculator, sample_campaign_data):
        """Test conversion value calculation."""
        conversion_value = roi_calculator._calculate_conversion_value(sample_campaign_data)

        expected_value = (
            2000 + 1500 +     # Direct sales
            50 * 10 +         # Lead value
            200 * 0.15        # Click value
        )

        assert float(conversion_value) == expected_value

    def test_calculate_brand_awareness_value(self, roi_calculator, sample_campaign_data):
        """Test brand awareness value calculation."""
        awareness_value = roi_calculator._calculate_brand_awareness_value(sample_campaign_data)

        expected_value = (
            25 * 0.50 +           # Brand mentions
            (50000 / 1000) * 2.00 # Hashtag reach value
        )

        assert abs(float(awareness_value) - expected_value) < 0.01

    def test_calculate_sentiment_value(self, roi_calculator, sample_campaign_data):
        """Test sentiment value calculation."""
        sentiment_value = roi_calculator._calculate_sentiment_value(sample_campaign_data)

        # High sentiment (0.8) should generate positive value
        assert float(sentiment_value) > 0

    def test_calculate_sentiment_value_negative(self, roi_calculator, sample_campaign_data):
        """Test sentiment value with low sentiment."""
        sample_campaign_data['average_sentiment'] = 0.3  # Low sentiment
        sentiment_value = roi_calculator._calculate_sentiment_value(sample_campaign_data)

        # Low sentiment should result in zero or minimal value
        assert float(sentiment_value) == 0.0

    def test_calculate_roi_metrics(self, roi_calculator):
        """Test ROI metrics calculation."""
        total_costs = Decimal('1000.00')
        total_value = Decimal('2500.00')

        roi_metrics = roi_calculator._calculate_roi_metrics(total_costs, total_value)

        assert roi_metrics['roi_percentage'] == 150.0  # (2500-1000)/1000 * 100
        assert roi_metrics['roas'] == 2.5              # 2500/1000
        assert roi_metrics['profit_margin'] == 60.0    # (2500-1000)/2500 * 100
        assert roi_metrics['cost_effectiveness_ratio'] == 0.4  # 1000/2500

    def test_calculate_roi_metrics_zero_cost(self, roi_calculator):
        """Test ROI metrics with zero cost."""
        total_costs = Decimal('0.00')
        total_value = Decimal('1000.00')

        roi_metrics = roi_calculator._calculate_roi_metrics(total_costs, total_value)

        assert all(metric == 0.0 for metric in roi_metrics.values())

    def test_calculate_efficiency_metrics(self, roi_calculator, sample_campaign_data):
        """Test cost efficiency metrics calculation."""
        total_costs = Decimal('3000.00')

        efficiency_metrics = roi_calculator._calculate_efficiency_metrics(
            sample_campaign_data, total_costs
        )

        assert 'cpm' in efficiency_metrics
        assert 'cost_per_engagement' in efficiency_metrics
        assert 'cost_per_post' in efficiency_metrics
        assert 'engagement_rate' in efficiency_metrics

        # Cost per post should be total_costs / number_of_posts
        expected_cost_per_post = 3000.00 / 2  # 2 posts
        assert efficiency_metrics['cost_per_post'] == expected_cost_per_post

    def test_get_attribution_weight_linear(self, roi_calculator, sample_campaign_data):
        """Test linear attribution weight calculation."""
        post = sample_campaign_data['content_posts'][0]

        weight = roi_calculator._get_attribution_weight(
            post, sample_campaign_data, AttributionModel.LINEAR
        )

        # Linear attribution should give equal weight to all posts
        expected_weight = 1.0 / len(sample_campaign_data['content_posts'])
        assert weight == expected_weight

    def test_get_attribution_weight_first_touch(self, roi_calculator, sample_campaign_data):
        """Test first-touch attribution weight calculation."""
        # Sort posts by date to determine first post
        posts = sorted(
            sample_campaign_data['content_posts'],
            key=lambda p: p['posted_at']
        )
        first_post = posts[0]
        second_post = posts[1]

        first_weight = roi_calculator._get_attribution_weight(
            first_post, sample_campaign_data, AttributionModel.FIRST_TOUCH
        )
        second_weight = roi_calculator._get_attribution_weight(
            second_post, sample_campaign_data, AttributionModel.FIRST_TOUCH
        )

        assert first_weight == 1.0
        assert second_weight == 0.0

    def test_get_attribution_weight_last_touch(self, roi_calculator, sample_campaign_data):
        """Test last-touch attribution weight calculation."""
        # Sort posts by date to determine last post
        posts = sorted(
            sample_campaign_data['content_posts'],
            key=lambda p: p['posted_at'],
            reverse=True
        )
        last_post = posts[0]

        weight = roi_calculator._get_attribution_weight(
            last_post, sample_campaign_data, AttributionModel.LAST_TOUCH
        )

        assert weight == 1.0

    def test_calculate_benchmarks(self, roi_calculator, sample_campaign_data):
        """Test benchmark calculation."""
        roi_metrics = {'roi_percentage': 200.0}

        benchmarks = roi_calculator._calculate_benchmarks(sample_campaign_data, roi_metrics)

        assert benchmarks['industry'] == 'fashion'
        assert 'benchmark_roi_min' in benchmarks
        assert 'benchmark_roi_max' in benchmarks
        assert 'performance_vs_benchmark' in benchmarks

    def test_compare_to_benchmark_excellent(self, roi_calculator):
        """Test benchmark comparison with excellent performance."""
        roi_metrics = {'roi_percentage': 450.0}
        benchmark = {'roi_min': 150, 'roi_max': 400}

        result = roi_calculator._compare_to_benchmark(roi_metrics, benchmark)

        assert result == 'excellent'

    def test_compare_to_benchmark_good(self, roi_calculator):
        """Test benchmark comparison with good performance."""
        roi_metrics = {'roi_percentage': 250.0}
        benchmark = {'roi_min': 150, 'roi_max': 400}

        result = roi_calculator._compare_to_benchmark(roi_metrics, benchmark)

        assert result == 'good'

    def test_compare_to_benchmark_below_expectations(self, roi_calculator):
        """Test benchmark comparison with below expectations performance."""
        roi_metrics = {'roi_percentage': 50.0}
        benchmark = {'roi_min': 150, 'roi_max': 400}

        result = roi_calculator._compare_to_benchmark(roi_metrics, benchmark)

        assert result == 'below_expectations'

    def test_generate_roi_recommendations_excellent(self, roi_calculator):
        """Test ROI recommendations for excellent performance."""
        roi_metrics = {'roi_percentage': 350.0}
        efficiency_metrics = {'cpm': 4.0, 'engagement_rate': 3.5}
        benchmarks = {'performance_vs_benchmark': 'excellent', 'benchmark_cpm': 5.50}

        recommendations = roi_calculator._generate_roi_recommendations(
            roi_metrics, efficiency_metrics, benchmarks
        )

        # Should include scaling recommendation for excellent performance
        assert any('scaling' in rec.lower() for rec in recommendations)

    def test_generate_roi_recommendations_below_expectations(self, roi_calculator):
        """Test ROI recommendations for below expectations performance."""
        roi_metrics = {'roi_percentage': 50.0}
        efficiency_metrics = {'cpm': 8.0, 'engagement_rate': 1.0}
        benchmarks = {'performance_vs_benchmark': 'below_expectations', 'benchmark_cpm': 5.50}

        recommendations = roi_calculator._generate_roi_recommendations(
            roi_metrics, efficiency_metrics, benchmarks
        )

        # Should include optimization recommendations
        assert any('optimizing' in rec.lower() for rec in recommendations)
        assert any('cpm' in rec.lower() for rec in recommendations)
        assert any('engagement' in rec.lower() for rec in recommendations)

    def test_calculate_confidence_score_high_completeness(self, roi_calculator, sample_campaign_data):
        """Test confidence score calculation with complete data."""
        confidence = roi_calculator._calculate_confidence_score(sample_campaign_data)

        # Should have high confidence with complete data
        assert confidence > 0.8

    def test_calculate_confidence_score_low_completeness(self, roi_calculator):
        """Test confidence score calculation with incomplete data."""
        incomplete_data = {'campaign_id': 1}

        confidence = roi_calculator._calculate_confidence_score(incomplete_data)

        # Should have low confidence with incomplete data
        assert confidence <= 0.6

    @pytest.mark.asyncio
    async def test_calculate_campaign_roi_complete_workflow(
        self,
        roi_calculator,
        sample_campaign_data
    ):
        """Test complete ROI calculation workflow."""
        result = await roi_calculator.calculate_campaign_roi(
            sample_campaign_data,
            AttributionModel.LINEAR,
            include_soft_metrics=True
        )

        assert isinstance(result, ROIResult)
        assert result.campaign_id == 1
        assert result.attribution_model == AttributionModel.LINEAR
        assert result.total_investment > 0
        assert result.total_value_generated > 0
        assert 'roi_percentage' in result.roi_metrics
        assert 'cpm' in result.efficiency_metrics
        assert len(result.value_breakdown) > 0
        assert len(result.cost_breakdown) > 0
        assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_calculate_campaign_roi_without_soft_metrics(
        self,
        roi_calculator,
        sample_campaign_data
    ):
        """Test ROI calculation without soft metrics."""
        result = await roi_calculator.calculate_campaign_roi(
            sample_campaign_data,
            AttributionModel.LINEAR,
            include_soft_metrics=False
        )

        # Should not include brand awareness and sentiment values
        assert result.value_breakdown['brand_awareness_value'] == 0.0
        assert result.value_breakdown['sentiment_value'] == 0.0

    def test_generate_value_breakdown(self, roi_calculator, sample_campaign_data):
        """Test value breakdown generation."""
        import asyncio

        breakdown = asyncio.run(
            roi_calculator._generate_value_breakdown(
                sample_campaign_data, AttributionModel.LINEAR
            )
        )

        expected_keys = [
            'engagement_value',
            'reach_value',
            'conversion_value',
            'brand_awareness_value',
            'sentiment_value'
        ]

        for key in expected_keys:
            assert key in breakdown
            assert isinstance(breakdown[key], float)

    def test_generate_cost_breakdown(self, roi_calculator, sample_campaign_data):
        """Test cost breakdown generation."""
        breakdown = roi_calculator._generate_cost_breakdown(sample_campaign_data)

        expected_keys = [
            'kol_payments',
            'product_costs',
            'platform_costs',
            'advertising_costs',
            'management_fees',
            'other_costs'
        ]

        for key in expected_keys:
            assert key in breakdown
            assert isinstance(breakdown[key], (int, float))

        # Verify calculations
        assert breakdown['kol_payments'] == 2500.0  # 1000 + 1500
        assert breakdown['product_costs'] == 350.0  # 200 + 150