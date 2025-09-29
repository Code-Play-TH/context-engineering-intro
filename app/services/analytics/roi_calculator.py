"""
ROI Calculator Service

Advanced ROI calculation service for KOL campaigns with multiple attribution models,
engagement value calculation, and comprehensive financial analysis.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from app.schemas.analytics import ROICalculationRequest, ROIResult, AttributionModel
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CostType(Enum):
    """Types of campaign costs."""
    KOL_PAYMENT = "kol_payment"
    PRODUCT_SEEDING = "product_seeding"
    CONTENT_CREATION = "content_creation"
    PLATFORM_FEES = "platform_fees"
    MANAGEMENT_FEES = "management_fees"
    ADVERTISING = "advertising"
    OTHER = "other"


class ValueMetric(Enum):
    """Value metrics for ROI calculation."""
    ENGAGEMENT_VALUE = "engagement_value"
    REACH_VALUE = "reach_value"
    CONVERSION_VALUE = "conversion_value"
    BRAND_AWARENESS_VALUE = "brand_awareness_value"
    SENTIMENT_VALUE = "sentiment_value"


class ROICalculator:
    """
    Advanced ROI calculation service with multiple models and comprehensive analysis.
    """

    def __init__(self):
        """Initialize ROI Calculator with default values and configurations."""
        self._load_default_values()

    def _load_default_values(self) -> None:
        """Load default values for calculations."""
        # Engagement value per interaction (in USD)
        self.engagement_values = {
            'like': 0.01,
            'comment': 0.05,
            'share': 0.10,
            'save': 0.08,
            'click': 0.15,
            'view': 0.001
        }

        # Platform-specific multipliers
        self.platform_multipliers = {
            'instagram': 1.0,
            'youtube': 1.5,
            'tiktok': 1.2,
            'twitter': 0.8,
            'facebook': 0.9,
            'linkedin': 2.0
        }

        # Industry benchmark CPMs (cost per mille/thousand impressions)
        self.industry_cpms = {
            'fashion': 5.50,
            'beauty': 6.00,
            'tech': 8.00,
            'food': 4.50,
            'travel': 7.00,
            'fitness': 5.00,
            'lifestyle': 5.50
        }

        # Conversion value estimates by content type
        self.conversion_multipliers = {
            'product_review': 2.0,
            'tutorial': 1.5,
            'unboxing': 1.8,
            'lifestyle': 1.2,
            'story_mention': 0.8
        }

    async def calculate_campaign_roi(
        self,
        campaign_data: Dict[str, Any],
        attribution_model: AttributionModel = AttributionModel.LINEAR,
        include_soft_metrics: bool = True
    ) -> ROIResult:
        """
        Calculate comprehensive ROI for a campaign.

        Args:
            campaign_data: Campaign data including costs, performance, and content
            attribution_model: Attribution model to use for value calculation
            include_soft_metrics: Whether to include brand awareness, sentiment value

        Returns:
            Comprehensive ROI analysis result
        """
        try:
            logger.info(f"Calculating ROI for campaign {campaign_data.get('campaign_id')}")

            # Calculate total costs
            total_costs = self._calculate_total_costs(campaign_data)

            # Calculate value generated
            total_value = await self._calculate_total_value(
                campaign_data, attribution_model, include_soft_metrics
            )

            # Calculate various ROI metrics
            roi_metrics = self._calculate_roi_metrics(total_costs, total_value)

            # Calculate cost efficiency metrics
            efficiency_metrics = self._calculate_efficiency_metrics(campaign_data, total_costs)

            # Generate value breakdown
            value_breakdown = await self._generate_value_breakdown(
                campaign_data, attribution_model
            )

            # Generate cost breakdown
            cost_breakdown = self._generate_cost_breakdown(campaign_data)

            # Calculate benchmarks and comparisons
            benchmarks = self._calculate_benchmarks(campaign_data, roi_metrics)

            # Generate recommendations
            recommendations = self._generate_roi_recommendations(
                roi_metrics, efficiency_metrics, benchmarks
            )

            return ROIResult(
                campaign_id=campaign_data.get('campaign_id'),
                calculation_date=datetime.utcnow(),
                attribution_model=attribution_model,
                total_investment=total_costs,
                total_value_generated=total_value,
                roi_metrics=roi_metrics,
                efficiency_metrics=efficiency_metrics,
                value_breakdown=value_breakdown,
                cost_breakdown=cost_breakdown,
                benchmarks=benchmarks,
                recommendations=recommendations,
                confidence_score=self._calculate_confidence_score(campaign_data)
            )

        except Exception as e:
            logger.error(f"ROI calculation failed: {str(e)}")
            raise

    def _calculate_total_costs(self, campaign_data: Dict[str, Any]) -> Decimal:
        """
        Calculate total campaign costs across all categories.

        Args:
            campaign_data: Campaign data

        Returns:
            Total campaign costs
        """
        total_costs = Decimal('0.00')

        # KOL payments
        kol_payments = campaign_data.get('kol_payments', [])
        for payment in kol_payments:
            amount = Decimal(str(payment.get('amount', 0)))
            currency_rate = Decimal(str(payment.get('currency_rate', 1.0)))
            total_costs += amount * currency_rate

        # Product seeding costs
        product_costs = campaign_data.get('product_costs', [])
        for cost in product_costs:
            total_costs += Decimal(str(cost.get('value', 0)))

        # Platform and advertising costs
        platform_costs = campaign_data.get('platform_costs', 0)
        advertising_costs = campaign_data.get('advertising_costs', 0)
        management_fees = campaign_data.get('management_fees', 0)

        total_costs += Decimal(str(platform_costs))
        total_costs += Decimal(str(advertising_costs))
        total_costs += Decimal(str(management_fees))

        # Other costs
        other_costs = campaign_data.get('other_costs', [])
        for cost in other_costs:
            total_costs += Decimal(str(cost.get('amount', 0)))

        return total_costs.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    async def _calculate_total_value(
        self,
        campaign_data: Dict[str, Any],
        attribution_model: AttributionModel,
        include_soft_metrics: bool
    ) -> Decimal:
        """
        Calculate total value generated by the campaign.

        Args:
            campaign_data: Campaign data
            attribution_model: Attribution model to use
            include_soft_metrics: Include soft metrics in calculation

        Returns:
            Total value generated
        """
        total_value = Decimal('0.00')

        # Engagement value
        engagement_value = await self._calculate_engagement_value(
            campaign_data, attribution_model
        )
        total_value += engagement_value

        # Reach and impression value
        reach_value = self._calculate_reach_value(campaign_data)
        total_value += reach_value

        # Direct conversion value (if available)
        conversion_value = self._calculate_conversion_value(campaign_data)
        total_value += conversion_value

        if include_soft_metrics:
            # Brand awareness value
            brand_awareness_value = self._calculate_brand_awareness_value(campaign_data)
            total_value += brand_awareness_value

            # Sentiment value
            sentiment_value = self._calculate_sentiment_value(campaign_data)
            total_value += sentiment_value

        return total_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    async def _calculate_engagement_value(
        self,
        campaign_data: Dict[str, Any],
        attribution_model: AttributionModel
    ) -> Decimal:
        """
        Calculate value from engagement metrics.

        Args:
            campaign_data: Campaign data
            attribution_model: Attribution model

        Returns:
            Engagement value
        """
        engagement_value = Decimal('0.00')
        content_posts = campaign_data.get('content_posts', [])

        for post in content_posts:
            platform = post.get('platform', 'instagram').lower()
            platform_multiplier = Decimal(str(self.platform_multipliers.get(platform, 1.0)))

            # Calculate engagement value by type
            likes = post.get('likes', 0)
            comments = post.get('comments', 0)
            shares = post.get('shares', 0)
            saves = post.get('saves', 0)

            post_value = Decimal('0.00')
            post_value += Decimal(str(likes)) * Decimal(str(self.engagement_values['like']))
            post_value += Decimal(str(comments)) * Decimal(str(self.engagement_values['comment']))
            post_value += Decimal(str(shares)) * Decimal(str(self.engagement_values['share']))
            post_value += Decimal(str(saves)) * Decimal(str(self.engagement_values['save']))

            # Apply platform multiplier
            post_value *= platform_multiplier

            # Apply attribution model weighting
            attribution_weight = self._get_attribution_weight(
                post, campaign_data, attribution_model
            )
            post_value *= Decimal(str(attribution_weight))

            engagement_value += post_value

        return engagement_value

    def _calculate_reach_value(self, campaign_data: Dict[str, Any]) -> Decimal:
        """
        Calculate value from reach and impressions.

        Args:
            campaign_data: Campaign data

        Returns:
            Reach value based on industry CPM benchmarks
        """
        reach_value = Decimal('0.00')
        content_posts = campaign_data.get('content_posts', [])

        # Get campaign industry for CPM benchmark
        industry = campaign_data.get('industry', 'lifestyle').lower()
        industry_cpm = Decimal(str(self.industry_cpms.get(industry, 5.50)))

        for post in content_posts:
            reach = post.get('reach', 0)
            if reach > 0:
                # Calculate value based on industry CPM
                value = (Decimal(str(reach)) / Decimal('1000')) * industry_cpm
                reach_value += value

        return reach_value

    def _calculate_conversion_value(self, campaign_data: Dict[str, Any]) -> Decimal:
        """
        Calculate direct conversion value.

        Args:
            campaign_data: Campaign data

        Returns:
            Direct conversion value
        """
        conversion_value = Decimal('0.00')

        # Direct sales attributed to campaign
        direct_sales = campaign_data.get('direct_sales', [])
        for sale in direct_sales:
            conversion_value += Decimal(str(sale.get('value', 0)))

        # Lead generation value
        leads = campaign_data.get('leads_generated', 0)
        lead_value = Decimal(str(campaign_data.get('average_lead_value', 0)))
        conversion_value += Decimal(str(leads)) * lead_value

        # Click-through value
        clicks = campaign_data.get('total_clicks', 0)
        click_value = Decimal(str(self.engagement_values['click']))
        conversion_value += Decimal(str(clicks)) * click_value

        return conversion_value

    def _calculate_brand_awareness_value(self, campaign_data: Dict[str, Any]) -> Decimal:
        """
        Calculate brand awareness value using proxy metrics.

        Args:
            campaign_data: Campaign data

        Returns:
            Brand awareness value
        """
        awareness_value = Decimal('0.00')

        # Brand mention value
        brand_mentions = campaign_data.get('brand_mentions', 0)
        mention_value = Decimal('0.50')  # $0.50 per brand mention
        awareness_value += Decimal(str(brand_mentions)) * mention_value

        # Share of voice improvement
        sov_improvement = campaign_data.get('share_of_voice_improvement', 0)
        if sov_improvement > 0:
            awareness_value += Decimal(str(sov_improvement)) * Decimal('100.00')

        # Hashtag performance value
        hashtag_reach = campaign_data.get('hashtag_reach', 0)
        if hashtag_reach > 0:
            hashtag_value = (Decimal(str(hashtag_reach)) / Decimal('1000')) * Decimal('2.00')
            awareness_value += hashtag_value

        return awareness_value

    def _calculate_sentiment_value(self, campaign_data: Dict[str, Any]) -> Decimal:
        """
        Calculate sentiment value impact.

        Args:
            campaign_data: Campaign data

        Returns:
            Sentiment value
        """
        sentiment_value = Decimal('0.00')

        # Average sentiment score (0-1 scale)
        avg_sentiment = campaign_data.get('average_sentiment', 0.5)

        # Sentiment improvement value
        if avg_sentiment > 0.7:  # Positive sentiment
            total_engagement = sum(
                post.get('likes', 0) + post.get('comments', 0) + post.get('shares', 0)
                for post in campaign_data.get('content_posts', [])
            )
            sentiment_multiplier = Decimal(str((avg_sentiment - 0.5) * 2))  # Scale to 0-1
            sentiment_value = Decimal(str(total_engagement)) * Decimal('0.02') * sentiment_multiplier

        return sentiment_value

    def _calculate_roi_metrics(
        self,
        total_costs: Decimal,
        total_value: Decimal
    ) -> Dict[str, float]:
        """
        Calculate various ROI metrics.

        Args:
            total_costs: Total campaign costs
            total_value: Total value generated

        Returns:
            Dictionary of ROI metrics
        """
        if total_costs == 0:
            return {
                'roi_percentage': 0.0,
                'roas': 0.0,
                'profit_margin': 0.0,
                'cost_effectiveness_ratio': 0.0
            }

        # ROI percentage: (Value - Cost) / Cost * 100
        roi_percentage = float(((total_value - total_costs) / total_costs) * Decimal('100'))

        # Return on Ad Spend: Value / Cost
        roas = float(total_value / total_costs)

        # Profit margin: (Value - Cost) / Value * 100
        profit_margin = float(((total_value - total_costs) / total_value) * Decimal('100')) if total_value > 0 else 0.0

        # Cost effectiveness ratio: Cost / Value
        cost_effectiveness_ratio = float(total_costs / total_value) if total_value > 0 else float('inf')

        return {
            'roi_percentage': round(roi_percentage, 2),
            'roas': round(roas, 2),
            'profit_margin': round(profit_margin, 2),
            'cost_effectiveness_ratio': round(cost_effectiveness_ratio, 4)
        }

    def _calculate_efficiency_metrics(
        self,
        campaign_data: Dict[str, Any],
        total_costs: Decimal
    ) -> Dict[str, float]:
        """
        Calculate cost efficiency metrics.

        Args:
            campaign_data: Campaign data
            total_costs: Total campaign costs

        Returns:
            Dictionary of efficiency metrics
        """
        content_posts = campaign_data.get('content_posts', [])

        if not content_posts:
            return {}

        # Calculate totals
        total_reach = sum(post.get('reach', 0) for post in content_posts)
        total_engagement = sum(
            post.get('likes', 0) + post.get('comments', 0) + post.get('shares', 0)
            for post in content_posts
        )
        total_posts = len(content_posts)

        efficiency_metrics = {}

        # CPM (Cost Per Mille/Thousand impressions)
        if total_reach > 0:
            cpm = float(total_costs / (Decimal(str(total_reach)) / Decimal('1000')))
            efficiency_metrics['cpm'] = round(cpm, 2)

        # Cost Per Engagement
        if total_engagement > 0:
            cpe = float(total_costs / Decimal(str(total_engagement)))
            efficiency_metrics['cost_per_engagement'] = round(cpe, 4)

        # Cost Per Post
        cost_per_post = float(total_costs / Decimal(str(total_posts)))
        efficiency_metrics['cost_per_post'] = round(cost_per_post, 2)

        # Engagement Rate
        if total_reach > 0:
            engagement_rate = (total_engagement / total_reach) * 100
            efficiency_metrics['engagement_rate'] = round(engagement_rate, 2)

        return efficiency_metrics

    def _get_attribution_weight(
        self,
        post: Dict[str, Any],
        campaign_data: Dict[str, Any],
        attribution_model: AttributionModel
    ) -> float:
        """
        Get attribution weight based on model and post timing.

        Args:
            post: Post data
            campaign_data: Campaign data
            attribution_model: Attribution model

        Returns:
            Attribution weight (0.0 to 1.0)
        """
        if attribution_model == AttributionModel.FIRST_TOUCH:
            # First post gets full attribution
            first_post = min(
                campaign_data.get('content_posts', []),
                key=lambda p: p.get('posted_at', datetime.max)
            )
            return 1.0 if post == first_post else 0.0

        elif attribution_model == AttributionModel.LAST_TOUCH:
            # Last post gets full attribution
            last_post = max(
                campaign_data.get('content_posts', []),
                key=lambda p: p.get('posted_at', datetime.min)
            )
            return 1.0 if post == last_post else 0.0

        elif attribution_model == AttributionModel.LINEAR:
            # Equal attribution across all posts
            return 1.0 / len(campaign_data.get('content_posts', [1]))

        elif attribution_model == AttributionModel.TIME_DECAY:
            # More recent posts get higher attribution
            post_date = post.get('posted_at', datetime.min)
            campaign_end = campaign_data.get('end_date', datetime.utcnow())
            days_from_end = (campaign_end - post_date).days
            # Exponential decay with half-life of 7 days
            return 0.5 ** (days_from_end / 7)

        else:  # Position-based or default
            posts = campaign_data.get('content_posts', [])
            post_count = len(posts)

            if post_count == 1:
                return 1.0
            elif post_count == 2:
                return 0.5  # Equal split for first and last
            else:
                # 40% first, 40% last, 20% distributed among middle posts
                sorted_posts = sorted(posts, key=lambda p: p.get('posted_at', datetime.min))
                if post == sorted_posts[0] or post == sorted_posts[-1]:
                    return 0.4
                else:
                    return 0.2 / (post_count - 2)

    async def _generate_value_breakdown(
        self,
        campaign_data: Dict[str, Any],
        attribution_model: AttributionModel
    ) -> Dict[str, float]:
        """Generate detailed value breakdown."""
        engagement_value = await self._calculate_engagement_value(campaign_data, attribution_model)
        reach_value = self._calculate_reach_value(campaign_data)
        conversion_value = self._calculate_conversion_value(campaign_data)
        brand_awareness_value = self._calculate_brand_awareness_value(campaign_data)
        sentiment_value = self._calculate_sentiment_value(campaign_data)

        return {
            'engagement_value': float(engagement_value),
            'reach_value': float(reach_value),
            'conversion_value': float(conversion_value),
            'brand_awareness_value': float(brand_awareness_value),
            'sentiment_value': float(sentiment_value)
        }

    def _generate_cost_breakdown(self, campaign_data: Dict[str, Any]) -> Dict[str, float]:
        """Generate detailed cost breakdown."""
        kol_payments = sum(
            payment.get('amount', 0) * payment.get('currency_rate', 1.0)
            for payment in campaign_data.get('kol_payments', [])
        )

        product_costs = sum(
            cost.get('value', 0)
            for cost in campaign_data.get('product_costs', [])
        )

        return {
            'kol_payments': kol_payments,
            'product_costs': product_costs,
            'platform_costs': campaign_data.get('platform_costs', 0),
            'advertising_costs': campaign_data.get('advertising_costs', 0),
            'management_fees': campaign_data.get('management_fees', 0),
            'other_costs': sum(
                cost.get('amount', 0)
                for cost in campaign_data.get('other_costs', [])
            )
        }

    def _calculate_benchmarks(
        self,
        campaign_data: Dict[str, Any],
        roi_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate industry benchmarks and comparisons."""
        industry = campaign_data.get('industry', 'lifestyle').lower()

        # Industry benchmark ROI ranges
        industry_benchmarks = {
            'fashion': {'roi_min': 150, 'roi_max': 400, 'avg_cpm': 5.50},
            'beauty': {'roi_min': 200, 'roi_max': 500, 'avg_cpm': 6.00},
            'tech': {'roi_min': 180, 'roi_max': 350, 'avg_cpm': 8.00},
            'food': {'roi_min': 120, 'roi_max': 300, 'avg_cpm': 4.50},
            'travel': {'roi_min': 160, 'roi_max': 380, 'avg_cpm': 7.00},
            'lifestyle': {'roi_min': 140, 'roi_max': 320, 'avg_cpm': 5.50}
        }

        benchmark = industry_benchmarks.get(industry, industry_benchmarks['lifestyle'])

        return {
            'industry': industry,
            'benchmark_roi_min': benchmark['roi_min'],
            'benchmark_roi_max': benchmark['roi_max'],
            'benchmark_cpm': benchmark['avg_cpm'],
            'performance_vs_benchmark': self._compare_to_benchmark(roi_metrics, benchmark)
        }

    def _compare_to_benchmark(
        self,
        roi_metrics: Dict[str, float],
        benchmark: Dict[str, float]
    ) -> str:
        """Compare performance to industry benchmark."""
        roi_percentage = roi_metrics.get('roi_percentage', 0)

        if roi_percentage >= benchmark['roi_max']:
            return 'excellent'
        elif roi_percentage >= benchmark['roi_min']:
            return 'good'
        elif roi_percentage >= benchmark['roi_min'] * 0.7:
            return 'fair'
        else:
            return 'below_expectations'

    def _generate_roi_recommendations(
        self,
        roi_metrics: Dict[str, float],
        efficiency_metrics: Dict[str, float],
        benchmarks: Dict[str, Any]
    ) -> List[str]:
        """Generate ROI optimization recommendations."""
        recommendations = []

        roi_percentage = roi_metrics.get('roi_percentage', 0)
        performance = benchmarks.get('performance_vs_benchmark', 'fair')

        if performance == 'below_expectations':
            recommendations.append("Consider optimizing KOL selection criteria and content strategy")
            recommendations.append("Review cost structure and negotiate better rates with top-performing KOLs")

        cpm = efficiency_metrics.get('cpm', 0)
        benchmark_cpm = benchmarks.get('benchmark_cpm', 5.50)

        if cpm > benchmark_cpm * 1.2:
            recommendations.append(f"CPM of ${cpm:.2f} is above industry average - focus on improving reach efficiency")

        engagement_rate = efficiency_metrics.get('engagement_rate', 0)
        if engagement_rate < 2.0:
            recommendations.append("Low engagement rate - consider content format optimization and posting time analysis")

        if roi_percentage > 300:
            recommendations.append("Excellent ROI achieved - consider scaling successful tactics and KOL partnerships")

        return recommendations

    def _calculate_confidence_score(self, campaign_data: Dict[str, Any]) -> float:
        """Calculate confidence score for ROI calculation."""
        score = 0.5  # Base confidence

        # Data completeness factors
        if campaign_data.get('kol_payments'):
            score += 0.1
        if campaign_data.get('content_posts'):
            score += 0.2
        if campaign_data.get('direct_sales'):
            score += 0.1
        if campaign_data.get('platform_costs') is not None:
            score += 0.05
        if campaign_data.get('brand_mentions', 0) > 0:
            score += 0.05

        return min(1.0, score)