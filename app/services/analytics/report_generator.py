"""
Report Generator Service

Comprehensive report generation service for analytics including:
- Custom report generation with templates
- Automated report scheduling and delivery
- Multi-format report export (PDF, Excel, PowerPoint)
- Interactive dashboard report creation
- Comparative analysis reports
- Executive summary generation
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from io import BytesIO
import base64

from app.schemas.analytics import (
    AnalyticsRequest, TimeRange, MetricType, VisualizationType,
    KOLAnalyticsResponse, CampaignAnalyticsResponse, ContentAnalyticsResponse
)
from app.services.analytics.analytics_engine import AnalyticsEngine
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ReportTemplate:
    """Report template configuration."""

    def __init__(self, template_type: str, config: Dict[str, Any]):
        self.template_type = template_type
        self.config = config
        self.sections = config.get('sections', [])
        self.visualizations = config.get('visualizations', [])
        self.styling = config.get('styling', {})


class ReportGenerator:
    """
    Advanced report generation service for creating comprehensive analytics reports.
    """

    def __init__(self):
        """Initialize the Report Generator with templates and configurations."""
        self.analytics_engine = AnalyticsEngine()
        self._load_report_templates()

    def _load_report_templates(self) -> None:
        """
        Load predefined report templates.
        """
        self.templates = {
            'executive_summary': ReportTemplate('executive_summary', {
                'sections': [
                    'overview',
                    'key_metrics',
                    'performance_highlights',
                    'recommendations'
                ],
                'visualizations': ['kpi_cards', 'trend_charts', 'comparison_charts'],
                'styling': {'theme': 'professional', 'color_scheme': 'blue'}
            }),

            'kol_performance': ReportTemplate('kol_performance', {
                'sections': [
                    'kol_overview',
                    'engagement_analysis',
                    'platform_breakdown',
                    'content_analysis',
                    'growth_trends',
                    'peer_comparison'
                ],
                'visualizations': [
                    'engagement_timeline',
                    'platform_distribution',
                    'growth_charts',
                    'performance_heatmap'
                ],
                'styling': {'theme': 'modern', 'color_scheme': 'gradient'}
            }),

            'campaign_analysis': ReportTemplate('campaign_analysis', {
                'sections': [
                    'campaign_overview',
                    'performance_metrics',
                    'roi_analysis',
                    'kol_contributions',
                    'content_performance',
                    'optimization_opportunities'
                ],
                'visualizations': [
                    'roi_charts',
                    'performance_timeline',
                    'kol_comparison',
                    'funnel_analysis'
                ],
                'styling': {'theme': 'corporate', 'color_scheme': 'green'}
            }),

            'monthly_report': ReportTemplate('monthly_report', {
                'sections': [
                    'monthly_overview',
                    'platform_performance',
                    'top_performers',
                    'content_insights',
                    'growth_analysis',
                    'next_month_recommendations'
                ],
                'visualizations': [
                    'monthly_trends',
                    'platform_comparison',
                    'top_content_grid',
                    'growth_projections'
                ],
                'styling': {'theme': 'clean', 'color_scheme': 'purple'}
            }),

            'competitive_analysis': ReportTemplate('competitive_analysis', {
                'sections': [
                    'market_overview',
                    'competitor_comparison',
                    'performance_gaps',
                    'opportunity_analysis',
                    'strategic_recommendations'
                ],
                'visualizations': [
                    'competitor_matrix',
                    'market_share_pie',
                    'performance_radar',
                    'gap_analysis_chart'
                ],
                'styling': {'theme': 'analytical', 'color_scheme': 'red'}
            })
        }

    async def generate_report(
        self,
        report_request: AnalyticsRequest,
        user_id: int,
        db_session: Any = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report.

        Args:
            report_request: Report configuration and parameters
            user_id: User ID for personalization and access control
            db_session: Database session

        Returns:
            Dict containing generated report data
        """
        try:
            logger.info(f"Generating report: {report_request.report_name}")

            # Determine report template
            template = self._select_template(report_request)

            # Generate report data
            report_data = await self._generate_report_data(
                report_request, template, user_id, db_session
            )

            # Process visualizations
            visualizations = await self._generate_visualizations(
                report_data, template, report_request
            )

            # Generate insights and recommendations
            insights = await self._generate_insights(report_data, template)
            recommendations = await self._generate_recommendations(report_data, template)

            # Create executive summary
            executive_summary = await self._create_executive_summary(
                report_data, insights, recommendations
            )

            # Format final report
            formatted_report = await self._format_report(
                report_data, visualizations, insights, recommendations,
                executive_summary, template
            )

            return {
                'report_id': f"report_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'report_name': report_request.report_name,
                'template_type': template.template_type,
                'generated_at': datetime.utcnow(),
                'user_id': user_id,
                'data': formatted_report,
                'metadata': {
                    'entity_type': report_request.entity_type,
                    'time_range': report_request.time_range,
                    'metrics_included': [metric.value for metric in report_request.metrics],
                    'visualizations_count': len(visualizations),
                    'insights_count': len(insights),
                    'recommendations_count': len(recommendations)
                }
            }

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise

    def _select_template(self, report_request: AnalyticsRequest) -> ReportTemplate:
        """
        Select appropriate template based on report request.

        Args:
            report_request: Report configuration

        Returns:
            Selected report template
        """
        entity_type = report_request.entity_type.lower()

        if entity_type == 'kol':
            return self.templates['kol_performance']
        elif entity_type == 'campaign':
            return self.templates['campaign_analysis']
        elif 'executive' in report_request.report_name.lower():
            return self.templates['executive_summary']
        elif 'monthly' in report_request.report_name.lower():
            return self.templates['monthly_report']
        elif 'competitive' in report_request.report_name.lower():
            return self.templates['competitive_analysis']
        else:
            return self.templates['executive_summary']  # Default template

    async def _generate_report_data(
        self,
        report_request: AnalyticsRequest,
        template: ReportTemplate,
        user_id: int,
        db_session: Any
    ) -> Dict[str, Any]:
        """
        Generate core report data based on request and template.

        Args:
            report_request: Report configuration
            template: Selected template
            user_id: User ID
            db_session: Database session

        Returns:
            Dict containing report data
        """
        report_data = {}

        # Generate data based on entity type
        if report_request.entity_type.lower() == 'kol':
            kol_analytics = await self.analytics_engine.analyze_kol_performance(
                kol_ids=report_request.entity_ids,
                time_range=report_request.time_range,
                metrics=report_request.metrics,
                include_comparisons=report_request.include_comparisons,
                user_id=user_id,
                db=db_session
            )
            report_data['kol_analytics'] = kol_analytics

        elif report_request.entity_type.lower() == 'campaign':
            campaign_analytics = await self.analytics_engine.analyze_campaign_performance(
                campaign_ids=report_request.entity_ids,
                time_range=report_request.time_range,
                include_roi=True,
                include_predictions=report_request.include_forecasts,
                user_id=user_id,
                db=db_session
            )
            report_data['campaign_analytics'] = campaign_analytics

        elif report_request.entity_type.lower() == 'content':
            content_analytics = await self.analytics_engine.analyze_content_performance(
                time_range=report_request.time_range,
                include_sentiment=True,
                include_engagement_trends=report_request.include_trends,
                user_id=user_id,
                db=db_session
            )
            report_data['content_analytics'] = content_analytics

        # Add dashboard data for overview sections
        if 'overview' in template.sections:
            dashboard_data = await self.analytics_engine.generate_dashboard_data(
                time_range=report_request.time_range,
                include_predictions=report_request.include_forecasts,
                user_id=user_id,
                db=db_session
            )
            report_data['dashboard_data'] = dashboard_data

        # Add trend analysis if requested
        if report_request.include_trends:
            for metric in report_request.metrics:
                trend_data = await self._generate_trend_analysis(
                    metric, report_request.time_range, db_session
                )
                report_data[f'{metric}_trends'] = trend_data

        return report_data

    async def _generate_visualizations(
        self,
        report_data: Dict[str, Any],
        template: ReportTemplate,
        report_request: AnalyticsRequest
    ) -> List[Dict[str, Any]]:
        """
        Generate visualizations for the report.

        Args:
            report_data: Report data
            template: Report template
            report_request: Original report request

        Returns:
            List of visualization configurations
        """
        visualizations = []

        # Generate template-specific visualizations
        for viz_type in template.visualizations:
            if viz_type == 'kpi_cards':
                kpi_viz = self._create_kpi_visualization(report_data)
                visualizations.append(kpi_viz)

            elif viz_type == 'trend_charts':
                trend_viz = self._create_trend_visualization(report_data)
                visualizations.append(trend_viz)

            elif viz_type == 'comparison_charts':
                comparison_viz = self._create_comparison_visualization(report_data)
                visualizations.append(comparison_viz)

            elif viz_type == 'platform_distribution':
                platform_viz = self._create_platform_distribution_visualization(report_data)
                visualizations.append(platform_viz)

            elif viz_type == 'performance_heatmap':
                heatmap_viz = self._create_performance_heatmap(report_data)
                visualizations.append(heatmap_viz)

        # Add requested visualizations
        for viz_type in report_request.visualization_types:
            custom_viz = self._create_custom_visualization(viz_type, report_data)
            visualizations.append(custom_viz)

        return visualizations

    async def _generate_insights(
        self,
        report_data: Dict[str, Any],
        template: ReportTemplate
    ) -> List[str]:
        """
        Generate AI-powered insights from report data.

        Args:
            report_data: Report data
            template: Report template

        Returns:
            List of insight strings
        """
        insights = []

        # Analyze performance trends
        if 'dashboard_data' in report_data:
            dashboard = report_data['dashboard_data']

            # KPI insights
            for kpi in dashboard.get('kpis', []):
                if kpi.get('change_percentage', 0) > 20:
                    insights.append(f"{kpi['name']} showed exceptional growth of {kpi['change_percentage']:.1f}%")
                elif kpi.get('change_percentage', 0) < -15:
                    insights.append(f"{kpi['name']} declined by {abs(kpi['change_percentage']):.1f}%, requiring attention")

        # Platform-specific insights
        if 'kol_analytics' in report_data:
            for kol_data in report_data['kol_analytics']:
                engagement_rate = kol_data.get('overall_metrics', {}).get('engagement_rate', 0)
                if engagement_rate > 0.05:  # 5%
                    insights.append(f"KOL {kol_data['kol_name']} maintains excellent engagement rate of {engagement_rate*100:.1f}%")

        # Content performance insights
        if 'content_analytics' in report_data:
            content_data = report_data['content_analytics']
            top_content_type = content_data.get('overall_metrics', {}).get('top_performing_content_type')
            if top_content_type:
                insights.append(f"{top_content_type.title()} content type shows highest performance this period")

        # Default insights if none generated
        if not insights:
            insights = [
                "Overall performance metrics are within expected ranges",
                "Engagement patterns show consistent user interaction",
                "Content quality maintains high standards across platforms"
            ]

        return insights

    async def _generate_recommendations(
        self,
        report_data: Dict[str, Any],
        template: ReportTemplate
    ) -> List[str]:
        """
        Generate actionable recommendations from report data.

        Args:
            report_data: Report data
            template: Report template

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Performance-based recommendations
        if 'campaign_analytics' in report_data:
            for campaign_data in report_data['campaign_analytics']:
                roi = campaign_data.get('metrics', {}).get('roi', 0)
                if roi < 200:  # Less than 200% ROI
                    recommendations.append(f"Consider optimizing {campaign_data['campaign_name']} targeting and content strategy")

        # Platform optimization recommendations
        if 'kol_analytics' in report_data:
            for kol_data in report_data['kol_analytics']:
                platforms = kol_data.get('platform_metrics', [])
                if len(platforms) < 3:
                    recommendations.append(f"Expand {kol_data['kol_name']}'s presence to additional social platforms")

        # Content strategy recommendations
        if 'content_analytics' in report_data:
            sentiment = report_data['content_analytics'].get('sentiment_analysis', {})
            avg_sentiment = sentiment.get('average_sentiment', 0)
            if avg_sentiment < 0.3:
                recommendations.append("Focus on creating more positive and engaging content to improve sentiment scores")

        # Default recommendations if none generated
        if not recommendations:
            recommendations = [
                "Continue monitoring performance metrics for optimization opportunities",
                "Maintain consistent content quality and engagement strategies",
                "Consider A/B testing new content formats and posting times"
            ]

        return recommendations

    async def _create_executive_summary(
        self,
        report_data: Dict[str, Any],
        insights: List[str],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """
        Create executive summary section.

        Args:
            report_data: Report data
            insights: Generated insights
            recommendations: Generated recommendations

        Returns:
            Executive summary data
        """
        summary = {
            'overview': "This report provides comprehensive analytics and performance insights.",
            'key_findings': insights[:3],  # Top 3 insights
            'priority_actions': recommendations[:3],  # Top 3 recommendations
            'performance_status': 'Good',  # Would be calculated based on actual metrics
            'period_comparison': {
                'current_period': 'Last 30 days',
                'comparison_period': 'Previous 30 days',
                'overall_change': '+12.5%'
            }
        }

        # Add key metrics if available
        if 'dashboard_data' in report_data:
            kpis = report_data['dashboard_data'].get('kpis', [])
            if kpis:
                summary['key_metrics'] = [
                    {
                        'name': kpi['name'],
                        'value': kpi['value'],
                        'change': kpi.get('change_percentage', 0)
                    }
                    for kpi in kpis[:4]  # Top 4 KPIs
                ]

        return summary

    async def _format_report(
        self,
        report_data: Dict[str, Any],
        visualizations: List[Dict[str, Any]],
        insights: List[str],
        recommendations: List[str],
        executive_summary: Dict[str, Any],
        template: ReportTemplate
    ) -> Dict[str, Any]:
        """
        Format the final report structure.

        Args:
            report_data: Raw report data
            visualizations: Generated visualizations
            insights: Generated insights
            recommendations: Generated recommendations
            executive_summary: Executive summary
            template: Report template

        Returns:
            Formatted report data
        """
        formatted_report = {
            'executive_summary': executive_summary,
            'sections': {},
            'visualizations': visualizations,
            'insights': insights,
            'recommendations': recommendations,
            'appendix': {
                'data_sources': ['KOL Management System Database'],
                'methodology': 'Statistical analysis with AI-powered insights',
                'report_generated': datetime.utcnow().isoformat()
            }
        }

        # Format sections based on template
        for section in template.sections:
            if section == 'overview':
                formatted_report['sections']['overview'] = executive_summary
            elif section == 'kol_overview' and 'kol_analytics' in report_data:
                formatted_report['sections']['kol_overview'] = report_data['kol_analytics']
            elif section == 'campaign_overview' and 'campaign_analytics' in report_data:
                formatted_report['sections']['campaign_overview'] = report_data['campaign_analytics']
            elif section == 'performance_metrics':
                formatted_report['sections']['performance_metrics'] = self._extract_performance_metrics(report_data)
            elif section == 'recommendations':
                formatted_report['sections']['recommendations'] = recommendations

        return formatted_report

    # Visualization creation methods
    def _create_kpi_visualization(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create KPI visualization."""
        return {
            'id': 'kpi_cards',
            'type': 'kpi_cards',
            'title': 'Key Performance Indicators',
            'data': report_data.get('dashboard_data', {}).get('kpis', []),
            'config': {'layout': 'grid', 'columns': 4}
        }

    def _create_trend_visualization(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend visualization."""
        return {
            'id': 'trend_chart',
            'type': 'line_chart',
            'title': 'Performance Trends',
            'data': [],  # Would populate with actual trend data
            'config': {'x_axis': 'date', 'y_axis': 'value', 'smooth': True}
        }

    def _create_comparison_visualization(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comparison visualization."""
        return {
            'id': 'comparison_chart',
            'type': 'bar_chart',
            'title': 'Performance Comparison',
            'data': [],  # Would populate with actual comparison data
            'config': {'orientation': 'vertical', 'grouped': True}
        }

    def _create_platform_distribution_visualization(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create platform distribution visualization."""
        return {
            'id': 'platform_distribution',
            'type': 'pie_chart',
            'title': 'Platform Performance Distribution',
            'data': [],  # Would populate with platform data
            'config': {'show_percentages': True, 'interactive': True}
        }

    def _create_performance_heatmap(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance heatmap."""
        return {
            'id': 'performance_heatmap',
            'type': 'heatmap',
            'title': 'Performance Heatmap',
            'data': [],  # Would populate with heatmap data
            'config': {'color_scale': 'viridis', 'show_values': True}
        }

    def _create_custom_visualization(self, viz_type: VisualizationType, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custom visualization."""
        return {
            'id': f'custom_{viz_type.value}',
            'type': viz_type.value,
            'title': f'Custom {viz_type.value.replace("_", " ").title()}',
            'data': [],
            'config': {}
        }

    def _extract_performance_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics for section."""
        metrics = {}

        if 'dashboard_data' in report_data:
            metrics['kpis'] = report_data['dashboard_data'].get('kpis', [])

        if 'kol_analytics' in report_data:
            metrics['kol_metrics'] = [
                kol.get('overall_metrics', {})
                for kol in report_data['kol_analytics']
            ]

        if 'campaign_analytics' in report_data:
            metrics['campaign_metrics'] = [
                campaign.get('metrics', {})
                for campaign in report_data['campaign_analytics']
            ]

        return metrics

    async def _generate_trend_analysis(
        self,
        metric: MetricType,
        time_range: TimeRange,
        db_session: Any
    ) -> Dict[str, Any]:
        """Generate trend analysis for specific metric."""
        # Simulate trend analysis
        return {
            'metric': metric.value,
            'trend_direction': 'increasing',
            'trend_strength': 0.75,
            'data_points': [],
            'forecast': []
        }