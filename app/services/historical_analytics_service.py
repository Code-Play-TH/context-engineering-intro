"""Historical data tracking and analytics service for KOL performance metrics."""
import math
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, or_, func, text
from fastapi import HTTPException, status
import logging
from dataclasses import dataclass
from enum import Enum

from app.models.kol import KOL
from app.models.kol_metrics import KOLMetrics
from app.models.performance_alert import PerformanceAlert, AlertType, AlertSeverity
from app.models.campaign import Campaign
from app.models.brief import Brief

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    FOLLOWER_DROP = "follower_drop"
    FOLLOWER_SPIKE = "follower_spike"
    ENGAGEMENT_DROP = "engagement_drop"
    ENGAGEMENT_SPIKE = "engagement_spike"
    SUSPICIOUS_GROWTH = "suspicious_growth"
    INACTIVE_PERIOD = "inactive_period"


@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    direction: TrendDirection
    strength: float  # 0-1, how strong the trend is
    confidence: float  # 0-1, confidence in the trend
    change_percentage: float
    period_days: int
    data_points: int


@dataclass
class AnomalyDetection:
    """Anomaly detection result."""
    anomaly_type: AnomalyType
    severity: str  # "low", "medium", "high"
    confidence: float  # 0-1
    detected_at: datetime
    description: str
    current_value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation_percentage: Optional[float] = None


class HistoricalAnalyticsService:
    """Service for historical data tracking and analytics."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Configuration for anomaly detection
        self.follower_drop_threshold = 10.0  # % drop to trigger alert
        self.follower_spike_threshold = 50.0  # % increase to trigger suspicious growth alert
        self.engagement_drop_threshold = 20.0  # % drop to trigger alert
        self.engagement_spike_threshold = 100.0  # % increase to trigger alert
        self.inactive_days_threshold = 7  # Days without new posts
        
        # Trend analysis configuration
        self.min_data_points = 5  # Minimum data points for trend analysis
        self.trend_confidence_threshold = 0.7  # Minimum confidence for trend detection
    
    async def get_historical_metrics(
        self,
        kol_id: int,
        platform: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None,
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """Get historical metrics for a KOL on a specific platform."""
        # Validate KOL exists
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Determine date range
        if days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        elif not start_date or not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)  # Default 30 days
        
        # Get metrics data
        statement = select(KOLMetrics).where(
            and_(
                KOLMetrics.kol_id == kol_id,
                KOLMetrics.platform == platform,
                KOLMetrics.scraped_at >= datetime.combine(start_date, datetime.min.time()),
                KOLMetrics.scraped_at <= datetime.combine(end_date, datetime.max.time()),
                KOLMetrics.scraping_success == True
            )
        ).order_by(KOLMetrics.scraped_at.asc())
        
        metrics = self.db.exec(statement).all()
        
        if not metrics:
            return {
                "kol_id": kol_id,
                "kol_name": kol.name,
                "platform": platform,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": granularity,
                "data_points": 0,
                "metrics": [],
                "summary": {},
                "trends": {}
            }
        
        # Process metrics based on granularity
        processed_metrics = self._process_metrics_by_granularity(metrics, granularity)
        
        # Calculate summary statistics
        summary = self._calculate_summary_statistics(processed_metrics)
        
        # Perform trend analysis
        trends = self._analyze_trends(processed_metrics)
        
        return {
            "kol_id": kol_id,
            "kol_name": kol.name,
            "platform": platform,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "granularity": granularity,
            "data_points": len(processed_metrics),
            "metrics": processed_metrics,
            "summary": summary,
            "trends": trends,
            "retrieved_at": datetime.utcnow()
        }
    
    async def get_growth_analysis(
        self,
        kol_id: int,
        platforms: Optional[List[str]] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive growth analysis for a KOL."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Get platforms to analyze
        if not platforms:
            platforms = [h.platform for h in kol.social_handles]
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        growth_analysis = {}
        
        for platform in platforms:
            # Get metrics for this platform
            statement = select(KOLMetrics).where(
                and_(
                    KOLMetrics.kol_id == kol_id,
                    KOLMetrics.platform == platform,
                    KOLMetrics.scraped_at >= start_date,
                    KOLMetrics.scraping_success == True
                )
            ).order_by(KOLMetrics.scraped_at.asc())
            
            metrics = self.db.exec(statement).all()
            
            if len(metrics) < 2:
                growth_analysis[platform] = {
                    "error": "Insufficient data for growth analysis",
                    "data_points": len(metrics)
                }
                continue
            
            # Calculate growth metrics
            first_metric = metrics[0]
            latest_metric = metrics[-1]
            
            # Follower growth
            follower_growth = latest_metric.follower_count - first_metric.follower_count
            follower_growth_rate = (follower_growth / first_metric.follower_count * 100) if first_metric.follower_count > 0 else 0
            
            # Daily average growth
            days_span = (latest_metric.scraped_at - first_metric.scraped_at).days or 1
            daily_growth = follower_growth / days_span
            
            # Engagement analysis
            engagement_values = [float(m.engagement_rate) for m in metrics]
            avg_engagement = sum(engagement_values) / len(engagement_values)
            engagement_trend = self._calculate_engagement_trend(engagement_values)
            
            # Volatility analysis
            volatility = self._calculate_volatility([m.follower_count for m in metrics])
            
            # Growth consistency
            consistency_score = self._calculate_growth_consistency(metrics)
            
            growth_analysis[platform] = {
                "period_days": period_days,
                "data_points": len(metrics),
                "follower_metrics": {
                    "start_followers": first_metric.follower_count,
                    "end_followers": latest_metric.follower_count,
                    "total_growth": follower_growth,
                    "growth_percentage": follower_growth_rate,
                    "daily_average_growth": daily_growth,
                    "volatility_score": volatility,
                    "consistency_score": consistency_score
                },
                "engagement_metrics": {
                    "current_rate": float(latest_metric.engagement_rate),
                    "average_rate": avg_engagement,
                    "trend": engagement_trend.direction.value,
                    "trend_strength": engagement_trend.strength,
                    "change_percentage": engagement_trend.change_percentage
                },
                "post_metrics": {
                    "start_posts": first_metric.post_count,
                    "end_posts": latest_metric.post_count,
                    "posts_added": latest_metric.post_count - first_metric.post_count,
                    "avg_posts_per_day": (latest_metric.post_count - first_metric.post_count) / days_span
                },
                "quality_indicators": {
                    "data_quality": "good" if len(metrics) > 10 else "limited",
                    "growth_quality": self._assess_growth_quality(follower_growth_rate, volatility, consistency_score),
                    "engagement_quality": self._assess_engagement_quality(avg_engagement, engagement_trend)
                }
            }
        
        return {
            "kol_id": kol_id,
            "kol_name": kol.name,
            "analysis_period_days": period_days,
            "platforms_analyzed": len(growth_analysis),
            "growth_analysis": growth_analysis,
            "generated_at": datetime.utcnow()
        }
    
    async def detect_anomalies(
        self,
        kol_id: int,
        platforms: Optional[List[str]] = None,
        lookback_days: int = 7
    ) -> List[AnomalyDetection]:
        """Detect anomalies in KOL performance metrics."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        if not platforms:
            platforms = [h.platform for h in kol.social_handles]
        
        anomalies = []
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        for platform in platforms:
            # Get recent metrics
            statement = select(KOLMetrics).where(
                and_(
                    KOLMetrics.kol_id == kol_id,
                    KOLMetrics.platform == platform,
                    KOLMetrics.scraped_at >= cutoff_date,
                    KOLMetrics.scraping_success == True
                )
            ).order_by(KOLMetrics.scraped_at.desc())
            
            metrics = self.db.exec(statement).all()
            
            if len(metrics) < 2:
                continue
            
            # Detect various types of anomalies
            platform_anomalies = []
            
            # 1. Follower count anomalies
            platform_anomalies.extend(self._detect_follower_anomalies(metrics, platform))
            
            # 2. Engagement rate anomalies
            platform_anomalies.extend(self._detect_engagement_anomalies(metrics, platform))
            
            # 3. Suspicious growth patterns
            platform_anomalies.extend(self._detect_suspicious_growth(metrics, platform))
            
            # 4. Inactive periods (check posts)
            platform_anomalies.extend(await self._detect_inactive_periods(kol_id, platform))
            
            anomalies.extend(platform_anomalies)
        
        # Sort by severity and confidence
        anomalies.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x.severity],
            x.confidence
        ), reverse=True)
        
        return anomalies
    
    async def get_comparative_analysis(
        self,
        kol_ids: List[int],
        platform: str,
        metric: str = "follower_count",
        days: int = 30
    ) -> Dict[str, Any]:
        """Compare multiple KOLs on a specific metric."""
        if len(kol_ids) > 20:  # Limit comparison size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 KOLs allowed for comparison"
            )
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        comparison_data = {}
        
        for kol_id in kol_ids:
            kol = self.db.get(KOL, kol_id)
            if not kol:
                comparison_data[kol_id] = {"error": "KOL not found"}
                continue
            
            # Get metrics
            statement = select(KOLMetrics).where(
                and_(
                    KOLMetrics.kol_id == kol_id,
                    KOLMetrics.platform == platform,
                    KOLMetrics.scraped_at >= start_date,
                    KOLMetrics.scraping_success == True
                )
            ).order_by(KOLMetrics.scraped_at.asc())
            
            metrics = self.db.exec(statement).all()
            
            if not metrics:
                comparison_data[kol_id] = {
                    "kol_name": kol.name,
                    "error": "No data available"
                }
                continue
            
            # Extract metric values
            if metric == "follower_count":
                values = [m.follower_count for m in metrics]
            elif metric == "engagement_rate":
                values = [float(m.engagement_rate) for m in metrics]
            elif metric == "post_count":
                values = [m.post_count for m in metrics]
            else:
                comparison_data[kol_id] = {
                    "kol_name": kol.name,
                    "error": f"Unsupported metric: {metric}"
                }
                continue
            
            # Calculate statistics
            current_value = values[-1]
            start_value = values[0]
            growth = current_value - start_value
            growth_rate = (growth / start_value * 100) if start_value > 0 else 0
            
            comparison_data[kol_id] = {
                "kol_name": kol.name,
                "current_value": current_value,
                "start_value": start_value,
                "growth": growth,
                "growth_rate": growth_rate,
                "data_points": len(values),
                "average_value": sum(values) / len(values),
                "max_value": max(values),
                "min_value": min(values),
                "volatility": self._calculate_volatility(values)
            }
        
        # Calculate rankings
        valid_data = {k: v for k, v in comparison_data.items() if "error" not in v}
        
        if valid_data:
            # Rank by current value
            current_ranking = sorted(valid_data.items(), key=lambda x: x[1]["current_value"], reverse=True)
            # Rank by growth rate
            growth_ranking = sorted(valid_data.items(), key=lambda x: x[1]["growth_rate"], reverse=True)
            
            rankings = {
                "by_current_value": [{"kol_id": k, "kol_name": v["kol_name"], "value": v["current_value"]} for k, v in current_ranking],
                "by_growth_rate": [{"kol_id": k, "kol_name": v["kol_name"], "growth_rate": v["growth_rate"]} for k, v in growth_ranking]
            }
        else:
            rankings = {"by_current_value": [], "by_growth_rate": []}
        
        return {
            "platform": platform,
            "metric": metric,
            "period_days": days,
            "kols_compared": len(kol_ids),
            "valid_data_count": len(valid_data),
            "comparison_data": comparison_data,
            "rankings": rankings,
            "generated_at": datetime.utcnow()
        }
    
    def _process_metrics_by_granularity(
        self, 
        metrics: List[KOLMetrics], 
        granularity: str
    ) -> List[Dict[str, Any]]:
        """Process metrics based on requested granularity."""
        if granularity == "raw":
            return [self._format_metric(m) for m in metrics]
        
        # Group metrics by time period
        grouped_metrics = {}
        
        for metric in metrics:
            if granularity == "daily":
                key = metric.scraped_at.date()
            elif granularity == "weekly":
                # Get Monday of the week
                key = metric.scraped_at.date() - timedelta(days=metric.scraped_at.weekday())
            elif granularity == "monthly":
                key = metric.scraped_at.date().replace(day=1)
            else:
                key = metric.scraped_at.date()  # Default to daily
            
            if key not in grouped_metrics:
                grouped_metrics[key] = []
            grouped_metrics[key].append(metric)
        
        # Aggregate metrics for each time period
        processed = []
        for period, period_metrics in sorted(grouped_metrics.items()):
            # Use the latest metric in the period as representative
            latest_metric = max(period_metrics, key=lambda m: m.scraped_at)
            
            # Calculate averages for some fields
            avg_engagement = sum(float(m.engagement_rate) for m in period_metrics) / len(period_metrics)
            
            processed.append({
                "period": period.isoformat(),
                "scraped_at": latest_metric.scraped_at.isoformat(),
                "follower_count": latest_metric.follower_count,
                "following_count": latest_metric.following_count,
                "post_count": latest_metric.post_count,
                "engagement_rate": avg_engagement,
                "avg_likes_per_post": float(latest_metric.avg_likes_per_post),
                "avg_comments_per_post": float(latest_metric.avg_comments_per_post),
                "follower_growth": latest_metric.follower_growth,
                "follower_growth_rate": float(latest_metric.follower_growth_rate),
                "data_points_in_period": len(period_metrics)
            })
        
        return processed
    
    def _format_metric(self, metric: KOLMetrics) -> Dict[str, Any]:
        """Format a single metric for output."""
        return {
            "scraped_at": metric.scraped_at.isoformat(),
            "follower_count": metric.follower_count,
            "following_count": metric.following_count,
            "post_count": metric.post_count,
            "engagement_rate": float(metric.engagement_rate),
            "avg_likes_per_post": float(metric.avg_likes_per_post),
            "avg_comments_per_post": float(metric.avg_comments_per_post),
            "avg_views_per_post": float(metric.avg_views_per_post) if metric.avg_views_per_post else None,
            "follower_growth": metric.follower_growth,
            "follower_growth_rate": float(metric.follower_growth_rate),
            "engagement_growth_rate": float(metric.engagement_growth_rate)
        }
    
    def _calculate_summary_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for metrics."""
        if not metrics:
            return {}
        
        follower_counts = [m["follower_count"] for m in metrics]
        engagement_rates = [m["engagement_rate"] for m in metrics]
        
        return {
            "follower_count": {
                "current": follower_counts[-1],
                "start": follower_counts[0],
                "max": max(follower_counts),
                "min": min(follower_counts),
                "average": sum(follower_counts) / len(follower_counts),
                "total_growth": follower_counts[-1] - follower_counts[0],
                "growth_percentage": ((follower_counts[-1] - follower_counts[0]) / follower_counts[0] * 100) if follower_counts[0] > 0 else 0
            },
            "engagement_rate": {
                "current": engagement_rates[-1],
                "average": sum(engagement_rates) / len(engagement_rates),
                "max": max(engagement_rates),
                "min": min(engagement_rates),
                "volatility": self._calculate_volatility(engagement_rates)
            },
            "data_quality": {
                "total_points": len(metrics),
                "quality_score": min(1.0, len(metrics) / 30),  # 30 points = perfect score
                "consistency": self._calculate_data_consistency(metrics)
            }
        }
    
    def _analyze_trends(self, metrics: List[Dict[str, Any]]) -> Dict[str, TrendAnalysis]:
        """Analyze trends in the metrics data."""
        if len(metrics) < self.min_data_points:
            return {}
        
        trends = {}
        
        # Analyze follower count trend
        follower_counts = [m["follower_count"] for m in metrics]
        trends["follower_count"] = self._calculate_trend(follower_counts, "follower_count")
        
        # Analyze engagement rate trend
        engagement_rates = [m["engagement_rate"] for m in metrics]
        trends["engagement_rate"] = self._calculate_trend(engagement_rates, "engagement_rate")
        
        return {k: {
            "direction": v.direction.value,
            "strength": v.strength,
            "confidence": v.confidence,
            "change_percentage": v.change_percentage,
            "period_days": v.period_days,
            "data_points": v.data_points
        } for k, v in trends.items()}
    
    def _calculate_trend(self, values: List[float], metric_name: str) -> TrendAnalysis:
        """Calculate trend analysis for a series of values."""
        if len(values) < 2:
            return TrendAnalysis(TrendDirection.STABLE, 0.0, 0.0, 0.0, 0, len(values))
        
        # Calculate linear regression slope
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Calculate correlation coefficient (R)
        y_variance = sum((values[i] - y_mean) ** 2 for i in range(n))
        if y_variance == 0:
            correlation = 0
        else:
            correlation = abs(numerator) / math.sqrt(denominator * y_variance)
        
        # Determine trend direction
        if abs(slope) < 0.01:  # Very small slope
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN
        
        # Calculate volatility
        volatility = self._calculate_volatility(values)
        if volatility > 0.3:  # High volatility
            direction = TrendDirection.VOLATILE
        
        # Calculate change percentage
        change_percentage = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        
        # Strength is based on absolute slope normalized by mean
        strength = min(1.0, abs(slope) / (y_mean if y_mean != 0 else 1))
        
        return TrendAnalysis(
            direction=direction,
            strength=strength,
            confidence=correlation,
            change_percentage=change_percentage,
            period_days=len(values),
            data_points=len(values)
        )
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation) for a series of values."""
        if len(values) < 2:
            return 0.0
        
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        
        return std_dev / mean_val  # Coefficient of variation
    
    def _calculate_growth_consistency(self, metrics: List[KOLMetrics]) -> float:
        """Calculate growth consistency score (0-1)."""
        if len(metrics) < 3:
            return 0.5  # Neutral score for insufficient data
        
        growth_rates = []
        for i in range(1, len(metrics)):
            prev_count = metrics[i-1].follower_count
            curr_count = metrics[i].follower_count
            if prev_count > 0:
                growth_rate = (curr_count - prev_count) / prev_count
                growth_rates.append(growth_rate)
        
        if not growth_rates:
            return 0.5
        
        # Calculate consistency as inverse of volatility
        volatility = self._calculate_volatility(growth_rates)
        consistency = max(0.0, 1.0 - volatility)
        
        return consistency
    
    def _calculate_engagement_trend(self, engagement_values: List[float]) -> TrendAnalysis:
        """Calculate engagement trend analysis."""
        return self._calculate_trend(engagement_values, "engagement_rate")
    
    def _calculate_data_consistency(self, metrics: List[Dict[str, Any]]) -> float:
        """Calculate data consistency score based on regular intervals."""
        if len(metrics) < 2:
            return 1.0
        
        # Calculate time intervals between data points
        intervals = []
        for i in range(1, len(metrics)):
            prev_time = datetime.fromisoformat(metrics[i-1]["scraped_at"].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(metrics[i]["scraped_at"].replace('Z', '+00:00'))
            interval_hours = (curr_time - prev_time).total_seconds() / 3600
            intervals.append(interval_hours)
        
        if not intervals:
            return 1.0
        
        # Calculate consistency as inverse of interval volatility
        volatility = self._calculate_volatility(intervals)
        consistency = max(0.0, 1.0 - min(1.0, volatility / 24))  # Normalize by 24 hours
        
        return consistency
    
    def _assess_growth_quality(self, growth_rate: float, volatility: float, consistency: float) -> str:
        """Assess the quality of growth based on multiple factors."""
        if growth_rate > 20 and volatility < 0.2 and consistency > 0.7:
            return "excellent"
        elif growth_rate > 10 and volatility < 0.3 and consistency > 0.5:
            return "good"
        elif growth_rate > 0 and volatility < 0.5:
            return "moderate"
        elif growth_rate < -10 or volatility > 0.7:
            return "poor"
        else:
            return "fair"
    
    def _assess_engagement_quality(self, avg_engagement: float, trend: TrendAnalysis) -> str:
        """Assess engagement quality based on rate and trend."""
        if avg_engagement > 5.0 and trend.direction == TrendDirection.UP:
            return "excellent"
        elif avg_engagement > 3.0 and trend.direction != TrendDirection.DOWN:
            return "good"
        elif avg_engagement > 1.0:
            return "moderate"
        elif avg_engagement > 0.5:
            return "fair"
        else:
            return "poor"
    
    def _detect_follower_anomalies(self, metrics: List[KOLMetrics], platform: str) -> List[AnomalyDetection]:
        """Detect follower count anomalies."""
        anomalies = []
        
        for i in range(1, len(metrics)):
            current = metrics[i]
            previous = metrics[i-1]
            
            if previous.follower_count == 0:
                continue
            
            change_percentage = ((current.follower_count - previous.follower_count) / previous.follower_count) * 100
            
            # Detect drops
            if change_percentage < -self.follower_drop_threshold:
                severity = "high" if change_percentage < -25 else "medium"
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.FOLLOWER_DROP,
                    severity=severity,
                    confidence=min(1.0, abs(change_percentage) / 50),
                    detected_at=current.scraped_at,
                    description=f"Follower count dropped by {abs(change_percentage):.1f}% on {platform}",
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_percentage=change_percentage
                ))
            
            # Detect spikes
            elif change_percentage > self.follower_spike_threshold:
                severity = "high" if change_percentage > 100 else "medium"
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.FOLLOWER_SPIKE,
                    severity=severity,
                    confidence=min(1.0, change_percentage / 100),
                    detected_at=current.scraped_at,
                    description=f"Follower count spiked by {change_percentage:.1f}% on {platform}",
                    current_value=float(current.follower_count),
                    expected_value=float(previous.follower_count),
                    deviation_percentage=change_percentage
                ))
        
        return anomalies
    
    def _detect_engagement_anomalies(self, metrics: List[KOLMetrics], platform: str) -> List[AnomalyDetection]:
        """Detect engagement rate anomalies."""
        anomalies = []
        
        for i in range(1, len(metrics)):
            current = metrics[i]
            previous = metrics[i-1]
            
            if float(previous.engagement_rate) == 0:
                continue
            
            change_percentage = ((float(current.engagement_rate) - float(previous.engagement_rate)) / float(previous.engagement_rate)) * 100
            
            # Detect drops
            if change_percentage < -self.engagement_drop_threshold:
                severity = "medium" if change_percentage < -40 else "low"
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.ENGAGEMENT_DROP,
                    severity=severity,
                    confidence=min(1.0, abs(change_percentage) / 50),
                    detected_at=current.scraped_at,
                    description=f"Engagement rate dropped by {abs(change_percentage):.1f}% on {platform}",
                    current_value=float(current.engagement_rate),
                    expected_value=float(previous.engagement_rate),
                    deviation_percentage=change_percentage
                ))
            
            # Detect spikes
            elif change_percentage > self.engagement_spike_threshold:
                severity = "medium"
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.ENGAGEMENT_SPIKE,
                    severity=severity,
                    confidence=min(1.0, change_percentage / 200),
                    detected_at=current.scraped_at,
                    description=f"Engagement rate spiked by {change_percentage:.1f}% on {platform}",
                    current_value=float(current.engagement_rate),
                    expected_value=float(previous.engagement_rate),
                    deviation_percentage=change_percentage
                ))
        
        return anomalies
    
    def _detect_suspicious_growth(self, metrics: List[KOLMetrics], platform: str) -> List[AnomalyDetection]:
        """Detect suspicious growth patterns that might indicate bot followers."""
        anomalies = []
        
        if len(metrics) < 3:
            return anomalies
        
        # Look for consistent high growth rates
        consecutive_high_growth = 0
        for i in range(1, len(metrics)):
            current = metrics[i]
            previous = metrics[i-1]
            
            if previous.follower_count == 0:
                continue
            
            growth_rate = ((current.follower_count - previous.follower_count) / previous.follower_count) * 100
            
            if growth_rate > 20:  # More than 20% growth
                consecutive_high_growth += 1
            else:
                consecutive_high_growth = 0
            
            # If we see 3+ consecutive periods of high growth
            if consecutive_high_growth >= 3:
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.SUSPICIOUS_GROWTH,
                    severity="high",
                    confidence=0.8,
                    detected_at=current.scraped_at,
                    description=f"Suspicious growth pattern detected on {platform} - {consecutive_high_growth} consecutive high-growth periods",
                    current_value=float(current.follower_count),
                    expected_value=None,
                    deviation_percentage=growth_rate
                ))
                consecutive_high_growth = 0  # Reset to avoid duplicate alerts
        
        return anomalies
    
    async def _detect_inactive_periods(self, kol_id: int, platform: str) -> List[AnomalyDetection]:
        """Detect periods of inactivity (no new posts)."""
        from app.models.post import Post
        
        anomalies = []
        
        # Get recent posts
        cutoff_date = datetime.utcnow() - timedelta(days=self.inactive_days_threshold)
        
        statement = select(Post).where(
            and_(
                Post.kol_id == kol_id,
                Post.platform == platform,
                Post.posted_at >= cutoff_date
            )
        )
        
        recent_posts = self.db.exec(statement).all()
        
        if not recent_posts:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.INACTIVE_PERIOD,
                severity="low",
                confidence=0.9,
                detected_at=datetime.utcnow(),
                description=f"No posts detected in the last {self.inactive_days_threshold} days on {platform}",
                current_value=0,
                expected_value=1,  # Expected at least 1 post
                deviation_percentage=None
            ))
        
        return anomalies
    
    async def archive_old_metrics(self, days_to_keep: int = 365) -> Dict[str, Any]:
        """Archive old metrics data to reduce database size."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count metrics to be archived
        count_statement = select(func.count(KOLMetrics.id)).where(
            KOLMetrics.scraped_at < cutoff_date
        )
        total_to_archive = self.db.exec(count_statement).first()
        
        if total_to_archive == 0:
            return {
                "success": True,
                "archived_count": 0,
                "message": "No old metrics to archive"
            }
        
        # In a real implementation, you would:
        # 1. Export data to cold storage (S3, etc.)
        # 2. Create summary records for archived data
        # 3. Delete the detailed records
        
        # For now, we'll just delete old records
        delete_statement = select(KOLMetrics).where(
            KOLMetrics.scraped_at < cutoff_date
        )
        old_metrics = self.db.exec(delete_statement).all()
        
        for metric in old_metrics:
            self.db.delete(metric)
        
        self.db.commit()
        
        logger.info(f"Archived {len(old_metrics)} old metrics records")
        
        return {
            "success": True,
            "archived_count": len(old_metrics),
            "cutoff_date": cutoff_date.isoformat(),
            "archived_at": datetime.utcnow()
        }