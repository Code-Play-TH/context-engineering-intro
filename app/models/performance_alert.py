"""Performance alert model for tracking KOL and campaign performance issues."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from enum import Enum


class AlertType(str, Enum):
    """Types of performance alerts."""
    ENGAGEMENT_DROP = "engagement_drop"
    FOLLOWER_DROP = "follower_drop"
    FOLLOWER_SPIKE = "follower_spike"  # Possible bot followers
    MISSED_DEADLINE = "missed_deadline"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    POST_UNDERPERFORMING = "post_underperforming"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SCRAPING_FAILED = "scraping_failed"
    KPI_MISS_PROJECTED = "kpi_miss_projected"
    CONTENT_NOT_POSTED = "content_not_posted"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status options."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class PerformanceAlert(SQLModel, table=True):
    """Model for tracking performance alerts and issues."""
    __tablename__ = "performance_alerts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: Optional[int] = Field(foreign_key="kols.id", index=True, default=None)
    campaign_id: Optional[int] = Field(foreign_key="campaigns.id", index=True, default=None)
    post_id: Optional[int] = Field(foreign_key="posts.id", index=True, default=None)
    
    # Alert details
    alert_type: AlertType = Field(index=True)
    severity: AlertSeverity = Field(default=AlertSeverity.WARNING, index=True)
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, index=True)
    
    # Message and context
    title: str
    message: str
    context_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Thresholds and values
    threshold_value: Optional[float] = Field(default=None)
    actual_value: Optional[float] = Field(default=None)
    previous_value: Optional[float] = Field(default=None)
    
    # Management
    is_acknowledged: bool = Field(default=False, index=True)
    acknowledged_by: Optional[int] = Field(foreign_key="users.id", default=None)
    acknowledged_at: Optional[datetime] = Field(default=None)
    acknowledgment_note: Optional[str] = Field(default=None)
    
    # Auto-resolution
    auto_resolve_at: Optional[datetime] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_note: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    kol: Optional["KOL"] = Relationship(back_populates="performance_alerts")
    campaign: Optional["Campaign"] = Relationship(back_populates="performance_alerts")
    post: Optional["Post"] = Relationship()
    acknowledged_by_user: Optional["User"] = Relationship()
    
    def acknowledge(self, user_id: int, note: Optional[str] = None) -> None:
        """Acknowledge the alert."""
        self.is_acknowledged = True
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
        self.acknowledgment_note = note
        self.updated_at = datetime.utcnow()
    
    def resolve(self, note: Optional[str] = None) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolution_note = note
        self.updated_at = datetime.utcnow()
    
    def dismiss(self, note: Optional[str] = None) -> None:
        """Dismiss the alert."""
        self.status = AlertStatus.DISMISSED
        self.resolved_at = datetime.utcnow()
        self.resolution_note = note
        self.updated_at = datetime.utcnow()
    
    def should_auto_resolve(self) -> bool:
        """Check if alert should be auto-resolved."""
        if not self.auto_resolve_at:
            return False
        
        return datetime.utcnow() >= self.auto_resolve_at
    
    def get_severity_color(self) -> str:
        """Get color code for alert severity."""
        colors = {
            AlertSeverity.INFO: "#3b82f6",      # Blue
            AlertSeverity.WARNING: "#f59e0b",   # Yellow
            AlertSeverity.CRITICAL: "#ef4444"  # Red
        }
        return colors.get(self.severity, "#6b7280")  # Gray default
    
    def get_type_icon(self) -> str:
        """Get icon for alert type."""
        icons = {
            AlertType.ENGAGEMENT_DROP: "📉",
            AlertType.FOLLOWER_DROP: "👥",
            AlertType.FOLLOWER_SPIKE: "🚀",
            AlertType.MISSED_DEADLINE: "⏰",
            AlertType.NEGATIVE_SENTIMENT: "😞",
            AlertType.POST_UNDERPERFORMING: "📊",
            AlertType.RATE_LIMIT_EXCEEDED: "🚫",
            AlertType.SCRAPING_FAILED: "⚠️",
            AlertType.KPI_MISS_PROJECTED: "🎯",
            AlertType.CONTENT_NOT_POSTED: "📝"
        }
        return icons.get(self.alert_type, "🔔")
    
    def format_message_with_context(self) -> str:
        """Format message with context data."""
        message = self.message
        
        # Replace placeholders with context data
        for key, value in self.context_data.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        
        return message
    
    @classmethod
    def create_engagement_drop_alert(
        cls,
        kol_id: int,
        current_rate: float,
        previous_rate: float,
        threshold: float,
        campaign_id: Optional[int] = None
    ) -> "PerformanceAlert":
        """Create an engagement drop alert."""
        drop_percentage = ((previous_rate - current_rate) / previous_rate) * 100
        
        return cls(
            kol_id=kol_id,
            campaign_id=campaign_id,
            alert_type=AlertType.ENGAGEMENT_DROP,
            severity=AlertSeverity.WARNING if drop_percentage < 50 else AlertSeverity.CRITICAL,
            title="Engagement Rate Drop Detected",
            message=f"Engagement rate dropped from {previous_rate:.2f}% to {current_rate:.2f}% ({drop_percentage:.1f}% decrease)",
            threshold_value=threshold,
            actual_value=current_rate,
            previous_value=previous_rate,
            context_data={
                "drop_percentage": round(drop_percentage, 1),
                "threshold": threshold,
                "current_rate": current_rate,
                "previous_rate": previous_rate
            }
        )
    
    @classmethod
    def create_follower_drop_alert(
        cls,
        kol_id: int,
        current_count: int,
        previous_count: int,
        platform: str
    ) -> "PerformanceAlert":
        """Create a follower drop alert."""
        drop_count = previous_count - current_count
        drop_percentage = (drop_count / previous_count) * 100
        
        return cls(
            kol_id=kol_id,
            alert_type=AlertType.FOLLOWER_DROP,
            severity=AlertSeverity.WARNING if drop_percentage < 20 else AlertSeverity.CRITICAL,
            title=f"{platform.title()} Follower Drop",
            message=f"Lost {drop_count:,} followers on {platform} ({drop_percentage:.1f}% decrease)",
            actual_value=current_count,
            previous_value=previous_count,
            context_data={
                "platform": platform,
                "drop_count": drop_count,
                "drop_percentage": round(drop_percentage, 1),
                "current_count": current_count,
                "previous_count": previous_count
            }
        )