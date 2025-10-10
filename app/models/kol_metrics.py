"""KOL metrics model for storing historical social media performance data."""
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship
from app.models.post import SocialPlatform


class KOLMetrics(SQLModel, table=True):
    """Model for storing KOL social media metrics over time.
    
    This table will be partitioned by month for better performance.
    """
    __tablename__ = "kol_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kols.id", index=True)
    platform: SocialPlatform = Field(index=True)
    
    # Follower metrics
    follower_count: int = Field(default=0)
    following_count: int = Field(default=0)
    
    # Content metrics
    post_count: int = Field(default=0)
    video_count: Optional[int] = Field(default=None)  # For TikTok, YouTube
    
    # Engagement metrics
    total_likes: Optional[int] = Field(default=None)
    total_comments: Optional[int] = Field(default=None)
    total_shares: Optional[int] = Field(default=None)
    total_views: Optional[int] = Field(default=None)
    
    # Calculated metrics
    engagement_rate: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    avg_likes_per_post: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    avg_comments_per_post: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    avg_views_per_post: Optional[Decimal] = Field(default=None, max_digits=15, decimal_places=2)
    
    # Growth metrics (compared to previous scraping)
    follower_growth: int = Field(default=0)
    follower_growth_rate: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    engagement_growth_rate: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    
    # Platform-specific metrics (stored as JSON)
    platform_specific_data: Dict[str, Any] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    
    # Collection metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    scraping_duration_seconds: Optional[float] = Field(default=None)
    scraping_success: bool = Field(default=True)
    scraping_error: Optional[str] = Field(default=None)
    
    # Data quality indicators
    is_estimated: bool = Field(default=False)  # If some metrics are estimated
    confidence_score: Decimal = Field(default=100, max_digits=5, decimal_places=2)  # 0-100
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    kol: Optional["KOL"] = Relationship(back_populates="metrics")
    
    def calculate_engagement_rate(self, recent_posts_data: Optional[list] = None) -> Decimal:
        """Calculate engagement rate based on recent posts or total metrics."""
        if self.follower_count == 0:
            self.engagement_rate = Decimal('0.00')
            return self.engagement_rate
        
        if recent_posts_data:
            # Calculate from recent posts (more accurate)
            total_engagement = sum(
                post.get('likes', 0) + post.get('comments', 0) + post.get('shares', 0)
                for post in recent_posts_data
            )
            if len(recent_posts_data) > 0:
                avg_engagement = total_engagement / len(recent_posts_data)
                rate = (avg_engagement / self.follower_count) * 100
                self.engagement_rate = Decimal(str(round(rate, 2)))
        else:
            # Calculate from total metrics (less accurate but available)
            if self.post_count > 0:
                avg_engagement = (
                    (self.total_likes or 0) + 
                    (self.total_comments or 0) + 
                    (self.total_shares or 0)
                ) / self.post_count
                rate = (avg_engagement / self.follower_count) * 100
                self.engagement_rate = Decimal(str(round(rate, 2)))
        
        return self.engagement_rate
    
    def calculate_average_metrics(self) -> None:
        """Calculate average metrics per post."""
        if self.post_count == 0:
            return
        
        if self.total_likes is not None:
            self.avg_likes_per_post = Decimal(str(round(self.total_likes / self.post_count, 2)))
        
        if self.total_comments is not None:
            self.avg_comments_per_post = Decimal(str(round(self.total_comments / self.post_count, 2)))
        
        if self.total_views is not None:
            self.avg_views_per_post = Decimal(str(round(self.total_views / self.post_count, 2)))
    
    def calculate_growth_from_previous(self, previous_metrics: Optional["KOLMetrics"]) -> None:
        """Calculate growth metrics compared to previous scraping."""
        if not previous_metrics:
            self.follower_growth = 0
            self.follower_growth_rate = Decimal('0.00')
            self.engagement_growth_rate = Decimal('0.00')
            return
        
        # Follower growth
        self.follower_growth = self.follower_count - previous_metrics.follower_count
        
        if previous_metrics.follower_count > 0:
            growth_rate = (self.follower_growth / previous_metrics.follower_count) * 100
            self.follower_growth_rate = Decimal(str(round(growth_rate, 2)))
        
        # Engagement growth rate
        if previous_metrics.engagement_rate > 0:
            eng_growth = float(self.engagement_rate) - float(previous_metrics.engagement_rate)
            eng_growth_rate = (eng_growth / float(previous_metrics.engagement_rate)) * 100
            self.engagement_growth_rate = Decimal(str(round(eng_growth_rate, 2)))
    
    def detect_anomalies(self, previous_metrics: Optional["KOLMetrics"]) -> list:
        """Detect anomalies in metrics that might indicate issues."""
        anomalies = []
        
        if not previous_metrics:
            return anomalies
        
        # Significant follower drop (>10% in one scraping)
        if self.follower_growth < 0:
            drop_percentage = abs(self.follower_growth / previous_metrics.follower_count) * 100
            if drop_percentage > 10:
                anomalies.append({
                    "type": "follower_drop",
                    "severity": "high" if drop_percentage > 20 else "medium",
                    "message": f"Follower count dropped by {drop_percentage:.1f}%",
                    "value": drop_percentage
                })
        
        # Suspicious follower spike (>50% in one scraping)
        if self.follower_growth > 0:
            growth_percentage = (self.follower_growth / previous_metrics.follower_count) * 100
            if growth_percentage > 50:
                anomalies.append({
                    "type": "follower_spike",
                    "severity": "medium",
                    "message": f"Follower count increased by {growth_percentage:.1f}% (possible bot followers)",
                    "value": growth_percentage
                })
        
        # Significant engagement rate change (>20%)
        if previous_metrics.engagement_rate > 0:
            eng_change = abs(float(self.engagement_rate) - float(previous_metrics.engagement_rate))
            eng_change_percentage = (eng_change / float(previous_metrics.engagement_rate)) * 100
            if eng_change_percentage > 20:
                direction = "increased" if self.engagement_rate > previous_metrics.engagement_rate else "decreased"
                anomalies.append({
                    "type": "engagement_change",
                    "severity": "medium",
                    "message": f"Engagement rate {direction} by {eng_change_percentage:.1f}%",
                    "value": eng_change_percentage
                })
        
        return anomalies
    
    def get_platform_specific_metric(self, key: str, default=None):
        """Get platform-specific metric value."""
        return self.platform_specific_data.get(key, default)
    
    def set_platform_specific_metric(self, key: str, value) -> None:
        """Set platform-specific metric value."""
        if not self.platform_specific_data:
            self.platform_specific_data = {}
        self.platform_specific_data[key] = value
    
    def is_recent(self, hours: int = 24) -> bool:
        """Check if metrics are recent (within specified hours)."""
        time_diff = datetime.utcnow() - self.scraped_at
        return time_diff.total_seconds() < (hours * 3600)
    
    def get_quality_score(self) -> float:
        """Get overall data quality score."""
        score = float(self.confidence_score)
        
        # Reduce score if scraping failed
        if not self.scraping_success:
            score *= 0.5
        
        # Reduce score if data is estimated
        if self.is_estimated:
            score *= 0.8
        
        # Reduce score if data is old
        if not self.is_recent(24):
            age_hours = (datetime.utcnow() - self.scraped_at).total_seconds() / 3600
            if age_hours > 168:  # More than a week old
                score *= 0.6
            elif age_hours > 72:  # More than 3 days old
                score *= 0.8
        
        return min(100.0, max(0.0, score))