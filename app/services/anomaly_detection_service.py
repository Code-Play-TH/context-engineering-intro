"""Anomaly detection service for KOL performance monitoring."""
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, func
from fastapi import HTTPException, status
import logging
from dataclasses import dataclass
from enum import Enum

from app.models.kol import KOL
from app.models.kol_metrics import KOLMetrics
from app.models.performance_alert import PerformanceAlert, AlertType, AlertSeverity
from app.models.post import Post

logger = logging.getLogger(__name__)


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyCategory(str, Enum):
    """Categories of anomalies."""
    FOLLOWER_ANOMALY = "follower_anomaly"
    ENGAGEMENT_ANOMALY = "engagement_anomaly"
    CONTENT_ANOMALY = "content_anomaly"
    GROWTH_ANOMALY = "growth_anomaly"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    kol_id: int
    platform: str
    anomaly_type: str
    category: AnomalyCategory
    severity: AnomalySeverity
    confidence: float  # 0-1
    description: str
    detected_at: datetime
    current_value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation_score: Optional[float] = None
    context_data: Dict[str, Any] = None


class AnomalyDetectionService:
    """Service for detecting anomalies in KOL performance data."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Thresholds for different types of anomalies
        self.thresholds = {
            "follower_drop_minor": 5.0,      # % drop
            "follower_drop_major": 15.0,     # % drop
            "follower_drop_critical": 30.0,  # % drop
            "follower_spike_suspicious": 50.0,  # % increase
            "follower_spike_critical": 100.0,   # % increase
            "engagement_drop_minor": 15.0,   # % drop
            "engagement_drop_major": 30.0,   # % drop
            "engagement_spike": 200.0,       # % increase
            "growth_rate_suspicious": 25.0,  # Daily % growth
            "inactive_days": 7,              # Days without posts
            "post_frequency_drop": 50.0,     # % drop in posting frequency
            "engagement_consistency": 0.3,   # Volatility threshold
        }
        
        # Statistical parameters
        self.z_score_threshold = 2.0  # Standard deviations for outlier detection
        self.min_data_points = 5      # Minimum data points for statistical analysis
        self.lookback_days = 30       # Days to look back for baseline calculation
    
    async def detect_all_anomalies(
        self,
        kol_id: int,
        platforms: Optional[List[str]] = None,
        detection_window_days: int = 7
    ) -> List[AnomalyResult]:
        """Detect all types of anomalies for a KOL."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        if not platforms:
            platforms = [h.platform for h in kol.social_handles]
        
        all_anomalies = []
        
        for platform in platforms:
            # Get metrics for analysis
            metrics = await self._get_metrics_for_analysis(kol_id, platform, detection_window_days)
            
            if len(metrics) < 2:
                continue
            
            # Detect different types of anomalies
            platform_anomalies = []
            
            # 1. Follower count anomalies
            platform_anomalies.extend(await self._detect_follower_anomalies(kol_id, platform, metrics))
            
            # 2. Engagement rate anomalies
            platform_anomalies.extend(await self._detect_engagement_anomalies(kol_id, platform, metrics))
            
            # 3. Growth pattern anomalies
            platform_anomalies.extend(await self._detect_growth_anomalies(kol_id, platform, metrics))
            
            # 4. Content posting anomalies
            platform_anomalies.extend(await self._detect_content_anomalies(kol_id, platform))
            
            # 5. Behavioral anomalies
            platform_anomalies.extend(await self._detect_behavioral_anomalies(kol_id, platform, metrics))
            
            all_anomalies.extend(platform_anomalies)
        
        # Sort by severity and confidence
        all_anomalies.sort(key=lambda x: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}[x.severity.value],
            x.confidence
        ), reverse=True)
        
        return all_anomalies
    
    async def detect_statistical_outliers(
        self,
        kol_id: int,
        platform: str,
        metric_name: str = "follower_count",
        window_days: int = 30
    ) -> List[AnomalyResult]:
        """Detect statistical outliers using Z-score analysis."""
        metrics = await self._get_metrics_for_analysis(kol_id, platform, window_days)
        
        if len(metrics) < self.min_data_points:
            return []
        
        # Extract metric values
        if metric_name == "follower_count":
            values = [m.follower_count for m in metrics]
        elif metric_name == "engagement_rate":
            values = [float(m.engagement_rate) for m in metrics]
        elif metric_name == "post_count":
            values = [m.post_count for m in metrics]
        else:
            return []
        
        # Calculate statistical parameters
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return []  # No variation in data
        
        anomalies = []
        
        # Check each data point for outliers
        for i, (metric, value) in enumerate(zip(metrics, values)):
            z_score = abs(value - mean_val) / std_dev
            
            if z_score > self.z_score_threshold:
                severity = self._calculate_outlier_severity(z_score)
                
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type=f"{metric_name}_outlier",
                    category=AnomalyCategory.BEHAVIORAL_ANOMALY,
                    severity=severity,
                    confidence=min(1.0, z_score / 4.0),  # Normalize confidence
                    description=f"Statistical outlier detected in {metric_name}: {z_score:.2f} standard deviations from mean",
                    detected_at=metric.scraped_at,
                    current_value=float(value),
                    expected_value=mean_val,
                    deviation_score=z_score,
                    context_data={
                        "z_score": z_score,
                        "mean": mean_val,
                        "std_dev": std_dev,
                        "threshold": self.z_score_threshold
                    }
                ))
        
        return anomalies
    
    async def detect_trend_anomalies(
        self,
        kol_id: int,
        platform: str,
        metric_name: str = "follower_count",
        trend_window_days: int = 14
    ) -> List[AnomalyResult]:
        """Detect anomalies in trend patterns."""
        metrics = await self._get_metrics_for_analysis(kol_id, platform, trend_window_days * 2)
        
        if len(metrics) < trend_window_days:
            return []
        
        # Split into baseline and recent periods
        split_point = len(metrics) // 2
        baseline_metrics = metrics[:split_point]
        recent_metrics = metrics[split_point:]
        
        # Extract values
        if metric_name == "follower_count":
            baseline_values = [m.follower_count for m in baseline_metrics]
            recent_values = [m.follower_count for m in recent_metrics]
        elif metric_name == "engagement_rate":
            baseline_values = [float(m.engagement_rate) for m in baseline_metrics]
            recent_values = [float(m.engagement_rate) for m in recent_metrics]
        else:
            return []
        
        # Calculate trends
        baseline_trend = self._calculate_trend_slope(baseline_values)
        recent_trend = self._calculate_trend_slope(recent_values)
        
        anomalies = []
        
        # Detect trend reversals
        if baseline_trend > 0.1 and recent_trend < -0.1:  # Positive to negative
            anomalies.append(AnomalyResult(
                kol_id=kol_id,
                platform=platform,
                anomaly_type="trend_reversal_negative",
                category=AnomalyCategory.GROWTH_ANOMALY,
                severity=AnomalySeverity.MEDIUM,
                confidence=0.8,
                description=f"Trend reversal detected: {metric_name} changed from positive to negative trend",
                detected_at=recent_metrics[-1].scraped_at,
                current_value=recent_trend,
                expected_value=baseline_trend,
                context_data={
                    "baseline_trend": baseline_trend,
                    "recent_trend": recent_trend,
                    "trend_change": recent_trend - baseline_trend
                }
            ))
        
        elif baseline_trend < -0.1 and recent_trend > 0.1:  # Negative to positive (recovery)
            anomalies.append(AnomalyResult(
                kol_id=kol_id,
                platform=platform,
                anomaly_type="trend_reversal_positive",
                category=AnomalyCategory.GROWTH_ANOMALY,
                severity=AnomalySeverity.LOW,
                confidence=0.7,
                description=f"Positive trend reversal detected: {metric_name} recovered from negative trend",
                detected_at=recent_metrics[-1].scraped_at,
                current_value=recent_trend,
                expected_value=baseline_trend,
                context_data={
                    "baseline_trend": baseline_trend,
                    "recent_trend": recent_trend,
                    "trend_change": recent_trend - baseline_trend
                }
            ))
        
        # Detect acceleration/deceleration
        trend_change = abs(recent_trend - baseline_trend)
        if trend_change > 0.5:  # Significant trend change
            severity = AnomalySeverity.HIGH if trend_change > 1.0 else AnomalySeverity.MEDIUM
            
            anomalies.append(AnomalyResult(
                kol_id=kol_id,
                platform=platform,
                anomaly_type="trend_acceleration",
                category=AnomalyCategory.GROWTH_ANOMALY,
                severity=severity,
                confidence=min(1.0, trend_change / 2.0),
                description=f"Significant trend change detected in {metric_name}: {trend_change:.2f} change in slope",
                detected_at=recent_metrics[-1].scraped_at,
                current_value=recent_trend,
                expected_value=baseline_trend,
                deviation_score=trend_change,
                context_data={
                    "baseline_trend": baseline_trend,
                    "recent_trend": recent_trend,
                    "trend_change": trend_change
                }
            ))
        
        return anomalies
    
    async def _get_metrics_for_analysis(
        self,
        kol_id: int,
        platform: str,
        days: int
    ) -> List[KOLMetrics]:
        """Get metrics data for anomaly analysis."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        statement = select(KOLMetrics).where(
            and_(
                KOLMetrics.kol_id == kol_id,
                KOLMetrics.platform == platform,
                KOLMetrics.scraped_at >= cutoff_date,
                KOLMetrics.scraping_success == True
            )
        ).order_by(KOLMetrics.scraped_at.asc())
        
        return list(self.db.exec(statement).all())
    
    async def _detect_follower_anomalies(
        self,
        kol_id: int,
        platform: str,
        metrics: List[KOLMetrics]
    ) -> List[AnomalyResult]:
        """Detect follower count anomalies."""
        anomalies = []
        
        for i in range(1, len(metrics)):
            current = metrics[i]
            previous = metrics[i-1]
            
            if previous.follower_count == 0:
                continue
            
            change_percentage = ((current.follower_count - previous.follower_count) / previous.follower_count) * 100
            
            # Detect drops
            if change_percentage <= -self.thresholds["follower_drop_critical"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="follower_drop_critical",
                    category=AnomalyCategory.FOLLOWER_ANOMALY,
                    severity=AnomalySeverity.CRITICAL,
                    confidence=0.95,
                    description=f"Critical follower drop: {abs(change_percentage):.1f}% decrease",
                    detected_at=current.scraped_at,
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_score=abs(change_percentage),
                    context_data={"change_percentage": change_percentage}
                ))
            
            elif change_percentage <= -self.thresholds["follower_drop_major"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="follower_drop_major",
                    category=AnomalyCategory.FOLLOWER_ANOMALY,
                    severity=AnomalySeverity.HIGH,
                    confidence=0.9,
                    description=f"Major follower drop: {abs(change_percentage):.1f}% decrease",
                    detected_at=current.scraped_at,
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_score=abs(change_percentage),
                    context_data={"change_percentage": change_percentage}
                ))
            
            elif change_percentage <= -self.thresholds["follower_drop_minor"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="follower_drop_minor",
                    category=AnomalyCategory.FOLLOWER_ANOMALY,
                    severity=AnomalySeverity.MEDIUM,
                    confidence=0.8,
                    description=f"Follower drop detected: {abs(change_percentage):.1f}% decrease",
                    detected_at=current.scraped_at,
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_score=abs(change_percentage),
                    context_data={"change_percentage": change_percentage}
                ))
            
            # Detect suspicious spikes
            elif change_percentage >= self.thresholds["follower_spike_critical"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="follower_spike_critical",
                    category=AnomalyCategory.FOLLOWER_ANOMALY,
                    severity=AnomalySeverity.CRITICAL,
                    confidence=0.9,
                    description=f"Critical follower spike: {change_percentage:.1f}% increase (possible bot activity)",
                    detected_at=current.scraped_at,
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_score=change_percentage,
                    context_data={"change_percentage": change_percentage, "suspicious": True}
                ))
            
            elif change_percentage >= self.thresholds["follower_spike_suspicious"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="follower_spike_suspicious",
                    category=AnomalyCategory.FOLLOWER_ANOMALY,
                    severity=AnomalySeverity.HIGH,
                    confidence=0.8,
                    description=f"Suspicious follower spike: {change_percentage:.1f}% increase",
                    detected_at=current.scraped_at,
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_score=change_percentage,
                    context_data={"change_percentage": change_percentage, "suspicious": True}
                ))
        
        return anomalies
    
    async def _detect_engagement_anomalies(
        self,
        kol_id: int,
        platform: str,
        metrics: List[KOLMetrics]
    ) -> List[AnomalyResult]:
        """Detect engagement rate anomalies."""
        anomalies = []
        
        # Calculate baseline engagement rate
        engagement_rates = [float(m.engagement_rate) for m in metrics]
        if len(engagement_rates) < 3:
            return anomalies
        
        baseline_engagement = sum(engagement_rates[:-2]) / len(engagement_rates[:-2])
        
        for i in range(1, len(metrics)):
            current = metrics[i]
            current_engagement = float(current.engagement_rate)
            
            if baseline_engagement == 0:
                continue
            
            change_percentage = ((current_engagement - baseline_engagement) / baseline_engagement) * 100
            
            # Detect engagement drops
            if change_percentage <= -self.thresholds["engagement_drop_major"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="engagement_drop_major",
                    category=AnomalyCategory.ENGAGEMENT_ANOMALY,
                    severity=AnomalySeverity.HIGH,
                    confidence=0.85,
                    description=f"Major engagement drop: {abs(change_percentage):.1f}% below baseline",
                    detected_at=current.scraped_at,
                    current_value=current_engagement,
                    expected_value=baseline_engagement,
                    deviation_score=abs(change_percentage),
                    context_data={"change_percentage": change_percentage, "baseline": baseline_engagement}
                ))
            
            elif change_percentage <= -self.thresholds["engagement_drop_minor"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="engagement_drop_minor",
                    category=AnomalyCategory.ENGAGEMENT_ANOMALY,
                    severity=AnomalySeverity.MEDIUM,
                    confidence=0.75,
                    description=f"Engagement drop detected: {abs(change_percentage):.1f}% below baseline",
                    detected_at=current.scraped_at,
                    current_value=current_engagement,
                    expected_value=baseline_engagement,
                    deviation_score=abs(change_percentage),
                    context_data={"change_percentage": change_percentage, "baseline": baseline_engagement}
                ))
            
            # Detect unusual engagement spikes
            elif change_percentage >= self.thresholds["engagement_spike"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="engagement_spike",
                    category=AnomalyCategory.ENGAGEMENT_ANOMALY,
                    severity=AnomalySeverity.MEDIUM,
                    confidence=0.7,
                    description=f"Unusual engagement spike: {change_percentage:.1f}% above baseline",
                    detected_at=current.scraped_at,
                    current_value=current_engagement,
                    expected_value=baseline_engagement,
                    deviation_score=change_percentage,
                    context_data={"change_percentage": change_percentage, "baseline": baseline_engagement}
                ))
        
        return anomalies
    
    async def _detect_growth_anomalies(
        self,
        kol_id: int,
        platform: str,
        metrics: List[KOLMetrics]
    ) -> List[AnomalyResult]:
        """Detect growth pattern anomalies."""
        anomalies = []
        
        if len(metrics) < 3:
            return anomalies
        
        # Calculate daily growth rates
        daily_growth_rates = []
        for i in range(1, len(metrics)):
            current = metrics[i]
            previous = metrics[i-1]
            
            if previous.follower_count > 0:
                days_diff = (current.scraped_at - previous.scraped_at).days or 1
                growth_rate = ((current.follower_count - previous.follower_count) / previous.follower_count) * 100 / days_diff
                daily_growth_rates.append((current, growth_rate))
        
        # Detect suspicious consistent high growth
        consecutive_high_growth = 0
        for metric, growth_rate in daily_growth_rates:
            if growth_rate > self.thresholds["growth_rate_suspicious"]:
                consecutive_high_growth += 1
            else:
                consecutive_high_growth = 0
            
            # Alert if 3+ consecutive days of suspicious growth
            if consecutive_high_growth >= 3:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="suspicious_growth_pattern",
                    category=AnomalyCategory.GROWTH_ANOMALY,
                    severity=AnomalySeverity.HIGH,
                    confidence=0.85,
                    description=f"Suspicious growth pattern: {consecutive_high_growth} consecutive days of high growth (avg {growth_rate:.1f}%/day)",
                    detected_at=metric.scraped_at,
                    current_value=growth_rate,
                    expected_value=5.0,  # Normal daily growth
                    deviation_score=growth_rate - 5.0,
                    context_data={
                        "consecutive_days": consecutive_high_growth,
                        "daily_growth_rate": growth_rate
                    }
                ))
                consecutive_high_growth = 0  # Reset to avoid duplicate alerts
        
        return anomalies
    
    async def _detect_content_anomalies(
        self,
        kol_id: int,
        platform: str
    ) -> List[AnomalyResult]:
        """Detect content posting anomalies."""
        anomalies = []
        
        # Check for inactive periods
        cutoff_date = datetime.utcnow() - timedelta(days=self.thresholds["inactive_days"])
        
        statement = select(Post).where(
            and_(
                Post.kol_id == kol_id,
                Post.platform == platform,
                Post.posted_at >= cutoff_date
            )
        )
        
        recent_posts = self.db.exec(statement).all()
        
        if not recent_posts:
            anomalies.append(AnomalyResult(
                kol_id=kol_id,
                platform=platform,
                anomaly_type="inactive_period",
                category=AnomalyCategory.CONTENT_ANOMALY,
                severity=AnomalySeverity.MEDIUM,
                confidence=0.9,
                description=f"No posts detected in the last {self.thresholds['inactive_days']} days",
                detected_at=datetime.utcnow(),
                current_value=0,
                expected_value=1,
                context_data={"inactive_days": self.thresholds["inactive_days"]}
            ))
        
        # Check posting frequency changes
        # Get posts from last 30 days and previous 30 days for comparison
        now = datetime.utcnow()
        recent_period_start = now - timedelta(days=30)
        baseline_period_start = now - timedelta(days=60)
        baseline_period_end = recent_period_start
        
        recent_posts_count = len(self.db.exec(
            select(Post).where(
                and_(
                    Post.kol_id == kol_id,
                    Post.platform == platform,
                    Post.posted_at >= recent_period_start
                )
            )
        ).all())
        
        baseline_posts_count = len(self.db.exec(
            select(Post).where(
                and_(
                    Post.kol_id == kol_id,
                    Post.platform == platform,
                    Post.posted_at >= baseline_period_start,
                    Post.posted_at < baseline_period_end
                )
            )
        ).all())
        
        if baseline_posts_count > 0:
            frequency_change = ((recent_posts_count - baseline_posts_count) / baseline_posts_count) * 100
            
            if frequency_change <= -self.thresholds["post_frequency_drop"]:
                anomalies.append(AnomalyResult(
                    kol_id=kol_id,
                    platform=platform,
                    anomaly_type="posting_frequency_drop",
                    category=AnomalyCategory.CONTENT_ANOMALY,
                    severity=AnomalySeverity.MEDIUM,
                    confidence=0.8,
                    description=f"Posting frequency dropped by {abs(frequency_change):.1f}%",
                    detected_at=datetime.utcnow(),
                    current_value=float(recent_posts_count),
                    expected_value=float(baseline_posts_count),
                    deviation_score=abs(frequency_change),
                    context_data={
                        "recent_posts": recent_posts_count,
                        "baseline_posts": baseline_posts_count,
                        "frequency_change": frequency_change
                    }
                ))
        
        return anomalies
    
    async def _detect_behavioral_anomalies(
        self,
        kol_id: int,
        platform: str,
        metrics: List[KOLMetrics]
    ) -> List[AnomalyResult]:
        """Detect behavioral anomalies in engagement patterns."""
        anomalies = []
        
        if len(metrics) < 5:
            return anomalies
        
        # Check engagement consistency
        engagement_rates = [float(m.engagement_rate) for m in metrics]
        engagement_volatility = self._calculate_volatility(engagement_rates)
        
        if engagement_volatility > self.thresholds["engagement_consistency"]:
            anomalies.append(AnomalyResult(
                kol_id=kol_id,
                platform=platform,
                anomaly_type="engagement_inconsistency",
                category=AnomalyCategory.BEHAVIORAL_ANOMALY,
                severity=AnomalySeverity.MEDIUM,
                confidence=0.75,
                description=f"High engagement volatility detected: {engagement_volatility:.2f}",
                detected_at=metrics[-1].scraped_at,
                current_value=engagement_volatility,
                expected_value=self.thresholds["engagement_consistency"],
                deviation_score=engagement_volatility - self.thresholds["engagement_consistency"],
                context_data={
                    "volatility": engagement_volatility,
                    "threshold": self.thresholds["engagement_consistency"],
                    "engagement_rates": engagement_rates[-5:]  # Last 5 values
                }
            ))
        
        return anomalies
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate the slope of a trend line using linear regression."""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation (volatility)."""
        if len(values) < 2:
            return 0.0
        
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        
        return std_dev / mean_val
    
    def _calculate_outlier_severity(self, z_score: float) -> AnomalySeverity:
        """Calculate severity based on Z-score."""
        if z_score > 4.0:
            return AnomalySeverity.CRITICAL
        elif z_score > 3.0:
            return AnomalySeverity.HIGH
        elif z_score > 2.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    async def create_performance_alerts(
        self,
        anomalies: List[AnomalyResult],
        auto_create: bool = True
    ) -> List[PerformanceAlert]:
        """Create performance alerts from detected anomalies."""
        if not auto_create:
            return []
        
        alerts = []
        
        for anomaly in anomalies:
            # Only create alerts for medium+ severity anomalies
            if anomaly.severity in [AnomalySeverity.MEDIUM, AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                
                # Map anomaly types to alert types
                alert_type_map = {
                    "follower_drop_critical": AlertType.FOLLOWER_DROP,
                    "follower_drop_major": AlertType.FOLLOWER_DROP,
                    "follower_drop_minor": AlertType.FOLLOWER_DROP,
                    "follower_spike_critical": AlertType.FOLLOWER_SPIKE,
                    "follower_spike_suspicious": AlertType.FOLLOWER_SPIKE,
                    "engagement_drop_major": AlertType.ENGAGEMENT_DROP,
                    "engagement_drop_minor": AlertType.ENGAGEMENT_DROP,
                    "engagement_spike": AlertType.ENGAGEMENT_SPIKE,
                }
                
                alert_type = alert_type_map.get(anomaly.anomaly_type, AlertType.ENGAGEMENT_DROP)
                
                # Map severity
                severity_map = {
                    AnomalySeverity.LOW: AlertSeverity.INFO,
                    AnomalySeverity.MEDIUM: AlertSeverity.WARNING,
                    AnomalySeverity.HIGH: AlertSeverity.CRITICAL,
                    AnomalySeverity.CRITICAL: AlertSeverity.CRITICAL
                }
                
                alert = PerformanceAlert(
                    kol_id=anomaly.kol_id,
                    alert_type=alert_type,
                    severity=severity_map[anomaly.severity],
                    title=f"Anomaly Detected - {anomaly.platform.title()}",
                    message=anomaly.description,
                    actual_value=anomaly.current_value,
                    previous_value=anomaly.expected_value,
                    context_data={
                        "platform": anomaly.platform,
                        "anomaly_type": anomaly.anomaly_type,
                        "confidence": anomaly.confidence,
                        "deviation_score": anomaly.deviation_score,
                        "detected_by": "anomaly_detection_service",
                        **(anomaly.context_data or {})
                    }
                )
                
                self.db.add(alert)
                alerts.append(alert)
        
        if alerts:
            self.db.commit()
            logger.info(f"Created {len(alerts)} performance alerts from anomaly detection")
        
        return alerts