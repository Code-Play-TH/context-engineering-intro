"""Pydantic schemas for analytics API."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HistoricalMetricsRequest(BaseModel):
    """Request model for historical metrics."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: Optional[int] = Field(None, ge=1, le=365)
    granularity: str = Field("daily", regex="^(raw|daily|weekly|monthly)$")


class GrowthAnalysisRequest(BaseModel):
    """Request model for growth analysis."""
    platforms: Optional[List[str]] = None
    period_days: int = Field(30, ge=7, le=365)


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection."""
    platforms: Optional[List[str]] = None
    detection_window_days: int = Field(7, ge=1, le=30)
    auto_create_alerts: bool = Field(True)


class ComparativeAnalysisRequest(BaseModel):
    """Request model for comparative analysis."""
    kol_ids: List[int] = Field(..., min_items=2, max_items=20)
    platform: str
    metric: str = Field("follower_count", regex="^(follower_count|engagement_rate|post_count)$")
    days: int = Field(30, ge=7, le=365)


class MetricDataPoint(BaseModel):
    """Single metric data point."""
    scraped_at: datetime
    follower_count: int
    following_count: int
    post_count: int
    engagement_rate: float
    avg_likes_per_post: float
    avg_comments_per_post: float
    avg_views_per_post: Optional[float] = None
    follower_growth: int
    follower_growth_rate: float
    engagement_growth_rate: float


class ProcessedMetricDataPoint(BaseModel):
    """Processed metric data point with period information."""
    period: str
    scraped_at: datetime
    follower_count: int
    following_count: int
    post_count: int
    engagement_rate: float
    avg_likes_per_post: float
    avg_comments_per_post: float
    follower_growth: int
    follower_growth_rate: float
    data_points_in_period: int


class SummaryStatistics(BaseModel):
    """Summary statistics for metrics."""
    follower_count: Dict[str, Any]
    engagement_rate: Dict[str, Any]
    data_quality: Dict[str, Any]


class TrendAnalysis(BaseModel):
    """Trend analysis results."""
    direction: str  # "up", "down", "stable", "volatile"
    strength: float
    confidence: float
    change_percentage: float
    period_days: int
    data_points: int


class HistoricalMetricsResponse(BaseModel):
    """Response model for historical metrics."""
    kol_id: int
    kol_name: str
    platform: str
    start_date: str
    end_date: str
    granularity: str
    data_points: int
    metrics: List[ProcessedMetricDataPoint]
    summary: SummaryStatistics
    trends: Dict[str, TrendAnalysis]
    retrieved_at: datetime


class FollowerMetrics(BaseModel):
    """Follower-related metrics."""
    start_followers: int
    end_followers: int
    total_growth: int
    growth_percentage: float
    daily_average_growth: float
    volatility_score: float
    consistency_score: float


class EngagementMetrics(BaseModel):
    """Engagement-related metrics."""
    current_rate: float
    average_rate: float
    trend: str
    trend_strength: float
    change_percentage: float


class PostMetrics(BaseModel):
    """Post-related metrics."""
    start_posts: int
    end_posts: int
    posts_added: int
    avg_posts_per_day: float


class QualityIndicators(BaseModel):
    """Quality indicators for growth analysis."""
    data_quality: str
    growth_quality: str
    engagement_quality: str


class PlatformGrowthAnalysis(BaseModel):
    """Growth analysis for a specific platform."""
    period_days: int
    data_points: int
    follower_metrics: FollowerMetrics
    engagement_metrics: EngagementMetrics
    post_metrics: PostMetrics
    quality_indicators: QualityIndicators


class GrowthAnalysisResponse(BaseModel):
    """Response model for growth analysis."""
    kol_id: int
    kol_name: str
    analysis_period_days: int
    platforms_analyzed: int
    growth_analysis: Dict[str, PlatformGrowthAnalysis]
    generated_at: datetime


class AnomalyResult(BaseModel):
    """Anomaly detection result."""
    anomaly_type: str
    category: str
    severity: str
    confidence: float
    description: str
    platform: str
    detected_at: datetime
    current_value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation_score: Optional[float] = None
    context_data: Optional[Dict[str, Any]] = None


class AnomalyDetectionResponse(BaseModel):
    """Response model for anomaly detection."""
    kol_id: int
    detection_window_days: int
    anomalies_detected: int
    alerts_created: int
    anomalies: List[AnomalyResult]
    detected_at: datetime


class StatisticalOutlier(BaseModel):
    """Statistical outlier result."""
    anomaly_type: str
    severity: str
    confidence: float
    description: str
    detected_at: datetime
    current_value: float
    expected_value: float
    z_score: float
    context_data: Dict[str, Any]


class StatisticalOutliersResponse(BaseModel):
    """Response model for statistical outliers."""
    kol_id: int
    platform: str
    metric: str
    window_days: int
    outliers_detected: int
    outliers: List[StatisticalOutlier]
    analyzed_at: datetime


class TrendAnomaly(BaseModel):
    """Trend anomaly result."""
    anomaly_type: str
    severity: str
    confidence: float
    description: str
    detected_at: datetime
    current_trend: float
    baseline_trend: float
    trend_change: float
    context_data: Dict[str, Any]


class TrendAnomaliesResponse(BaseModel):
    """Response model for trend anomalies."""
    kol_id: int
    platform: str
    metric: str
    trend_window_days: int
    trend_anomalies_detected: int
    trend_anomalies: List[TrendAnomaly]
    analyzed_at: datetime


class KOLComparisonData(BaseModel):
    """Comparison data for a single KOL."""
    kol_name: str
    current_value: float
    start_value: float
    growth: float
    growth_rate: float
    data_points: int
    average_value: float
    max_value: float
    min_value: float
    volatility: float


class KOLRanking(BaseModel):
    """KOL ranking entry."""
    kol_id: int
    kol_name: str
    value: Optional[float] = None
    growth_rate: Optional[float] = None


class Rankings(BaseModel):
    """Rankings for comparative analysis."""
    by_current_value: List[KOLRanking]
    by_growth_rate: List[KOLRanking]


class ComparativeAnalysisResponse(BaseModel):
    """Response model for comparative analysis."""
    platform: str
    metric: str
    period_days: int
    kols_compared: int
    valid_data_count: int
    comparison_data: Dict[int, KOLComparisonData]
    rankings: Rankings
    generated_at: datetime


class TrendsSummaryResponse(BaseModel):
    """Response model for trends summary."""
    summary_period_days: int
    platforms_analyzed: List[str]
    top_performers: List[Dict[str, Any]]
    trending_up: List[Dict[str, Any]]
    trending_down: List[Dict[str, Any]]
    anomalies_detected: int
    generated_at: datetime
    note: Optional[str] = None


class ArchiveDataResponse(BaseModel):
    """Response model for data archiving."""
    success: bool
    archived_count: int
    cutoff_date: datetime
    archived_at: datetime


class MetricsData(BaseModel):
    """Metrics data for system status."""
    total_metrics: int
    recent_metrics_24h: int
    data_coverage: str


class AlertsData(BaseModel):
    """Alerts data for system status."""
    total_alerts: int
    unread_alerts: int
    alert_rate: str


class AnalyticsFeatures(BaseModel):
    """Available analytics features."""
    historical_analysis: str
    anomaly_detection: str
    comparative_analysis: str
    trend_analysis: str


class AnalyticsSystemStatusResponse(BaseModel):
    """Response model for analytics system status."""
    system_status: str
    metrics_data: Optional[MetricsData] = None
    alerts_data: Optional[AlertsData] = None
    analytics_features: Optional[AnalyticsFeatures] = None
    last_updated: datetime
    error: Optional[str] = None