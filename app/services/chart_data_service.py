"""
Chart Data Service for generating chart data for report templates.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.models.campaign import Campaign
from app.models.kol_metrics import KOLMetrics
from app.models.post_metrics import PostMetrics, CollectionInterval
from app.models.post import Post
from app.models.campaign_kol import CampaignKOL


class ChartDataService:
    """Service for generating chart data for various chart types."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def generate_chart_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Generate chart data based on chart configuration.
        
        Args:
            chart_config: Chart configuration from template
            campaign_id: Campaign ID
            
        Returns:
            Chart data dictionary with labels, datasets, and metadata
        """
        chart_type = chart_config.get('chart_type', 'bar')
        data_source = chart_config.get('data_source', 'kol_performance')
        
        # Route to appropriate data generation method
        if data_source == 'kol_performance':
            return await self._generate_kol_performance_data(chart_config, campaign_id)
        elif data_source == 'kpi_achievement':
            return await self._generate_kpi_achievement_data(chart_config, campaign_id)
        elif data_source == 'platform_breakdown':
            return await self._generate_platform_breakdown_data(chart_config, campaign_id)
        elif data_source == 'engagement_timeline':
            return await self._generate_engagement_timeline_data(chart_config, campaign_id)
        elif data_source == 'post_performance':
            return await self._generate_post_performance_data(chart_config, campaign_id)
        elif data_source == 'campaign_summary':
            return await self._generate_campaign_summary_data(chart_config, campaign_id)
        else:
            return self._generate_empty_chart_data(chart_type)
    
    async def _generate_kol_performance_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """Generate KOL performance comparison chart data."""
        # Get campaign KOLs with latest metrics
        campaign_kols_query = (
            select(CampaignKOL)
            .options(selectinload(CampaignKOL.kol))
            .where(CampaignKOL.campaign_id == campaign_id)
        )
        
        result = await self.session.execute(campaign_kols_query)
        campaign_kols = result.scalars().all()
        
        if not campaign_kols:
            return self._generate_empty_chart_data(chart_config.get('chart_type', 'bar'))
        
        # Fetch latest metrics for each KOL
        kol_ids = [ck.kol_id for ck in campaign_kols]
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
        
        # Prepare chart data
        labels = []
        reach_data = []
        engagement_data = []
        engagement_rate_data = []
        
        for ck in campaign_kols:
            kol_name = f"KOL #{ck.kol_id}"  # TODO: Get actual KOL name
            labels.append(kol_name)
            
            if ck.kol_id in kol_metrics:
                metric = kol_metrics[ck.kol_id]
                reach_data.append(metric.follower_count)
                engagement_data.append(
                    (metric.total_likes or 0) + 
                    (metric.total_comments or 0) + 
                    (metric.total_shares or 0)
                )
                engagement_rate_data.append(float(metric.engagement_rate))
            else:
                reach_data.append(0)
                engagement_data.append(0)
                engagement_rate_data.append(0)
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Total Reach',
                    'data': reach_data,
                    'backgroundColor': '#1f4e79',
                    'borderColor': '#1f4e79',
                    'borderWidth': 1
                },
                {
                    'label': 'Total Engagement',
                    'data': engagement_data,
                    'backgroundColor': '#70ad47',
                    'borderColor': '#70ad47',
                    'borderWidth': 1
                }
            ],
            'chart_type': chart_config.get('chart_type', 'bar'),
            'title': chart_config.get('title', 'KOL Performance Comparison')
        }
    
    async def _generate_kpi_achievement_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """Generate KPI achievement chart data."""
        # TODO: Implement KPI achievement data generation
        # For now, return sample data
        return {
            'labels': ['Achieved', 'Remaining', 'Exceeded'],
            'datasets': [{
                'data': [70, 20, 10],
                'backgroundColor': ['#70ad47', '#ffc000', '#c55a5a'],
                'borderWidth': 0
            }],
            'chart_type': chart_config.get('chart_type', 'donut'),
            'title': chart_config.get('title', 'KPI Achievement')
        }
    
    async def _generate_platform_breakdown_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """Generate platform breakdown chart data."""
        # Get posts by platform
        posts_query = (
            select(Post.platform, func.count(Post.id).label('post_count'))
            .where(
                and_(
                    Post.campaign_id == campaign_id,
                    Post.is_campaign_content == True
                )
            )
            .group_by(Post.platform)
        )
        
        result = await self.session.execute(posts_query)
        platform_data = result.all()
        
        if not platform_data:
            return self._generate_empty_chart_data(chart_config.get('chart_type', 'pie'))
        
        labels = [row.platform.title() for row in platform_data]
        data = [row.post_count for row in platform_data]
        
        # Platform colors
        platform_colors = {
            'instagram': '#E4405F',
            'tiktok': '#000000',
            'youtube': '#FF0000',
            'facebook': '#1877F2',
            'twitter': '#1DA1F2'
        }
        
        colors = [
            platform_colors.get(row.platform.lower(), '#666666') 
            for row in platform_data
        ]
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors,
                'borderWidth': 1
            }],
            'chart_type': chart_config.get('chart_type', 'pie'),
            'title': chart_config.get('title', 'Platform Breakdown')
        }
    
    async def _generate_engagement_timeline_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """Generate engagement timeline chart data."""
        # Get campaign posts with metrics over time
        posts_query = (
            select(Post)
            .options(selectinload(Post.metrics))
            .where(
                and_(
                    Post.campaign_id == campaign_id,
                    Post.is_campaign_content == True
                )
            )
            .order_by(Post.posted_at)
        )
        
        result = await self.session.execute(posts_query)
        posts = result.scalars().all()
        
        if not posts:
            return self._generate_empty_chart_data(chart_config.get('chart_type', 'line'))
        
        # Group engagement by day
        daily_engagement = defaultdict(int)
        
        for post in posts:
            post_date = post.posted_at.date()
            
            # Get latest metrics for this post
            if post.metrics:
                latest_metric = max(post.metrics, key=lambda m: m.collected_at)
                engagement = latest_metric.likes + latest_metric.comments + latest_metric.shares
                daily_engagement[post_date] += engagement
        
        # Sort by date and prepare chart data
        sorted_dates = sorted(daily_engagement.keys())
        labels = [date.strftime('%m/%d') for date in sorted_dates]
        data = [daily_engagement[date] for date in sorted_dates]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Daily Engagement',
                'data': data,
                'borderColor': '#1f4e79',
                'backgroundColor': 'rgba(31, 78, 121, 0.1)',
                'borderWidth': 2,
                'fill': True
            }],
            'chart_type': chart_config.get('chart_type', 'line'),
            'title': chart_config.get('title', 'Engagement Timeline')
        }
    
    async def _generate_post_performance_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """Generate top performing posts chart data."""
        # Get posts with latest metrics
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
        
        if not posts:
            return self._generate_empty_chart_data(chart_config.get('chart_type', 'bar'))
        
        # Calculate engagement for each post and get top 10
        post_engagement = []
        
        for post in posts:
            if post.metrics:
                latest_metric = max(post.metrics, key=lambda m: m.collected_at)
                engagement = latest_metric.likes + latest_metric.comments + latest_metric.shares
                post_engagement.append({
                    'post': post,
                    'engagement': engagement,
                    'metric': latest_metric
                })
        
        # Sort by engagement and take top 10
        top_posts = sorted(post_engagement, key=lambda x: x['engagement'], reverse=True)[:10]
        
        labels = [f"Post #{p['post'].id}" for p in top_posts]
        likes_data = [p['metric'].likes for p in top_posts]
        comments_data = [p['metric'].comments for p in top_posts]
        shares_data = [p['metric'].shares for p in top_posts]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Likes',
                    'data': likes_data,
                    'backgroundColor': '#E4405F',
                    'borderColor': '#E4405F',
                    'borderWidth': 1
                },
                {
                    'label': 'Comments',
                    'data': comments_data,
                    'backgroundColor': '#1877F2',
                    'borderColor': '#1877F2',
                    'borderWidth': 1
                },
                {
                    'label': 'Shares',
                    'data': shares_data,
                    'backgroundColor': '#70ad47',
                    'borderColor': '#70ad47',
                    'borderWidth': 1
                }
            ],
            'chart_type': chart_config.get('chart_type', 'bar'),
            'title': chart_config.get('title', 'Top Performing Posts')
        }
    
    async def _generate_campaign_summary_data(
        self, 
        chart_config: Dict[str, Any], 
        campaign_id: int
    ) -> Dict[str, Any]:
        """Generate campaign summary table data."""
        # Get campaign with metrics
        campaign_query = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
        )
        
        result = await self.session.execute(campaign_query)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return {'data': [], 'columns': ['Metric', 'Value']}
        
        # Calculate summary metrics
        kol_count_query = select(func.count(CampaignKOL.id)).where(CampaignKOL.campaign_id == campaign_id)
        kol_count_result = await self.session.execute(kol_count_query)
        kol_count = kol_count_result.scalar() or 0
        
        posts_count_query = select(func.count(Post.id)).where(
            and_(
                Post.campaign_id == campaign_id,
                Post.is_campaign_content == True
            )
        )
        posts_count_result = await self.session.execute(posts_count_query)
        posts_count = posts_count_result.scalar() or 0
        
        # Prepare table data
        summary_data = [
            ['Campaign Name', campaign.name],
            ['Status', campaign.status.value.title()],
            ['Total Budget', f"{campaign.total_budget:,.2f} {campaign.currency}" if campaign.total_budget else "N/A"],
            ['KOLs Count', f"{kol_count:,}"],
            ['Total Posts', f"{posts_count:,}"],
            ['Start Date', campaign.start_date.strftime('%B %d, %Y') if campaign.start_date else "N/A"],
            ['End Date', campaign.end_date.strftime('%B %d, %Y') if campaign.end_date else "N/A"],
        ]
        
        return {
            'data': summary_data,
            'columns': ['Metric', 'Value'],
            'title': chart_config.get('title', 'Campaign Summary')
        }
    
    def _generate_empty_chart_data(self, chart_type: str) -> Dict[str, Any]:
        """Generate empty chart data structure."""
        if chart_type in ['pie', 'donut']:
            return {
                'labels': ['No Data'],
                'datasets': [{
                    'data': [1],
                    'backgroundColor': ['#cccccc'],
                    'borderWidth': 0
                }],
                'chart_type': chart_type,
                'title': 'No Data Available'
            }
        elif chart_type == 'line':
            return {
                'labels': [],
                'datasets': [{
                    'label': 'No Data',
                    'data': [],
                    'borderColor': '#cccccc',
                    'backgroundColor': 'rgba(204, 204, 204, 0.1)',
                    'borderWidth': 1
                }],
                'chart_type': chart_type,
                'title': 'No Data Available'
            }
        else:  # bar, column, etc.
            return {
                'labels': ['No Data'],
                'datasets': [{
                    'label': 'No Data',
                    'data': [0],
                    'backgroundColor': '#cccccc',
                    'borderColor': '#cccccc',
                    'borderWidth': 1
                }],
                'chart_type': chart_type,
                'title': 'No Data Available'
            }
    
    async def get_available_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Get available chart data sources with their descriptions."""
        return {
            'kol_performance': {
                'name': 'KOL Performance',
                'description': 'Compare KOL reach and engagement metrics',
                'chart_types': ['bar', 'column', 'line'],
                'fields': ['reach', 'engagement', 'engagement_rate']
            },
            'kpi_achievement': {
                'name': 'KPI Achievement',
                'description': 'Show KPI achievement status',
                'chart_types': ['pie', 'donut'],
                'fields': ['achieved', 'remaining', 'exceeded']
            },
            'platform_breakdown': {
                'name': 'Platform Breakdown',
                'description': 'Distribution of posts across platforms',
                'chart_types': ['pie', 'donut', 'bar'],
                'fields': ['post_count', 'engagement']
            },
            'engagement_timeline': {
                'name': 'Engagement Timeline',
                'description': 'Engagement trends over time',
                'chart_types': ['line', 'area'],
                'fields': ['daily_engagement', 'cumulative_engagement']
            },
            'post_performance': {
                'name': 'Post Performance',
                'description': 'Top performing posts comparison',
                'chart_types': ['bar', 'column'],
                'fields': ['likes', 'comments', 'shares', 'engagement']
            },
            'campaign_summary': {
                'name': 'Campaign Summary',
                'description': 'Key campaign metrics table',
                'chart_types': ['table'],
                'fields': ['various_metrics']
            }
        }


# Dependency function for FastAPI
async def get_chart_data_service(session: AsyncSession) -> ChartDataService:
    """Get ChartDataService instance."""
    return ChartDataService(session)