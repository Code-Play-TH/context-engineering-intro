"""
Advanced Analytics Service

Comprehensive analytics service providing advanced insights, predictive analytics,
and business intelligence for KOL campaign management.
"""

import logging
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.content import ContentPost, ContentStats
from app.services.analytics.roi_calculator import ROICalculator
from app.services.analytics.analytics_engine import AnalyticsEngine
from app.schemas.analytics import (
    AdvancedAnalyticsRequest, PredictiveInsight, TrendAnalysis,
    CompetitiveAnalysis, AudienceInsight
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AdvancedAnalyticsService:
    """
    Advanced analytics service providing sophisticated analysis capabilities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.roi_calculator = ROICalculator()
        self.analytics_engine = AnalyticsEngine()

    async def generate_predictive_insights(
        self,
        entity_type: str,
        entity_ids: List[int],
        prediction_horizon_days: int = 30
    ) -> List[PredictiveInsight]:
        """
        Generate predictive insights using historical data and trend analysis.

        Args:
            entity_type: Type of entity (kol, campaign, content)
            entity_ids: List of entity IDs to analyze
            prediction_horizon_days: Days into the future to predict

        Returns:
            List of predictive insights
        """
        insights = []

        try:
            if entity_type.lower() == 'kol':
                insights.extend(await self._predict_kol_performance(entity_ids, prediction_horizon_days))
            elif entity_type.lower() == 'campaign':
                insights.extend(await self._predict_campaign_performance(entity_ids, prediction_horizon_days))

            # Add cross-entity insights
            insights.extend(await self._generate_cross_entity_predictions(entity_ids, prediction_horizon_days))

            return insights

        except Exception as e:
            logger.error(f"Predictive insights generation failed: {str(e)}")
            return []

    async def _predict_kol_performance(
        self,
        kol_ids: List[int],
        prediction_horizon: int
    ) -> List[PredictiveInsight]:
        """Predict KOL performance trends."""
        insights = []

        for kol_id in kol_ids:
            # Get historical performance data
            historical_data = await self._get_kol_historical_performance(kol_id)

            if len(historical_data) < 3:  # Need minimum data points
                continue

            # Analyze engagement trends
            engagement_trend = self._analyze_engagement_trend(historical_data)
            follower_growth_trend = self._analyze_follower_growth_trend(historical_data)

            # Generate predictions
            if engagement_trend['slope'] > 0.01:  # Positive trend
                insights.append(PredictiveInsight(
                    entity_type='kol',
                    entity_id=kol_id,
                    insight_type='engagement_growth',
                    prediction=f"Engagement rate expected to increase by {engagement_trend['projected_change']:.1%} over next {prediction_horizon} days",
                    confidence_score=engagement_trend['confidence'],
                    supporting_data=engagement_trend
                ))

            if follower_growth_trend['projected_growth'] > 1000:
                insights.append(PredictiveInsight(
                    entity_type='kol',
                    entity_id=kol_id,
                    insight_type='follower_growth',
                    prediction=f"Expected to gain {follower_growth_trend['projected_growth']:,.0f} followers over next {prediction_horizon} days",
                    confidence_score=follower_growth_trend['confidence'],
                    supporting_data=follower_growth_trend
                ))

        return insights

    async def _predict_campaign_performance(
        self,
        campaign_ids: List[int],
        prediction_horizon: int
    ) -> List[PredictiveInsight]:
        """Predict campaign performance and outcomes."""
        insights = []

        for campaign_id in campaign_ids:
            # Get campaign data
            stmt = select(Campaign).where(Campaign.id == campaign_id)
            result = await self.db.execute(stmt)
            campaign = result.scalar_one_or_none()

            if not campaign:
                continue

            # Analyze current performance trajectory
            performance_data = await self._get_campaign_performance_trajectory(campaign_id)

            if not performance_data:
                continue

            # ROI trajectory prediction
            roi_prediction = self._predict_roi_trajectory(performance_data)
            if roi_prediction['final_roi'] > 200:  # Expected to exceed 200% ROI
                insights.append(PredictiveInsight(
                    entity_type='campaign',
                    entity_id=campaign_id,
                    insight_type='roi_forecast',
                    prediction=f"Campaign projected to achieve {roi_prediction['final_roi']:.0f}% ROI by completion",
                    confidence_score=roi_prediction['confidence'],
                    supporting_data=roi_prediction
                ))

            # Content performance prediction
            content_prediction = await self._predict_content_performance(campaign_id)
            if content_prediction['expected_viral_posts'] > 0:
                insights.append(PredictiveInsight(
                    entity_type='campaign',
                    entity_id=campaign_id,
                    insight_type='viral_content_potential',
                    prediction=f"Expected {content_prediction['expected_viral_posts']} posts to achieve viral status",
                    confidence_score=content_prediction['confidence'],
                    supporting_data=content_prediction
                ))

        return insights

    async def generate_competitive_analysis(
        self,
        target_kols: List[int],
        competitor_kols: List[int],
        analysis_period_days: int = 90
    ) -> CompetitiveAnalysis:
        """
        Generate comprehensive competitive analysis.

        Args:
            target_kols: Target KOLs to analyze
            competitor_kols: Competitor KOLs for comparison
            analysis_period_days: Period for analysis

        Returns:
            Competitive analysis report
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=analysis_period_days)

        # Get performance data for both groups
        target_performance = await self._get_kol_group_performance(target_kols, start_date, end_date)
        competitor_performance = await self._get_kol_group_performance(competitor_kols, start_date, end_date)

        # Calculate competitive metrics
        market_share = self._calculate_market_share(target_performance, competitor_performance)
        performance_gaps = self._identify_performance_gaps(target_performance, competitor_performance)
        opportunity_areas = self._identify_opportunity_areas(target_performance, competitor_performance)

        # Generate strategic recommendations
        recommendations = self._generate_competitive_recommendations(
            market_share, performance_gaps, opportunity_areas
        )

        return CompetitiveAnalysis(
            analysis_date=datetime.utcnow(),
            target_kols=target_kols,
            competitor_kols=competitor_kols,
            analysis_period_days=analysis_period_days,
            market_share=market_share,
            performance_gaps=performance_gaps,
            opportunity_areas=opportunity_areas,
            recommendations=recommendations
        )

    async def generate_audience_insights(
        self,
        kol_ids: List[int],
        analysis_depth: str = 'comprehensive'
    ) -> List[AudienceInsight]:
        """
        Generate deep audience insights for KOLs.

        Args:
            kol_ids: List of KOL IDs to analyze
            analysis_depth: Depth of analysis (basic, standard, comprehensive)

        Returns:
            List of audience insights
        """
        insights = []

        for kol_id in kol_ids:
            # Get audience demographics (would integrate with social media APIs)
            audience_data = await self._get_kol_audience_data(kol_id)

            if not audience_data:
                continue

            # Demographic analysis
            demographic_insights = self._analyze_audience_demographics(audience_data)

            # Interest analysis
            interest_insights = self._analyze_audience_interests(audience_data)

            # Behavior patterns
            behavior_insights = self._analyze_audience_behavior(audience_data)

            # Engagement patterns
            engagement_insights = await self._analyze_audience_engagement_patterns(kol_id)

            insights.append(AudienceInsight(
                kol_id=kol_id,
                analysis_date=datetime.utcnow(),
                demographic_breakdown=demographic_insights,
                interest_categories=interest_insights,
                behavior_patterns=behavior_insights,
                engagement_patterns=engagement_insights,
                audience_quality_score=self._calculate_audience_quality_score(audience_data),
                growth_potential=self._assess_audience_growth_potential(audience_data)
            ))

        return insights

    async def generate_trend_analysis(
        self,
        metric_type: str,
        entity_ids: List[int],
        time_granularity: str = 'daily',
        analysis_period_days: int = 90
    ) -> TrendAnalysis:
        """
        Generate comprehensive trend analysis for specified metrics.

        Args:
            metric_type: Type of metric to analyze
            entity_ids: Entity IDs to include
            time_granularity: Time granularity (daily, weekly, monthly)
            analysis_period_days: Period for analysis

        Returns:
            Trend analysis results
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=analysis_period_days)

        # Get time series data
        time_series_data = await self._get_metric_time_series(
            metric_type, entity_ids, start_date, end_date, time_granularity
        )

        # Perform trend analysis
        trend_direction = self._calculate_trend_direction(time_series_data)
        trend_strength = self._calculate_trend_strength(time_series_data)
        seasonality = self._detect_seasonality_patterns(time_series_data)
        anomalies = self._detect_anomalies(time_series_data)

        # Generate forecasts
        forecast = self._generate_trend_forecast(time_series_data, forecast_periods=30)

        return TrendAnalysis(
            metric_type=metric_type,
            analysis_period=f"{start_date.date()} to {end_date.date()}",
            time_granularity=time_granularity,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            seasonality_detected=seasonality,
            anomalies_detected=anomalies,
            forecast=forecast,
            statistical_significance=self._calculate_statistical_significance(time_series_data)
        )

    async def generate_performance_attribution(
        self,
        campaign_id: int,
        attribution_model: str = 'linear'
    ) -> Dict[str, Any]:
        """
        Generate performance attribution analysis for campaign elements.

        Args:
            campaign_id: Campaign ID to analyze
            attribution_model: Attribution model to use

        Returns:
            Performance attribution analysis
        """
        # Get campaign content and performance data
        content_posts = await self._get_campaign_content_with_performance(campaign_id)

        if not content_posts:
            return {}

        # Calculate attribution for different factors
        kol_attribution = self._calculate_kol_attribution(content_posts, attribution_model)
        platform_attribution = self._calculate_platform_attribution(content_posts, attribution_model)
        content_type_attribution = self._calculate_content_type_attribution(content_posts, attribution_model)
        timing_attribution = self._calculate_timing_attribution(content_posts, attribution_model)

        return {
            'campaign_id': campaign_id,
            'attribution_model': attribution_model,
            'kol_attribution': kol_attribution,
            'platform_attribution': platform_attribution,
            'content_type_attribution': content_type_attribution,
            'timing_attribution': timing_attribution,
            'top_performing_combinations': self._identify_top_performing_combinations(content_posts)
        }

    # Helper methods for trend analysis
    def _analyze_engagement_trend(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement rate trends."""
        if len(historical_data) < 2:
            return {'slope': 0, 'confidence': 0, 'projected_change': 0}

        # Extract engagement rates over time
        engagement_rates = [data.get('engagement_rate', 0) for data in historical_data]
        time_points = list(range(len(engagement_rates)))

        # Simple linear regression
        slope = self._calculate_linear_trend(time_points, engagement_rates)
        confidence = min(1.0, len(historical_data) / 10)  # More data = higher confidence

        # Project change over next 30 days
        projected_change = slope * 30

        return {
            'slope': slope,
            'confidence': confidence,
            'projected_change': projected_change,
            'current_rate': engagement_rates[-1],
            'trend_direction': 'increasing' if slope > 0 else 'decreasing'
        }

    def _analyze_follower_growth_trend(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze follower growth trends."""
        if len(historical_data) < 2:
            return {'projected_growth': 0, 'confidence': 0}

        follower_counts = [data.get('total_followers', 0) for data in historical_data]

        # Calculate daily growth rate
        growth_rates = []
        for i in range(1, len(follower_counts)):
            if follower_counts[i-1] > 0:
                daily_growth = (follower_counts[i] - follower_counts[i-1]) / follower_counts[i-1]
                growth_rates.append(daily_growth)

        if not growth_rates:
            return {'projected_growth': 0, 'confidence': 0}

        avg_growth_rate = statistics.mean(growth_rates)
        current_followers = follower_counts[-1]

        # Project growth over next 30 days
        projected_growth = current_followers * avg_growth_rate * 30

        return {
            'projected_growth': max(0, projected_growth),
            'confidence': min(1.0, len(growth_rates) / 7),
            'avg_daily_growth_rate': avg_growth_rate,
            'current_followers': current_followers
        }

    def _calculate_linear_trend(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate linear trend slope."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)

        # Calculate slope using least squares
        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _calculate_trend_direction(self, time_series: List[Dict]) -> str:
        """Calculate overall trend direction."""
        if len(time_series) < 2:
            return 'insufficient_data'

        values = [point['value'] for point in time_series]
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = statistics.mean(first_half) if first_half else 0
        second_avg = statistics.mean(second_half) if second_half else 0

        if second_avg > first_avg * 1.05:  # 5% threshold
            return 'increasing'
        elif second_avg < first_avg * 0.95:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_trend_strength(self, time_series: List[Dict]) -> float:
        """Calculate trend strength (0-1 scale)."""
        if len(time_series) < 3:
            return 0.0

        values = [point['value'] for point in time_series]
        time_points = list(range(len(values)))

        # Calculate R-squared for trend line
        slope = self._calculate_linear_trend(time_points, values)
        if slope == 0:
            return 0.0

        # Calculate correlation coefficient
        try:
            correlation = abs(np.corrcoef(time_points, values)[0, 1])
            return min(1.0, correlation)
        except:
            return 0.0

    def _detect_seasonality_patterns(self, time_series: List[Dict]) -> Dict[str, Any]:
        """Detect seasonality patterns in time series."""
        if len(time_series) < 14:  # Need at least 2 weeks of data
            return {'detected': False}

        # Simple weekly seasonality detection
        values = [point['value'] for point in time_series]

        # Group by day of week (if daily data)
        if len(values) >= 14:
            weekly_patterns = {}
            for i, value in enumerate(values):
                day_of_week = i % 7
                if day_of_week not in weekly_patterns:
                    weekly_patterns[day_of_week] = []
                weekly_patterns[day_of_week].append(value)

            # Calculate variance across days
            day_averages = {day: statistics.mean(values) for day, values in weekly_patterns.items()}
            overall_avg = statistics.mean(list(day_averages.values()))

            # Check if any day is significantly different
            significant_variation = any(
                abs(avg - overall_avg) / overall_avg > 0.2
                for avg in day_averages.values()
                if overall_avg > 0
            )

            if significant_variation:
                return {
                    'detected': True,
                    'pattern_type': 'weekly',
                    'day_patterns': day_averages,
                    'strongest_day': max(day_averages, key=day_averages.get),
                    'weakest_day': min(day_averages, key=day_averages.get)
                }

        return {'detected': False}

    def _detect_anomalies(self, time_series: List[Dict]) -> List[Dict[str, Any]]:
        """Detect anomalies in time series data."""
        if len(time_series) < 7:
            return []

        values = [point['value'] for point in time_series]
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        if std_dev == 0:
            return []

        anomalies = []
        threshold = 2.5  # Standard deviations

        for i, point in enumerate(time_series):
            z_score = abs(point['value'] - mean_value) / std_dev
            if z_score > threshold:
                anomalies.append({
                    'index': i,
                    'date': point.get('date'),
                    'value': point['value'],
                    'z_score': z_score,
                    'type': 'spike' if point['value'] > mean_value else 'dip'
                })

        return anomalies

    def _generate_trend_forecast(self, time_series: List[Dict], forecast_periods: int) -> List[Dict]:
        """Generate forecast based on trend analysis."""
        if len(time_series) < 3:
            return []

        values = [point['value'] for point in time_series]
        time_points = list(range(len(values)))

        # Calculate trend
        slope = self._calculate_linear_trend(time_points, values)
        last_value = values[-1]

        # Generate forecast points
        forecast = []
        for i in range(1, forecast_periods + 1):
            predicted_value = last_value + (slope * i)
            # Add some uncertainty bounds
            uncertainty = abs(predicted_value * 0.1 * i)  # Increasing uncertainty over time

            forecast.append({
                'period': i,
                'predicted_value': max(0, predicted_value),
                'lower_bound': max(0, predicted_value - uncertainty),
                'upper_bound': predicted_value + uncertainty,
                'confidence': max(0.1, 1.0 - (i * 0.02))  # Decreasing confidence over time
            })

        return forecast

    # Placeholder methods for data retrieval (would integrate with actual data sources)
    async def _get_kol_historical_performance(self, kol_id: int) -> List[Dict]:
        """Get historical performance data for KOL."""
        # This would query the database for historical performance metrics
        return []

    async def _get_campaign_performance_trajectory(self, campaign_id: int) -> Dict:
        """Get campaign performance trajectory data."""
        return {}

    async def _get_kol_group_performance(self, kol_ids: List[int], start_date: datetime, end_date: datetime) -> Dict:
        """Get performance data for a group of KOLs."""
        return {}

    async def _get_kol_audience_data(self, kol_id: int) -> Dict:
        """Get audience data for KOL."""
        return {}

    async def _get_metric_time_series(self, metric_type: str, entity_ids: List[int], start_date: datetime, end_date: datetime, granularity: str) -> List[Dict]:
        """Get time series data for metric."""
        return []

    async def _get_campaign_content_with_performance(self, campaign_id: int) -> List[Dict]:
        """Get campaign content with performance data."""
        return []

    # Additional helper methods would be implemented here...
    def _calculate_statistical_significance(self, time_series: List[Dict]) -> float:
        """Calculate statistical significance of trend."""
        return 0.95  # Placeholder

    def _predict_roi_trajectory(self, performance_data: Dict) -> Dict:
        """Predict ROI trajectory."""
        return {'final_roi': 250, 'confidence': 0.8}

    async def _predict_content_performance(self, campaign_id: int) -> Dict:
        """Predict content performance."""
        return {'expected_viral_posts': 1, 'confidence': 0.7}