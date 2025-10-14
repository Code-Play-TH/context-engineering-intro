"""
Data Population Service for populating report templates with campaign data.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.models.campaign import Campaign
from app.models.kol_metrics import KOLMetrics
from app.models.post_metrics import PostMetrics
from app.models.post import Post
from app.models.campaign_kpi import CampaignKPI
from app.models.deliverable import Deliverable
from app.models.campaign_kol import CampaignKOL
from app.models.report_template import ReportTemplate
from app.services.variable_mapping import variable_mapper, VariableFormatters
from app.services.chart_data_service import ChartDataService


class DataPopulationService:
    """Service for populating report templates with campaign data."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.formatters = VariableFormatters()
        self.variable_mapper = variable_mapper
        self.chart_service = ChartDataService(session)
    
    async def populate_template_variables(
        self, 
        template: ReportTemplate, 
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Populate all template variables with campaign data.
        
        Args:
            template: ReportTemplate instance
            campaign_id: Campaign ID to fetch data for
            
        Returns:
            Dictionary with variable names as keys and populated data as values
        """
        # Fetch campaign data
        campaign_data = await self.fetch_campaign_metrics(campaign_id)
        
        # Initialize populated data dictionary
        populated_data = {}
        
        # Process each variable in the template
        for variable in template.variables:
            # Map variable to data using the comprehensive mapping system
            populated_data[variable] = self._get_variable_value(variable, campaign_data)
        
        return populated_data
    
    async def generate_chart_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Generate chart data for template charts.
        
        Args:
            chart_config: Chart configuration from template
            campaign_id: Campaign ID
            
        Returns:
            Chart data dictionary
        """
        return await self.chart_service.generate_chart_data(chart_config, campaign_id)
    
    async def fetch_campaign_metrics(self, campaign_id: int) -> Dict[str, Any]:
        """
        Fetch comprehensive campaign metrics and data.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary containing all campaign-related data
        """
        # Fetch campaign with relationships
        campaign_query = (
            select(Campaign)
            .options(
                selectinload(Campaign.kpis),
                selectinload(Campaign.deliverables),
                selectinload(Campaign.campaign_kols)
            )
            .where(Campaign.id == campaign_id)
        )
        
        result = await self.session.execute(campaign_query)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return {}
        
        # Fetch KOL metrics
        kol_metrics = await self._fetch_kol_metrics(campaign_id)
        
        # Fetch post metrics
        post_metrics = await self._fetch_post_metrics(campaign_id)
        
        # Calculate aggregated metrics
        aggregated_metrics = await self.calculate_aggregated_metrics(campaign_id)
        
        return {
            'campaign': campaign,
            'kol_metrics': kol_metrics,
            'post_metrics': post_metrics,
            'aggregated_metrics': aggregated_metrics,
            'generation_date': datetime.utcnow()
        }
    
    async def _fetch_kol_metrics(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Fetch latest KOL metrics for campaign KOLs."""
        # Get campaign KOLs
        campaign_kols_query = select(CampaignKOL).where(CampaignKOL.campaign_id == campaign_id)
        result = await self.session.execute(campaign_kols_query)
        campaign_kols = result.scalars().all()
        
        kol_ids = [ck.kol_id for ck in campaign_kols]
        
        if not kol_ids:
            return []
        
        # Fetch latest metrics for each KOL
        metrics_query = (
            select(KOLMetrics)
            .where(KOLMetrics.kol_id.in_(kol_ids))
            .order_by(KOLMetrics.kol_id, desc(KOLMetrics.scraped_at))
        )
        
        result = await self.session.execute(metrics_query)
        all_metrics = result.scalars().all()
        
        # Group by KOL and get latest metrics
        kol_metrics = {}
        for metric in all_metrics:
            if metric.kol_id not in kol_metrics:
                kol_metrics[metric.kol_id] = metric
        
        return list(kol_metrics.values())
    
    async def _fetch_post_metrics(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Fetch post metrics for campaign posts."""
        # Get campaign posts
        posts_query = (
            select(Post)
            .options(selectinload(Post.metrics))
            .where(
                and_(
                    Post.campaign_id == campaign_id,
                    Post.is_campaign_content == True
                )
            )
        )
        
        result = await self.session.execute(posts_query)
        posts = result.scalars().all()
        
        post_metrics = []
        for post in posts:
            if post.metrics:
                # Get latest metrics for each post
                latest_metric = max(post.metrics, key=lambda m: m.collected_at)
                post_metrics.append({
                    'post': post,
                    'latest_metrics': latest_metric,
                    'all_metrics': post.metrics
                })
        
        return post_metrics
    
    async def calculate_aggregated_metrics(self, campaign_id: int) -> Dict[str, Any]:
        """
        Calculate aggregated campaign metrics.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with aggregated metrics
        """
        # Get KOL metrics
        kol_metrics = await self._fetch_kol_metrics(campaign_id)
        
        # Get post metrics
        post_metrics = await self._fetch_post_metrics(campaign_id)
        
        # Calculate totals
        total_reach = sum(metric.follower_count for metric in kol_metrics)
        total_engagement = sum(
            pm['latest_metrics'].engagement_count 
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        
        # Calculate averages
        avg_engagement_rate = 0
        if kol_metrics:
            avg_engagement_rate = sum(
                float(metric.engagement_rate) for metric in kol_metrics
            ) / len(kol_metrics)
        
        # Count metrics
        kol_count = len(kol_metrics)
        post_count = len(post_metrics)
        
        return {
            'total_reach': total_reach,
            'total_engagement': total_engagement,
            'avg_engagement_rate': round(avg_engagement_rate, 2),
            'kol_count': kol_count,
            'post_count': post_count
        }
    
    def _format_number(self, value: Any) -> str:
        """Format numbers with commas for readability."""
        if value is None:
            return "N/A"
        
        if isinstance(value, (int, float, Decimal)):
            if isinstance(value, float):
                # Round floats to 2 decimal places
                return f"{value:,.2f}"
            else:
                return f"{value:,}"
        
        return str(value)
    
    def _format_currency(self, value: Any, currency: str = "USD") -> str:
        """Format currency values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, (int, float, Decimal)):
            return f"{value:,.2f} {currency}"
        
        return str(value)
    
    def _format_percentage(self, value: Any) -> str:
        """Format percentage values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, (int, float, Decimal)):
            return f"{value:.1f}%"
        
        return str(value)
    
    def _format_date(self, value: Any) -> str:
        """Format date values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, datetime):
            return value.strftime("%B %d, %Y")
        elif hasattr(value, 'strftime'):
            return value.strftime("%B %d, %Y")
        
        return str(value)
    
    def _get_variable_value(self, variable: str, campaign_data: Dict[str, Any]) -> str:
        """
        Get the value for a specific template variable.
        
        Args:
            variable: Template variable (e.g., '{{campaign_name}}')
            campaign_data: Campaign data dictionary
            
        Returns:
            Formatted variable value
        """
        # Check if variable is supported
        variable_info = self.variable_mapper.get_variable_info(variable)
        if not variable_info:
            return "N/A"
        
        # Get the mapping function
        mapping_func = self._get_variable_mapping_function(variable)
        if mapping_func:
            return mapping_func(campaign_data)
        
        return "N/A"
    
    def _get_variable_mapping_function(self, variable: str) -> Optional[callable]:
        """Get the mapping function for a specific variable."""
        return self.VARIABLE_MAPPING.get(variable)
    
    # Variable mapping functions
    @property
    def VARIABLE_MAPPING(self) -> Dict[str, callable]:
        """Mapping of template variables to data extraction functions."""
        return {
            # Campaign Information
            '{{campaign_name}}': lambda data: data['campaign'].name if data.get('campaign') else "N/A",
            '{{campaign_start_date}}': lambda data: self.formatters.format_date(data['campaign'].start_date) if data.get('campaign') else "N/A",
            '{{campaign_end_date}}': lambda data: self.formatters.format_date(data['campaign'].end_date) if data.get('campaign') else "N/A",
            '{{campaign_budget}}': lambda data: self.formatters.format_number(data['campaign'].total_budget) if data.get('campaign') else "N/A",
            '{{campaign_currency}}': lambda data: data['campaign'].currency if data.get('campaign') else "USD",
            '{{campaign_status}}': lambda data: data['campaign'].status.value.title() if data.get('campaign') else "N/A",
            '{{campaign_objectives}}': lambda data: data['campaign'].objectives if data.get('campaign') else "N/A",
            '{{campaign_duration_days}}': lambda data: self._calculate_campaign_duration(data),
            
            # KOL Metrics
            '{{kol_count}}': lambda data: self.formatters.format_number(data['aggregated_metrics']['kol_count']) if data.get('aggregated_metrics') else "0",
            '{{total_reach}}': lambda data: self.formatters.format_number(data['aggregated_metrics']['total_reach']) if data.get('aggregated_metrics') else "0",
            '{{total_engagement}}': lambda data: self.formatters.format_number(data['aggregated_metrics']['total_engagement']) if data.get('aggregated_metrics') else "0",
            '{{avg_engagement_rate}}': lambda data: self.formatters.format_percentage(data['aggregated_metrics']['avg_engagement_rate']) if data.get('aggregated_metrics') else "0%",
            '{{top_performing_kol}}': lambda data: self._get_top_performing_kol(data),
            '{{avg_follower_count}}': lambda data: self._calculate_avg_follower_count(data),
            
            # Content Metrics
            '{{total_posts}}': lambda data: self.formatters.format_number(data['aggregated_metrics']['post_count']) if data.get('aggregated_metrics') else "0",
            '{{total_likes}}': lambda data: self._calculate_total_likes(data),
            '{{total_comments}}': lambda data: self._calculate_total_comments(data),
            '{{total_shares}}': lambda data: self._calculate_total_shares(data),
            '{{total_views}}': lambda data: self._calculate_total_views(data),
            '{{avg_likes_per_post}}': lambda data: self._calculate_avg_likes_per_post(data),
            '{{avg_comments_per_post}}': lambda data: self._calculate_avg_comments_per_post(data),
            
            # Performance Metrics
            '{{cpm}}': lambda data: self._calculate_cpm(data),
            '{{cpe}}': lambda data: self._calculate_cpe(data),
            '{{roi_percentage}}': lambda data: self._calculate_roi(data),
            '{{conversion_rate}}': lambda data: "N/A",  # TODO: Implement conversion tracking
            
            # Platform Breakdown
            '{{instagram_posts}}': lambda data: self._count_posts_by_platform(data, 'instagram'),
            '{{tiktok_posts}}': lambda data: self._count_posts_by_platform(data, 'tiktok'),
            '{{youtube_posts}}': lambda data: self._count_posts_by_platform(data, 'youtube'),
            '{{facebook_posts}}': lambda data: self._count_posts_by_platform(data, 'facebook'),
            
            # Time-based Metrics
            '{{best_posting_time}}': lambda data: self._get_best_posting_time(data),
            '{{best_posting_day}}': lambda data: self._get_best_posting_day(data),
            
            # KPI Achievement
            '{{kpi_reach_target}}': lambda data: self._get_kpi_target(data, 'reach'),
            '{{kpi_reach_actual}}': lambda data: self._get_kpi_actual(data, 'reach'),
            '{{kpi_reach_achievement}}': lambda data: self._get_kpi_achievement(data, 'reach'),
            '{{kpi_engagement_target}}': lambda data: self._get_kpi_target(data, 'engagement'),
            '{{kpi_engagement_actual}}': lambda data: self._get_kpi_actual(data, 'engagement'),
            '{{kpi_engagement_achievement}}': lambda data: self._get_kpi_achievement(data, 'engagement'),
            '{{overall_kpi_achievement}}': lambda data: self._calculate_overall_kpi_achievement(data),
            
            # Report Metadata
            '{{generation_date}}': lambda data: self.formatters.format_date(data['generation_date']) if data.get('generation_date') else self.formatters.format_date(datetime.utcnow()),
            '{{generation_time}}': lambda data: self.formatters.format_time(data['generation_date']) if data.get('generation_date') else self.formatters.format_time(datetime.utcnow()),
            '{{report_period}}': lambda data: self._format_report_period(data),
            
            # Client Information
            '{{client_name}}': lambda data: self._get_client_name(data),
            '{{client_logo}}': lambda data: self._get_client_logo(data),
            '{{brand_name}}': lambda data: self._get_brand_name(data),
        }
    
    # Helper methods for complex calculations
    def _calculate_campaign_duration(self, data: Dict[str, Any]) -> str:
        """Calculate campaign duration in days."""
        campaign = data.get('campaign')
        if not campaign or not campaign.start_date or not campaign.end_date:
            return "N/A"
        
        return self.formatters.format_duration(campaign.start_date, campaign.end_date)
    
    def _get_top_performing_kol(self, data: Dict[str, Any]) -> str:
        """Get the name of the top performing KOL."""
        kol_metrics = data.get('kol_metrics', [])
        if not kol_metrics:
            return "N/A"
        
        # Sort by engagement rate
        top_kol = max(kol_metrics, key=lambda k: float(k.engagement_rate))
        return f"KOL #{top_kol.kol_id}"  # TODO: Get actual KOL name
    
    def _calculate_avg_follower_count(self, data: Dict[str, Any]) -> str:
        """Calculate average follower count per KOL."""
        kol_metrics = data.get('kol_metrics', [])
        if not kol_metrics:
            return "0"
        
        total_followers = sum(metric.follower_count for metric in kol_metrics)
        avg_followers = total_followers / len(kol_metrics)
        return self.formatters.format_number(avg_followers)
    
    def _calculate_total_likes(self, data: Dict[str, Any]) -> str:
        """Calculate total likes across all posts."""
        post_metrics = data.get('post_metrics', [])
        total_likes = sum(
            pm['latest_metrics'].likes 
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        return self.formatters.format_number(total_likes)
    
    def _calculate_total_comments(self, data: Dict[str, Any]) -> str:
        """Calculate total comments across all posts."""
        post_metrics = data.get('post_metrics', [])
        total_comments = sum(
            pm['latest_metrics'].comments 
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        return self.formatters.format_number(total_comments)
    
    def _calculate_total_shares(self, data: Dict[str, Any]) -> str:
        """Calculate total shares across all posts."""
        post_metrics = data.get('post_metrics', [])
        total_shares = sum(
            pm['latest_metrics'].shares 
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        return self.formatters.format_number(total_shares)
    
    def _calculate_total_views(self, data: Dict[str, Any]) -> str:
        """Calculate total views across all posts."""
        post_metrics = data.get('post_metrics', [])
        total_views = sum(
            pm['latest_metrics'].views or 0
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        return self.formatters.format_number(total_views)
    
    def _calculate_avg_likes_per_post(self, data: Dict[str, Any]) -> str:
        """Calculate average likes per post."""
        post_metrics = data.get('post_metrics', [])
        if not post_metrics:
            return "0"
        
        total_likes = sum(
            pm['latest_metrics'].likes 
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        avg_likes = total_likes / len(post_metrics)
        return self.formatters.format_number(avg_likes)
    
    def _calculate_avg_comments_per_post(self, data: Dict[str, Any]) -> str:
        """Calculate average comments per post."""
        post_metrics = data.get('post_metrics', [])
        if not post_metrics:
            return "0"
        
        total_comments = sum(
            pm['latest_metrics'].comments 
            for pm in post_metrics 
            if pm['latest_metrics']
        )
        avg_comments = total_comments / len(post_metrics)
        return self.formatters.format_number(avg_comments)
    
    def _calculate_cpm(self, data: Dict[str, Any]) -> str:
        """Calculate cost per mille (thousand impressions)."""
        campaign = data.get('campaign')
        aggregated = data.get('aggregated_metrics', {})
        
        if not campaign or not campaign.total_budget or not aggregated.get('total_reach'):
            return "N/A"
        
        cpm = (float(campaign.total_budget) / aggregated['total_reach']) * 1000
        return self.formatters.format_currency(cpm, campaign.currency)
    
    def _calculate_cpe(self, data: Dict[str, Any]) -> str:
        """Calculate cost per engagement."""
        campaign = data.get('campaign')
        aggregated = data.get('aggregated_metrics', {})
        
        if not campaign or not campaign.total_budget or not aggregated.get('total_engagement'):
            return "N/A"
        
        cpe = float(campaign.total_budget) / aggregated['total_engagement']
        return self.formatters.format_currency(cpe, campaign.currency)
    
    def _calculate_roi(self, data: Dict[str, Any]) -> str:
        """Calculate return on investment."""
        # TODO: Implement ROI calculation based on conversion tracking
        return "N/A"
    
    def _count_posts_by_platform(self, data: Dict[str, Any], platform: str) -> str:
        """Count posts by platform."""
        post_metrics = data.get('post_metrics', [])
        platform_posts = sum(
            1 for pm in post_metrics 
            if pm['post'].platform.lower() == platform.lower()
        )
        return self.formatters.format_number(platform_posts)
    
    def _get_best_posting_time(self, data: Dict[str, Any]) -> str:
        """Get best performing posting time."""
        # TODO: Implement time analysis
        return "N/A"
    
    def _get_best_posting_day(self, data: Dict[str, Any]) -> str:
        """Get best performing day of week."""
        # TODO: Implement day analysis
        return "N/A"
    
    def _get_kpi_target(self, data: Dict[str, Any], kpi_type: str) -> str:
        """Get KPI target value."""
        campaign = data.get('campaign')
        if not campaign or not campaign.kpis:
            return "N/A"
        
        # TODO: Implement KPI target extraction
        return "N/A"
    
    def _get_kpi_actual(self, data: Dict[str, Any], kpi_type: str) -> str:
        """Get KPI actual value."""
        # TODO: Implement KPI actual extraction
        return "N/A"
    
    def _get_kpi_achievement(self, data: Dict[str, Any], kpi_type: str) -> str:
        """Get KPI achievement percentage."""
        # TODO: Implement KPI achievement calculation
        return "N/A"
    
    def _calculate_overall_kpi_achievement(self, data: Dict[str, Any]) -> str:
        """Calculate overall KPI achievement."""
        # TODO: Implement overall KPI achievement calculation
        return "N/A"
    
    def _format_report_period(self, data: Dict[str, Any]) -> str:
        """Format the report period."""
        campaign = data.get('campaign')
        if not campaign or not campaign.start_date or not campaign.end_date:
            return "N/A"
        
        start = self.formatters.format_date(campaign.start_date)
        end = self.formatters.format_date(campaign.end_date)
        return f"{start} - {end}"
    
    def _get_client_name(self, data: Dict[str, Any]) -> str:
        """Get client name."""
        # TODO: Implement client name extraction from campaign or client brief
        return "Client Name"
    
    def _get_client_logo(self, data: Dict[str, Any]) -> str:
        """Get client logo path."""
        # TODO: Implement client logo handling
        return "logo_placeholder.png"
    
    def _get_brand_name(self, data: Dict[str, Any]) -> str:
        """Get brand name."""
        # TODO: Implement brand name extraction
        return "Brand Name"


# Dependency function for FastAPI
async def get_data_population_service(session: AsyncSession) -> DataPopulationService:
    """Get DataPopulationService instance."""
    return DataPopulationService(session)