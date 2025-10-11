"""Pydantic schemas for performance tracking API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RefreshRequest(BaseModel):
    """Request model for manual refresh."""
    platforms: Optional[List[str]] = Field(None, description="Specific platforms to refresh")
    include_posts: bool = Field(True, description="Include recent posts in refresh")


class BulkRefreshRequest(BaseModel):
    """Request model for bulk refresh."""
    kol_ids: List[int] = Field(..., min_items=1, max_items=50, description="List of KOL IDs to refresh")
    platforms: Optional[List[str]] = Field(None, description="Specific platforms to refresh")
    include_posts: bool = Field(False, description="Include recent posts in refresh")


class RefreshStatusResponse(BaseModel):
    """Response model for refresh status."""
    refresh_id: str
    kol_id: int
    status: str
    progress: int = Field(..., ge=0, le=100)
    total_platforms: int
    platforms: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float
    results: Dict[str, Any] = {}
    errors: List[str] = []


class RefreshResponse(BaseModel):
    """Response model for refresh initiation."""
    refresh_id: str
    status: str
    kol_id: int
    platforms: List[str]
    include_posts: bool
    estimated_duration_seconds: int
    started_at: datetime
    triggered_by: Optional[str] = None
    triggered_at: Optional[datetime] = None


class MetricsResponse(BaseModel):
    """Response model for KOL metrics."""
    kol_id: int
    kol_name: str
    last_scraped_at: Optional[datetime]
    metrics: Dict[str, Any]
    platforms_available: int
    retrieved_at: datetime


class PlatformMetrics(BaseModel):
    """Platform-specific metrics."""
    id: int
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
    scraped_at: datetime
    scraping_success: bool
    platform_specific_data: Dict[str, Any] = {}
    quality_score: float


class HistoricalMetricsResponse(BaseModel):
    """Response model for historical metrics."""
    kol_id: int
    kol_name: str
    platform: str
    period_days: int
    data_points: int
    metrics: List[Dict[str, Any]]
    trends: Dict[str, Any]
    retrieved_at: datetime


class HistoricalDataPoint(BaseModel):
    """Single historical data point."""
    scraped_at: datetime
    follower_count: int
    engagement_rate: float
    follower_growth: int
    follower_growth_rate: float
    post_count: int


class TrendsAnalysis(BaseModel):
    """Trends analysis data."""
    follower_trend: str  # "up" or "down"
    engagement_trend: str  # "up" or "down"
    total_follower_growth: int
    avg_daily_growth: float
    growth_rate_percentage: float
    data_quality: str  # "good" or "limited"


class GrowthAnalyticsResponse(BaseModel):
    """Response model for growth analytics."""
    kol_id: int
    kol_name: str
    analytics: Dict[str, Any]
    generated_at: datetime


class PlatformAnalytics(BaseModel):
    """Analytics for a specific platform."""
    current_followers: int
    follower_growth_30d: int
    daily_growth_rate: float
    growth_percentage: float
    current_engagement_rate: float
    avg_engagement_rate_30d: float
    engagement_trend: str  # "up" or "down"
    data_points: int
    analysis_period_days: int
    anomalies: List[str]
    last_updated: datetime


class PerformanceIssue(BaseModel):
    """Performance issue detection."""
    type: str  # "follower_drop", "engagement_drop", etc.
    platform: str
    severity: str  # "low", "medium", "high"
    message: str
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    detected_at: datetime


class PerformanceIssuesResponse(BaseModel):
    """Response model for performance issues."""
    kol_id: int
    issues: List[PerformanceIssue]
    total_issues: int
    critical_issues: int
    detected_at: datetime


class BulkRefreshResponse(BaseModel):
    """Response model for bulk refresh."""
    total_kols: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    triggered_by: str
    triggered_at: datetime


class BulkRefreshResult(BaseModel):
    """Individual result in bulk refresh."""
    kol_id: int
    success: bool
    refresh_id: Optional[str] = None
    error: Optional[str] = None


class ActiveRefreshOperation(BaseModel):
    """Active refresh operation info."""
    refresh_id: str
    kol_id: int
    status: str
    progress: int
    platforms: List[str]
    started_at: datetime
    duration_seconds: float


class ActiveRefreshOperationsResponse(BaseModel):
    """Response model for active refresh operations."""
    active_operations: List[ActiveRefreshOperation]
    total_active: int
    retrieved_at: datetime


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    system_status: str  # "operational", "degraded", "down"
    timestamp: datetime
    scraping_system: Dict[str, Any]
    active_refresh_operations: int
    platform_configs: List[str]
    rate_limit_status: Dict[str, Any]
    error: Optional[str] = None


class CleanupResponse(BaseModel):
    """Response model for cleanup operations."""
    success: bool
    cleaned_operations: int
    cleanup_threshold_hours: int
    cleaned_at: datetime


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "status_update", "final_update", "error"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WebSocketStatusUpdate(BaseModel):
    """WebSocket status update message."""
    type: str = "status_update"
    data: RefreshStatusResponse


class WebSocketFinalUpdate(BaseModel):
    """WebSocket final update message."""
    type: str = "final_update"
    data: RefreshStatusResponse


class WebSocketError(BaseModel):
    """WebSocket error message."""
    type: str = "error"
    error: str