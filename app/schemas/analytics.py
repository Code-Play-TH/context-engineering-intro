"""
Analytics Pydantic Schemas

Provides validation schemas for analytics and reporting operations including:
- Analytics requests and responses
- KOL performance analytics
- Campaign analytics and ROI analysis
- Content performance metrics
- Platform comparisons and trends
- Dashboard data and visualizations
- Export and reporting configurations
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TimeRange(str, Enum):
    """Time range enumeration for analytics."""
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class MetricType(str, Enum):
    """Metric type enumeration."""
    ENGAGEMENT = "engagement"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    FOLLOWERS = "followers"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"
    ROI = "roi"
    CPM = "cpm"
    CPC = "cpc"
    CPA = "cpa"
    SENTIMENT = "sentiment"
    BRAND_SAFETY = "brand_safety"
    QUALITY_SCORE = "quality_score"


class VisualizationType(str, Enum):
    """Visualization type enumeration."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TABLE = "table"


class ExportFormat(str, Enum):
    """Export format enumeration."""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"
    PNG = "png"
    SVG = "svg"


# Base Analytics Schemas
class AnalyticsRequest(BaseModel):
    """Schema for analytics requests."""
    report_name: str = Field(..., min_length=1, max_length=200)
    entity_type: str = Field(..., description="Type of entity to analyze")
    entity_ids: Optional[List[int]] = Field(None, description="Specific entity IDs")
    metrics: List[MetricType] = Field(..., min_items=1)
    time_range: TimeRange = TimeRange.LAST_30_DAYS
    custom_date_range: Optional[Dict[str, datetime]] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    include_comparisons: bool = False
    include_trends: bool = True
    include_forecasts: bool = False
    visualization_types: List[VisualizationType] = Field(default_factory=list)


class AnalyticsResponse(BaseModel):
    """Schema for analytics responses."""
    report_id: str
    report_name: str
    entity_type: str
    time_range: TimeRange
    generated_at: datetime
    data: Dict[str, Any]
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# KOL Analytics Schemas
class KOLMetrics(BaseModel):
    """Schema for KOL performance metrics."""
    total_followers: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    average_likes: float = Field(ge=0)
    average_comments: float = Field(ge=0)
    average_shares: float = Field(ge=0)
    reach: int = Field(ge=0)
    impressions: int = Field(ge=0)
    growth_rate: float = Field(description="Follower growth rate")
    quality_score: float = Field(ge=0, le=1)
    brand_safety_score: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)


class KOLPlatformMetrics(BaseModel):
    """Schema for KOL platform-specific metrics."""
    platform: str
    followers: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    posts_count: int = Field(ge=0)
    average_engagement: float = Field(ge=0)
    top_content: List[Dict[str, Any]] = Field(default_factory=list)
    growth_metrics: Dict[str, float] = Field(default_factory=dict)


class KOLAnalyticsResponse(BaseModel):
    """Schema for KOL analytics responses."""
    kol_id: int
    kol_name: str
    overall_metrics: KOLMetrics
    platform_metrics: List[KOLPlatformMetrics] = Field(default_factory=list)
    trend_data: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    peer_comparison: Optional[Dict[str, Any]] = None
    campaign_performance: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_period: Dict[str, datetime]

    model_config = ConfigDict(from_attributes=True)


# Campaign Analytics Schemas
class CampaignMetrics(BaseModel):
    """Schema for campaign performance metrics."""
    total_reach: int = Field(ge=0)
    total_impressions: int = Field(ge=0)
    total_engagement: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    total_clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=1)
    total_spend: float = Field(ge=0)
    revenue: float = Field(ge=0)
    roi: float = Field(description="Return on Investment")
    cpm: float = Field(ge=0, description="Cost per mille")
    cpc: float = Field(ge=0, description="Cost per click")
    cpa: float = Field(ge=0, description="Cost per acquisition")


class CampaignAnalyticsResponse(BaseModel):
    """Schema for campaign analytics responses."""
    campaign_id: int
    campaign_name: str
    status: str
    metrics: CampaignMetrics
    kol_performance: List[Dict[str, Any]] = Field(default_factory=list)
    content_performance: List[Dict[str, Any]] = Field(default_factory=list)
    platform_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    timeline_data: List[Dict[str, Any]] = Field(default_factory=list)
    roi_analysis: Optional[Dict[str, Any]] = None
    predictions: Optional[Dict[str, Any]] = None
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_period: Dict[str, datetime]

    model_config = ConfigDict(from_attributes=True)


# Content Analytics Schemas
class ContentMetrics(BaseModel):
    """Schema for content performance metrics."""
    total_posts: int = Field(ge=0)
    average_engagement: float = Field(ge=0)
    average_reach: float = Field(ge=0)
    average_impressions: float = Field(ge=0)
    top_performing_content_type: str
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    quality_distribution: Dict[str, int] = Field(default_factory=dict)
    engagement_trends: List[Dict[str, Any]] = Field(default_factory=list)


class ContentAnalyticsResponse(BaseModel):
    """Schema for content analytics responses."""
    overall_metrics: ContentMetrics
    content_type_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    platform_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    trending_topics: List[Dict[str, Any]] = Field(default_factory=list)
    top_performing_content: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict)
    quality_analysis: Dict[str, Any] = Field(default_factory=dict)
    engagement_patterns: Dict[str, Any] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_period: Dict[str, datetime]

    model_config = ConfigDict(from_attributes=True)


# Platform Analytics Schemas
class PlatformMetrics(BaseModel):
    """Schema for platform-specific metrics."""
    platform: str
    total_reach: int = Field(ge=0)
    total_engagement: int = Field(ge=0)
    engagement_rate: float = Field(ge=0, le=1)
    average_cpm: float = Field(ge=0)
    average_cpc: float = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=1)
    roi: float
    growth_rate: float


class PlatformAnalyticsResponse(BaseModel):
    """Schema for platform analytics responses."""
    platform_metrics: List[PlatformMetrics]
    platform_comparisons: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    trend_analysis: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    audience_demographics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    optimal_posting_times: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    content_preferences: Dict[str, List[str]] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_period: Dict[str, datetime]

    model_config = ConfigDict(from_attributes=True)


# Dashboard Schemas
class DashboardKPI(BaseModel):
    """Schema for dashboard KPIs."""
    name: str
    value: Union[int, float, str]
    previous_value: Optional[Union[int, float, str]] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    format_type: str = "number"  # "number", "currency", "percentage"


class DashboardChart(BaseModel):
    """Schema for dashboard charts."""
    chart_id: str
    title: str
    chart_type: VisualizationType
    data: List[Dict[str, Any]]
    config: Dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Schema for dashboard responses."""
    kpis: List[DashboardKPI] = Field(default_factory=list)
    charts: List[DashboardChart] = Field(default_factory=list)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    quick_insights: List[str] = Field(default_factory=list)
    performance_summary: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime
    time_range: TimeRange

    model_config = ConfigDict(from_attributes=True)


# Visualization Schemas
class VisualizationData(BaseModel):
    """Schema for visualization data."""
    visualization_id: str
    title: str
    visualization_type: VisualizationType
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Comparison and Analysis Schemas
class ComparisonEntity(BaseModel):
    """Schema for entities in comparison analysis."""
    entity_id: int
    entity_name: str
    entity_type: str
    metrics: Dict[str, Union[int, float]]
    ranking: Optional[int] = None
    percentile: Optional[float] = None


class ComparisonAnalysis(BaseModel):
    """Schema for comparison analysis responses."""
    comparison_id: str
    entities: List[ComparisonEntity]
    comparison_metrics: List[MetricType]
    winner: Optional[ComparisonEntity] = None
    insights: List[str] = Field(default_factory=list)
    statistical_significance: Dict[str, float] = Field(default_factory=dict)
    visualizations: List[VisualizationData] = Field(default_factory=list)
    analysis_period: Dict[str, datetime]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrendPoint(BaseModel):
    """Schema for trend data points."""
    timestamp: datetime
    value: Union[int, float]
    metadata: Optional[Dict[str, Any]] = None


class TrendAnalysis(BaseModel):
    """Schema for trend analysis responses."""
    trend_id: str
    metric_type: MetricType
    data_points: List[TrendPoint]
    trend_direction: str  # "increasing", "decreasing", "stable", "volatile"
    trend_strength: float = Field(ge=0, le=1)
    seasonal_patterns: Optional[List[Dict[str, Any]]] = None
    forecasts: Optional[List[TrendPoint]] = None
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    confidence_interval: Optional[Dict[str, float]] = None
    analysis_period: Dict[str, datetime]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ROI Analysis Schemas
class ROIBreakdown(BaseModel):
    """Schema for ROI breakdown by dimension."""
    dimension: str
    dimension_value: str
    investment: float = Field(ge=0)
    revenue: float = Field(ge=0)
    roi: float
    roi_percentage: float


class ROIAnalysis(BaseModel):
    """Schema for ROI analysis responses."""
    analysis_id: str
    overall_roi: float
    total_investment: float = Field(ge=0)
    total_revenue: float = Field(ge=0)
    breakdowns: List[ROIBreakdown] = Field(default_factory=list)
    roi_trends: List[TrendPoint] = Field(default_factory=list)
    projections: Optional[List[TrendPoint]] = None
    benchmarks: Dict[str, float] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_period: Dict[str, datetime]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Export Schemas
class ExportRequest(BaseModel):
    """Schema for export requests."""
    export_name: str = Field(..., min_length=1, max_length=200)
    format: ExportFormat
    entity_type: str
    entity_ids: Optional[List[int]] = None
    metrics: List[MetricType] = Field(..., min_items=1)
    time_range: TimeRange = TimeRange.LAST_30_DAYS
    custom_date_range: Optional[Dict[str, datetime]] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    include_visualizations: bool = False
    include_raw_data: bool = True
    compression: bool = False


class ExportResponse(BaseModel):
    """Schema for export responses."""
    task_id: str
    export_name: str
    format: ExportFormat
    status: str  # "processing", "completed", "failed"
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Insight and Recommendation Schemas
class InsightCategory(str, Enum):
    """Insight category enumeration."""
    PERFORMANCE = "performance"
    AUDIENCE = "audience"
    CONTENT = "content"
    ENGAGEMENT = "engagement"
    GROWTH = "growth"
    OPTIMIZATION = "optimization"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class Insight(BaseModel):
    """Schema for AI-generated insights."""
    insight_id: str
    category: InsightCategory
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)
    impact_score: float = Field(ge=0, le=1)
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime


class Recommendation(BaseModel):
    """Schema for actionable recommendations."""
    recommendation_id: str
    title: str
    description: str
    category: str
    priority: str  # "low", "medium", "high", "critical"
    effort_required: str  # "low", "medium", "high"
    expected_impact: str  # "low", "medium", "high"
    implementation_steps: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    related_insights: List[str] = Field(default_factory=list)
    generated_at: datetime


# Filter and Search Schemas
class AnalyticsFilters(BaseModel):
    """Schema for analytics filters."""
    entity_types: Optional[List[str]] = None
    entity_ids: Optional[List[int]] = None
    platforms: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    metric_thresholds: Optional[Dict[str, Dict[str, float]]] = None
    tags: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None


# Advanced Analytics Schemas
class CohortAnalysis(BaseModel):
    """Schema for cohort analysis."""
    cohort_id: str
    cohort_name: str
    cohort_definition: Dict[str, Any]
    time_periods: List[str]
    retention_rates: List[List[float]]
    value_metrics: Optional[List[List[float]]] = None
    insights: List[str] = Field(default_factory=list)
    generated_at: datetime


class FunnelAnalysis(BaseModel):
    """Schema for funnel analysis."""
    funnel_id: str
    funnel_name: str
    stages: List[Dict[str, Any]]
    conversion_rates: List[float]
    drop_off_points: List[Dict[str, Any]]
    optimization_opportunities: List[str] = Field(default_factory=list)
    generated_at: datetime


class AttributionAnalysis(BaseModel):
    """Schema for attribution analysis."""
    attribution_id: str
    attribution_model: str
    touchpoints: List[Dict[str, Any]]
    attribution_weights: Dict[str, float]
    conversion_paths: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    generated_at: datetime