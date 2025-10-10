"""Post metrics model for tracking social media post performance over time."""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class CollectionInterval(str, Enum):
    """Post metrics collection intervals."""
    INITIAL = "initial"  # At detection
    HOUR_24 = "24hr"
    DAY_3 = "3day"
    DAY_5 = "5day"
    DAY_7 = "7day"
    DAY_14 = "14day"
    DAY_30 = "30day"


class PostMetrics(SQLModel, table=True):
    """Model for tracking post performance metrics over time.
    
    This table will be partitioned by month for better performance.
    """
    __tablename__ = "post_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id", index=True)
    
    # Metrics
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    views: Optional[int] = Field(default=None)
    saves: Optional[int] = Field(default=None)  # Instagram/TikTok specific
    
    # Calculated metrics
    engagement_rate: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    engagement_count: int = Field(default=0)  # likes + comments + shares
    
    # Collection metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    collection_interval: CollectionInterval = Field(index=True)
    
    # Growth since previous collection
    likes_growth: int = Field(default=0)
    comments_growth: int = Field(default=0)
    shares_growth: int = Field(default=0)
    views_growth: Optional[int] = Field(default=None)
    
    # Performance indicators
    is_viral: bool = Field(default=False)  # Engagement significantly above average
    is_underperforming: bool = Field(default=False)  # Engagement below threshold
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    post: Optional["Post"] = Relationship(back_populates="metrics")
    
    def calculate_engagement_rate(self, follower_count: int) -> Decimal:
        """Calculate engagement rate based on follower count."""
        if follower_count == 0:
            return Decimal('0.00')
        
        self.engagement_count = self.likes + self.comments + self.shares
        rate = (self.engagement_count / follower_count) * 100
        self.engagement_rate = Decimal(str(round(rate, 2)))
        return self.engagement_rate
    
    def calculate_growth_from_previous(self, previous_metrics: Optional["PostMetrics"]) -> None:
        """Calculate growth metrics compared to previous collection."""
        if not previous_metrics:
            self.likes_growth = self.likes
            self.comments_growth = self.comments
            self.shares_growth = self.shares
            self.views_growth = self.views
            return
        
        self.likes_growth = self.likes - previous_metrics.likes
        self.comments_growth = self.comments - previous_metrics.comments
        self.shares_growth = self.shares - previous_metrics.shares
        
        if self.views is not None and previous_metrics.views is not None:
            self.views_growth = self.views - previous_metrics.views
    
    def check_performance_status(self, kol_average_engagement: float, viral_threshold: float = 5.0) -> None:
        """Check if post is viral or underperforming."""
        engagement_rate_float = float(self.engagement_rate)
        
        # Check if viral (engagement rate 5x above KOL average)
        if engagement_rate_float >= (kol_average_engagement * viral_threshold):
            self.is_viral = True
        
        # Check if underperforming (engagement rate below 50% of KOL average)
        if engagement_rate_float < (kol_average_engagement * 0.5):
            self.is_underperforming = True
    
    def get_growth_percentage(self, metric: str) -> Optional[float]:
        """Get growth percentage for a specific metric."""
        current_value = getattr(self, metric, 0)
        growth_value = getattr(self, f"{metric}_growth", 0)
        
        if current_value == 0 or growth_value == 0:
            return None
        
        previous_value = current_value - growth_value
        if previous_value == 0:
            return 100.0  # 100% growth from 0
        
        return (growth_value / previous_value) * 100