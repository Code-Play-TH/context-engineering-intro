"""Performance tracking service for manual refresh operations and KOL metrics management."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, or_
from fastapi import HTTPException, status
import logging
import uuid

from app.models.kol import KOL
from app.models.kol_metrics import KOLMetrics
from app.models.post import Post
from app.models.post_metrics import PostMetrics
from app.models.performance_alert import PerformanceAlert, AlertType, AlertSeverity
from app.models.social_handle import SocialHandle
from app.services.scraping_service import ScrapingService
from datetime import timedelta
from app.services.rate_limit_manager import RateLimitManager, RateLimitExceeded

logger = logging.getLogger(__name__)


class RefreshStatus:
    """Class to track refresh operation status."""
    def __init__(self, refresh_id: str, kol_id: int, platforms: List[str]):
        self.refresh_id = refresh_id
        self.kol_id = kol_id
        self.platforms = platforms
        self.status = "in_progress"
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.results = {}
        self.errors = []
        self.progress = 0
        self.total_platforms = len(platforms)


class PerformanceTrackingService:
    """Service for managing KOL performance tracking and manual refresh operations."""
    
    def __init__(self, db: Session, platform_configs: Dict[str, Dict[str, Any]]):
        self.db = db
        self.scraping_service = ScrapingService(db, platform_configs)
        self.rate_limit_manager = RateLimitManager(db)
        
        # In-memory storage for refresh status (in production, use Redis)
        self._refresh_operations: Dict[str, RefreshStatus] = {}
    
    async def manual_refresh_kol(
        self, 
        kol_id: int, 
        platforms: Optional[List[str]] = None,
        include_posts: bool = True,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Trigger manual refresh for a KOL's metrics."""
        # Validate KOL exists
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Get KOL's social handles
        social_handles = kol.social_handles
        if not social_handles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KOL has no social media handles configured"
            )
        
        # Filter platforms if specified
        available_platforms = [h.platform for h in social_handles]
        if platforms:
            platforms = [p for p in platforms if p in available_platforms]
            if not platforms:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="None of the specified platforms are available for this KOL"
                )
        else:
            platforms = available_platforms
        
        # Check for recent refresh (within 5 minutes) to avoid duplicate requests
        recent_refresh = await self._check_recent_refresh(kol_id)
        if recent_refresh:
            return {
                "refresh_id": recent_refresh["refresh_id"],
                "status": "cached",
                "message": "Recent refresh data available",
                "cached_result": recent_refresh,
                "cache_age_seconds": (datetime.utcnow() - recent_refresh["started_at"]).total_seconds()
            }
        
        # Create refresh operation
        refresh_id = str(uuid.uuid4())
        refresh_status = RefreshStatus(refresh_id, kol_id, platforms)
        self._refresh_operations[refresh_id] = refresh_status
        
        # Start async refresh
        asyncio.create_task(self._execute_refresh(refresh_status, include_posts, user_id))
        
        return {
            "refresh_id": refresh_id,
            "status": "started",
            "kol_id": kol_id,
            "platforms": platforms,
            "include_posts": include_posts,
            "estimated_duration_seconds": len(platforms) * 10,  # Rough estimate
            "started_at": refresh_status.started_at
        }
    
    async def get_refresh_status(self, refresh_id: str) -> Dict[str, Any]:
        """Get status of a refresh operation."""
        if refresh_id not in self._refresh_operations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh operation not found"
            )
        
        refresh_status = self._refresh_operations[refresh_id]
        
        return {
            "refresh_id": refresh_id,
            "kol_id": refresh_status.kol_id,
            "status": refresh_status.status,
            "progress": refresh_status.progress,
            "total_platforms": refresh_status.total_platforms,
            "platforms": refresh_status.platforms,
            "started_at": refresh_status.started_at,
            "completed_at": refresh_status.completed_at,
            "duration_seconds": (
                (refresh_status.completed_at or datetime.utcnow()) - refresh_status.started_at
            ).total_seconds(),
            "results": refresh_status.results,
            "errors": refresh_status.errors
        }
    
    async def get_latest_metrics(
        self, 
        kol_id: int, 
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get latest metrics for a KOL."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Build query
        statement = select(KOLMetrics).where(KOLMetrics.kol_id == kol_id)
        
        if platforms:
            statement = statement.where(KOLMetrics.platform.in_(platforms))
        
        # Get latest metrics for each platform
        latest_metrics = {}
        
        if platforms:
            platform_list = platforms
        else:
            # Get all platforms for this KOL
            platform_list = [h.platform for h in kol.social_handles]
        
        for platform in platform_list:
            platform_statement = statement.where(KOLMetrics.platform == platform).order_by(
                KOLMetrics.scraped_at.desc()
            )
            
            latest_metric = self.db.exec(platform_statement).first()
            if latest_metric:
                latest_metrics[platform] = {
                    "id": latest_metric.id,
                    "follower_count": latest_metric.follower_count,
                    "following_count": latest_metric.following_count,
                    "post_count": latest_metric.post_count,
                    "engagement_rate": float(latest_metric.engagement_rate),
                    "avg_likes_per_post": float(latest_metric.avg_likes_per_post),
                    "avg_comments_per_post": float(latest_metric.avg_comments_per_post),
                    "avg_views_per_post": float(latest_metric.avg_views_per_post) if latest_metric.avg_views_per_post else None,
                    "follower_growth": latest_metric.follower_growth,
                    "follower_growth_rate": float(latest_metric.follower_growth_rate),
                    "engagement_growth_rate": float(latest_metric.engagement_growth_rate),
                    "scraped_at": latest_metric.scraped_at,
                    "scraping_success": latest_metric.scraping_success,
                    "platform_specific_data": latest_metric.platform_specific_data,
                    "quality_score": latest_metric.get_quality_score()
                }
        
        return {
            "kol_id": kol_id,
            "kol_name": kol.name,
            "last_scraped_at": kol.last_scraped_at,
            "metrics": latest_metrics,
            "platforms_available": len(latest_metrics),
            "retrieved_at": datetime.utcnow()
        }
    
    async def get_historical_metrics(
        self, 
        kol_id: int, 
        platform: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get historical metrics for a KOL on a specific platform."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Get historical data
        since_date = datetime.utcnow() - timedelta(days=days)
        
        statement = select(KOLMetrics).where(
            and_(
                KOLMetrics.kol_id == kol_id,
                KOLMetrics.platform == platform,
                KOLMetrics.scraped_at >= since_date
            )
        ).order_by(KOLMetrics.scraped_at.asc())
        
        metrics = self.db.exec(statement).all()
        
        if not metrics:
            return {
                "kol_id": kol_id,
                "platform": platform,
                "period_days": days,
                "data_points": 0,
                "metrics": [],
                "trends": {}
            }
        
        # Format metrics data
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "scraped_at": metric.scraped_at,
                "follower_count": metric.follower_count,
                "engagement_rate": float(metric.engagement_rate),
                "follower_growth": metric.follower_growth,
                "follower_growth_rate": float(metric.follower_growth_rate),
                "post_count": metric.post_count
            })
        
        # Calculate trends
        trends = self._calculate_trends(metrics_data)
        
        return {
            "kol_id": kol_id,
            "kol_name": kol.name,
            "platform": platform,
            "period_days": days,
            "data_points": len(metrics_data),
            "metrics": metrics_data,
            "trends": trends,
            "retrieved_at": datetime.utcnow()
        }
    
    async def get_growth_analytics(
        self, 
        kol_id: int, 
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get growth analytics for a KOL."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Get platforms to analyze
        if not platforms:
            platforms = [h.platform for h in kol.social_handles]
        
        analytics = {}
        
        for platform in platforms:
            # Get recent metrics (last 30 days)
            recent_metrics = self.db.exec(
                select(KOLMetrics).where(
                    and_(
                        KOLMetrics.kol_id == kol_id,
                        KOLMetrics.platform == platform,
                        KOLMetrics.scraped_at >= datetime.utcnow() - timedelta(days=30)
                    )
                ).order_by(KOLMetrics.scraped_at.desc())
            ).all()
            
            if len(recent_metrics) < 2:
                analytics[platform] = {"error": "Insufficient data for growth analysis"}
                continue
            
            latest = recent_metrics[0]
            oldest = recent_metrics[-1]
            
            # Calculate growth metrics
            days_span = (latest.scraped_at - oldest.scraped_at).days
            if days_span == 0:
                days_span = 1
            
            follower_growth = latest.follower_count - oldest.follower_count
            daily_growth = follower_growth / days_span
            
            # Calculate average engagement rate
            avg_engagement = sum(float(m.engagement_rate) for m in recent_metrics) / len(recent_metrics)
            
            # Detect anomalies
            anomalies = []
            for metric in recent_metrics[:5]:  # Check last 5 data points
                anomaly_list = metric.detect_anomalies(None)  # Would need previous metric
                anomalies.extend(anomaly_list)
            
            analytics[platform] = {
                "current_followers": latest.follower_count,
                "follower_growth_30d": follower_growth,
                "daily_growth_rate": daily_growth,
                "growth_percentage": (follower_growth / oldest.follower_count * 100) if oldest.follower_count > 0 else 0,
                "current_engagement_rate": float(latest.engagement_rate),
                "avg_engagement_rate_30d": avg_engagement,
                "engagement_trend": "up" if latest.engagement_rate > avg_engagement else "down",
                "data_points": len(recent_metrics),
                "analysis_period_days": days_span,
                "anomalies": anomalies,
                "last_updated": latest.scraped_at
            }
        
        return {
            "kol_id": kol_id,
            "kol_name": kol.name,
            "analytics": analytics,
            "generated_at": datetime.utcnow()
        }
    
    async def detect_performance_issues(self, kol_id: int) -> List[Dict[str, Any]]:
        """Detect performance issues for a KOL."""
        issues = []
        
        # Get recent metrics
        recent_metrics = self.db.exec(
            select(KOLMetrics).where(
                and_(
                    KOLMetrics.kol_id == kol_id,
                    KOLMetrics.scraped_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(KOLMetrics.scraped_at.desc())
        ).all()
        
        if len(recent_metrics) < 2:
            return issues
        
        # Group by platform
        platform_metrics = {}
        for metric in recent_metrics:
            if metric.platform not in platform_metrics:
                platform_metrics[metric.platform] = []
            platform_metrics[metric.platform].append(metric)
        
        # Analyze each platform
        for platform, metrics in platform_metrics.items():
            if len(metrics) < 2:
                continue
            
            latest = metrics[0]
            previous = metrics[1]
            
            # Check for follower drops
            if latest.follower_count < previous.follower_count:
                drop_percentage = ((previous.follower_count - latest.follower_count) / previous.follower_count) * 100
                if drop_percentage > 5:  # More than 5% drop
                    issues.append({
                        "type": "follower_drop",
                        "platform": platform,
                        "severity": "high" if drop_percentage > 15 else "medium",
                        "message": f"Follower count dropped by {drop_percentage:.1f}% on {platform}",
                        "current_value": latest.follower_count,
                        "previous_value": previous.follower_count,
                        "detected_at": datetime.utcnow()
                    })
            
            # Check for engagement drops
            if latest.engagement_rate < previous.engagement_rate:
                eng_drop = ((float(previous.engagement_rate) - float(latest.engagement_rate)) / float(previous.engagement_rate)) * 100
                if eng_drop > 20:  # More than 20% drop
                    issues.append({
                        "type": "engagement_drop",
                        "platform": platform,
                        "severity": "medium",
                        "message": f"Engagement rate dropped by {eng_drop:.1f}% on {platform}",
                        "current_value": float(latest.engagement_rate),
                        "previous_value": float(previous.engagement_rate),
                        "detected_at": datetime.utcnow()
                    })
        
        return issues
    
    async def _execute_refresh(
        self, 
        refresh_status: RefreshStatus, 
        include_posts: bool,
        user_id: Optional[int]
    ) -> None:
        """Execute the actual refresh operation asynchronously."""
        try:
            # Update status
            refresh_status.status = "scraping_metrics"
            
            # Scrape metrics
            metrics_result = await self.scraping_service.scrape_kol_metrics(
                refresh_status.kol_id, 
                refresh_status.platforms,
                force_refresh=True
            )
            
            refresh_status.results["metrics"] = metrics_result
            refresh_status.progress = 50 if include_posts else 90
            
            # Scrape posts if requested
            if include_posts:
                refresh_status.status = "scraping_posts"
                
                posts_result = await self.scraping_service.scrape_kol_posts(
                    refresh_status.kol_id,
                    refresh_status.platforms,
                    limit=20
                )
                
                refresh_status.results["posts"] = posts_result
                refresh_status.progress = 90
            
            # Detect performance issues
            refresh_status.status = "analyzing"
            issues = await self.detect_performance_issues(refresh_status.kol_id)
            refresh_status.results["issues"] = issues
            
            # Create alerts for significant issues
            for issue in issues:
                if issue["severity"] in ["high", "critical"]:
                    await self._create_performance_alert(refresh_status.kol_id, issue, user_id)
            
            # Complete
            refresh_status.status = "completed"
            refresh_status.progress = 100
            refresh_status.completed_at = datetime.utcnow()
            
        except RateLimitExceeded as e:
            refresh_status.status = "rate_limited"
            refresh_status.errors.append(f"Rate limit exceeded: {e}")
            refresh_status.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error in refresh operation {refresh_status.refresh_id}: {e}")
            refresh_status.status = "failed"
            refresh_status.errors.append(str(e))
            refresh_status.completed_at = datetime.utcnow()
    
    async def _check_recent_refresh(self, kol_id: int) -> Optional[Dict[str, Any]]:
        """Check if there's a recent refresh for this KOL."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        
        for refresh_status in self._refresh_operations.values():
            if (refresh_status.kol_id == kol_id and 
                refresh_status.started_at > cutoff_time and
                refresh_status.status in ["completed", "in_progress"]):
                
                return {
                    "refresh_id": refresh_status.refresh_id,
                    "status": refresh_status.status,
                    "started_at": refresh_status.started_at,
                    "results": refresh_status.results
                }
        
        return None
    
    def _calculate_trends(self, metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend analysis from metrics data."""
        if len(metrics_data) < 2:
            return {}
        
        # Calculate overall trends
        first = metrics_data[0]
        last = metrics_data[-1]
        
        follower_trend = "up" if last["follower_count"] > first["follower_count"] else "down"
        engagement_trend = "up" if last["engagement_rate"] > first["engagement_rate"] else "down"
        
        # Calculate average growth rate
        total_growth = last["follower_count"] - first["follower_count"]
        days_span = (last["scraped_at"] - first["scraped_at"]).days or 1
        avg_daily_growth = total_growth / days_span
        
        return {
            "follower_trend": follower_trend,
            "engagement_trend": engagement_trend,
            "total_follower_growth": total_growth,
            "avg_daily_growth": avg_daily_growth,
            "growth_rate_percentage": (total_growth / first["follower_count"] * 100) if first["follower_count"] > 0 else 0,
            "data_quality": "good" if len(metrics_data) > 10 else "limited"
        }
    
    async def _create_performance_alert(
        self, 
        kol_id: int, 
        issue: Dict[str, Any], 
        user_id: Optional[int]
    ) -> None:
        """Create a performance alert for an issue."""
        try:
            alert_type_map = {
                "follower_drop": AlertType.FOLLOWER_DROP,
                "engagement_drop": AlertType.ENGAGEMENT_DROP,
                "follower_spike": AlertType.FOLLOWER_SPIKE
            }
            
            severity_map = {
                "low": AlertSeverity.INFO,
                "medium": AlertSeverity.WARNING,
                "high": AlertSeverity.CRITICAL
            }
            
            alert = PerformanceAlert(
                kol_id=kol_id,
                alert_type=alert_type_map.get(issue["type"], AlertType.ENGAGEMENT_DROP),
                severity=severity_map.get(issue["severity"], AlertSeverity.WARNING),
                title=f"Performance Issue Detected - {issue['platform'].title()}",
                message=issue["message"],
                actual_value=issue.get("current_value"),
                previous_value=issue.get("previous_value"),
                context_data={
                    "platform": issue["platform"],
                    "detected_by": "manual_refresh",
                    "user_id": user_id
                }
            )
            
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating performance alert: {e}")
    
    async def cleanup_old_refresh_operations(self, hours: int = 24) -> int:
        """Clean up old refresh operations from memory."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        to_remove = []
        for refresh_id, refresh_status in self._refresh_operations.items():
            if refresh_status.started_at < cutoff_time:
                to_remove.append(refresh_id)
        
        for refresh_id in to_remove:
            del self._refresh_operations[refresh_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old refresh operations")
        return len(to_remove)