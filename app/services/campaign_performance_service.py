"""Campaign performance analysis service for KPI tracking and comparison."""
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, or_, func
from fastapi import HTTPException, status
import logging
from dataclasses import dataclass
from enum import Enum

from app.models.campaign import Campaign
from app.models.brief import Brief
from app.models.kol import KOL
from app.models.kol_metrics import KOLMetrics
from app.models.post import Post
from app.models.post_metrics import PostMetrics
from app.models.performance_alert import PerformanceAlert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class KPIStatus(str, Enum):
    """KPI achievement status."""
    EXCEEDED = "exceeded"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    NOT_STARTED = "not_started"


class ProjectionConfidence(str, Enum):
    """Confidence level for projections."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class KPITarget:
    """KPI target definition."""
    metric_name: str
    target_value: float
    current_value: float
    achievement_percentage: float
    status: KPIStatus
    projected_final_value: Optional[float] = None
    projection_confidence: Optional[ProjectionConfidence] = None


@dataclass
class CampaignProjection:
    """Campaign performance projection."""
    projected_reach: int
    projected_engagement: float
    projected_conversions: int
    confidence_level: ProjectionConfidence
    projection_date: datetime
    based_on_days: int


class CampaignPerformanceService:
    """Service for campaign performance analysis and KPI tracking."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Default KPI thresholds
        self.kpi_thresholds = {
            "on_track_percentage": 80.0,    # 80%+ of target = on track
            "at_risk_percentage": 60.0,     # 60-80% of target = at risk
            "behind_percentage": 60.0,      # <60% of target = behind
            "exceeded_percentage": 100.0,   # >100% of target = exceeded
        }
        
        # Projection confidence thresholds
        self.projection_thresholds = {
            "high_confidence_days": 14,     # 14+ days of data = high confidence
            "medium_confidence_days": 7,    # 7-14 days of data = medium confidence
            "low_confidence_days": 3,       # 3-7 days of data = low confidence
        }
    
    async def get_campaign_performance_overview(
        self,
        campaign_id: int,
        include_projections: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive campaign performance overview."""
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )
        
        # Get campaign KOLs
        briefs = self.db.exec(
            select(Brief).where(Brief.campaign_id == campaign_id)
        ).all()
        
        kol_ids = [brief.kol_id for brief in briefs]
        
        if not kol_ids:
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "kols_count": 0,
                "performance_summary": {},
                "kpi_analysis": {},
                "projections": {} if include_projections else None,
                "generated_at": datetime.utcnow()
            }
        
        # Calculate performance metrics
        performance_summary = await self._calculate_performance_summary(campaign, kol_ids)
        
        # Analyze KPIs
        kpi_analysis = await self._analyze_campaign_kpis(campaign, performance_summary)
        
        # Generate projections if requested
        projections = None
        if include_projections:
            projections = await self._generate_campaign_projections(campaign, kol_ids, performance_summary)
        
        # Get recent alerts
        recent_alerts = await self._get_recent_campaign_alerts(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
            "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
            "kols_count": len(kol_ids),
            "performance_summary": performance_summary,
            "kpi_analysis": kpi_analysis,
            "projections": projections,
            "recent_alerts": recent_alerts,
            "generated_at": datetime.utcnow()
        }
    
    async def compare_campaign_kpis(
        self,
        campaign_id: int,
        target_kpis: Dict[str, float]
    ) -> Dict[str, Any]:
        """Compare actual campaign performance against target KPIs."""
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )
        
        # Get campaign KOLs
        briefs = self.db.exec(
            select(Brief).where(Brief.campaign_id == campaign_id)
        ).all()
        
        kol_ids = [brief.kol_id for brief in briefs]
        
        # Calculate current performance
        performance_summary = await self._calculate_performance_summary(campaign, kol_ids)
        
        # Compare against targets
        kpi_comparisons = {}
        
        for kpi_name, target_value in target_kpis.items():
            current_value = performance_summary.get(kpi_name, 0)
            
            if target_value > 0:
                achievement_percentage = (current_value / target_value) * 100
            else:
                achievement_percentage = 100.0 if current_value > 0 else 0.0
            
            # Determine status
            status = self._determine_kpi_status(achievement_percentage, campaign)
            
            kpi_comparisons[kpi_name] = KPITarget(
                metric_name=kpi_name,
                target_value=target_value,
                current_value=current_value,
                achievement_percentage=achievement_percentage,
                status=status
            )
        
        # Calculate overall campaign health
        overall_health = self._calculate_campaign_health(kpi_comparisons)
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "kpi_comparisons": {
                name: {
                    "metric_name": kpi.metric_name,
                    "target_value": kpi.target_value,
                    "current_value": kpi.current_value,
                    "achievement_percentage": kpi.achievement_percentage,
                    "status": kpi.status.value
                }
                for name, kpi in kpi_comparisons.items()
            },
            "overall_health": overall_health,
            "recommendations": self._generate_kpi_recommendations(kpi_comparisons),
            "analyzed_at": datetime.utcnow()
        }
    
    async def get_campaign_completion_tracking(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """Track campaign completion progress."""
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )
        
        # Get campaign briefs and their status
        briefs = self.db.exec(
            select(Brief).where(Brief.campaign_id == campaign_id)
        ).all()
        
        # Calculate completion metrics
        total_briefs = len(briefs)
        completed_briefs = len([b for b in briefs if b.status == "completed"])
        in_progress_briefs = len([b for b in briefs if b.status == "in_progress"])
        pending_briefs = len([b for b in briefs if b.status == "pending"])
        
        completion_percentage = (completed_briefs / total_briefs * 100) if total_briefs > 0 else 0
        
        # Calculate timeline progress
        timeline_progress = self._calculate_timeline_progress(campaign)
        
        # Get deliverables status
        deliverables_status = await self._get_deliverables_status(campaign_id)
        
        # Estimate completion date
        estimated_completion = self._estimate_completion_date(campaign, completion_percentage, timeline_progress)
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "completion_metrics": {
                "total_briefs": total_briefs,
                "completed_briefs": completed_briefs,
                "in_progress_briefs": in_progress_briefs,
                "pending_briefs": pending_briefs,
                "completion_percentage": completion_percentage
            },
            "timeline_progress": timeline_progress,
            "deliverables_status": deliverables_status,
            "estimated_completion": estimated_completion,
            "status_summary": self._generate_completion_status_summary(
                completion_percentage, timeline_progress, campaign
            ),
            "tracked_at": datetime.utcnow()
        }
    
    async def get_kol_performance_within_campaign(
        self,
        campaign_id: int,
        sort_by: str = "engagement_rate",
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get KOL performance ranking within a campaign."""
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )
        
        # Get campaign KOLs
        briefs = self.db.exec(
            select(Brief).where(Brief.campaign_id == campaign_id)
        ).all()
        
        kol_performances = []
        
        for brief in briefs:
            kol = self.db.get(KOL, brief.kol_id)
            if not kol:
                continue
            
            # Get latest metrics for each platform
            kol_metrics = {}
            total_reach = 0
            avg_engagement = 0
            platform_count = 0
            
            for handle in kol.social_handles:
                latest_metric = self.db.exec(
                    select(KOLMetrics).where(
                        and_(
                            KOLMetrics.kol_id == kol.id,
                            KOLMetrics.platform == handle.platform,
                            KOLMetrics.scraping_success == True
                        )
                    ).order_by(KOLMetrics.scraped_at.desc()).limit(1)
                ).first()
                
                if latest_metric:
                    kol_metrics[handle.platform] = {
                        "follower_count": latest_metric.follower_count,
                        "engagement_rate": float(latest_metric.engagement_rate),
                        "post_count": latest_metric.post_count
                    }
                    total_reach += latest_metric.follower_count
                    avg_engagement += float(latest_metric.engagement_rate)
                    platform_count += 1
            
            if platform_count > 0:
                avg_engagement = avg_engagement / platform_count
            
            # Get campaign-specific posts
            campaign_posts = await self._get_campaign_posts(brief.kol_id, campaign_id)
            
            kol_performances.append({
                "kol_id": kol.id,
                "kol_name": kol.name,
                "brief_status": brief.status,
                "total_reach": total_reach,
                "avg_engagement_rate": avg_engagement,
                "platforms": list(kol_metrics.keys()),
                "platform_metrics": kol_metrics,
                "campaign_posts": len(campaign_posts),
                "campaign_performance": self._calculate_campaign_specific_performance(campaign_posts)
            })
        
        # Sort KOLs by specified metric
        if sort_by == "engagement_rate":
            kol_performances.sort(key=lambda x: x["avg_engagement_rate"], reverse=True)
        elif sort_by == "reach":
            kol_performances.sort(key=lambda x: x["total_reach"], reverse=True)
        elif sort_by == "posts":
            kol_performances.sort(key=lambda x: x["campaign_posts"], reverse=True)
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "kol_count": len(kol_performances),
            "sort_by": sort_by,
            "kol_performances": kol_performances[:limit],
            "top_performers": {
                "by_engagement": sorted(kol_performances, key=lambda x: x["avg_engagement_rate"], reverse=True)[:3],
                "by_reach": sorted(kol_performances, key=lambda x: x["total_reach"], reverse=True)[:3],
                "by_posts": sorted(kol_performances, key=lambda x: x["campaign_posts"], reverse=True)[:3]
            },
            "analyzed_at": datetime.utcnow()
        }
    
    async def _calculate_performance_summary(
        self,
        campaign: Campaign,
        kol_ids: List[int]
    ) -> Dict[str, Any]:
        """Calculate overall campaign performance summary."""
        if not kol_ids:
            return {}
        
        # Get latest metrics for all KOLs
        total_reach = 0
        total_engagement = 0
        total_posts = 0
        active_kols = 0
        
        for kol_id in kol_ids:
            kol = self.db.get(KOL, kol_id)
            if not kol:
                continue
            
            kol_reach = 0
            kol_engagement = 0
            kol_platforms = 0
            
            for handle in kol.social_handles:
                latest_metric = self.db.exec(
                    select(KOLMetrics).where(
                        and_(
                            KOLMetrics.kol_id == kol_id,
                            KOLMetrics.platform == handle.platform,
                            KOLMetrics.scraping_success == True
                        )
                    ).order_by(KOLMetrics.scraped_at.desc()).limit(1)
                ).first()
                
                if latest_metric:
                    kol_reach += latest_metric.follower_count
                    kol_engagement += float(latest_metric.engagement_rate)
                    kol_platforms += 1
            
            if kol_platforms > 0:
                total_reach += kol_reach
                total_engagement += kol_engagement / kol_platforms
                active_kols += 1
            
            # Count campaign posts
            campaign_posts = await self._get_campaign_posts(kol_id, campaign.id)
            total_posts += len(campaign_posts)
        
        avg_engagement = total_engagement / active_kols if active_kols > 0 else 0
        
        return {
            "total_reach": total_reach,
            "average_engagement_rate": avg_engagement,
            "total_posts": total_posts,
            "active_kols": active_kols,
            "total_kols": len(kol_ids),
            "activation_rate": (active_kols / len(kol_ids) * 100) if kol_ids else 0
        }
    
    async def _analyze_campaign_kpis(
        self,
        campaign: Campaign,
        performance_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze campaign KPIs against targets."""
        # This would typically use campaign.target_kpis if stored in the model
        # For now, we'll use default targets based on campaign type
        
        default_targets = {
            "total_reach": 1000000,  # 1M reach
            "average_engagement_rate": 3.0,  # 3% engagement
            "total_posts": 50,  # 50 posts
            "activation_rate": 90.0  # 90% KOL activation
        }
        
        kpi_analysis = {}
        
        for kpi_name, target_value in default_targets.items():
            current_value = performance_summary.get(kpi_name, 0)
            
            if target_value > 0:
                achievement_percentage = (current_value / target_value) * 100
            else:
                achievement_percentage = 100.0 if current_value > 0 else 0.0
            
            status = self._determine_kpi_status(achievement_percentage, campaign)
            
            kpi_analysis[kpi_name] = {
                "target": target_value,
                "current": current_value,
                "achievement_percentage": achievement_percentage,
                "status": status.value
            }
        
        return kpi_analysis
    
    async def _generate_campaign_projections(
        self,
        campaign: Campaign,
        kol_ids: List[int],
        performance_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate campaign performance projections."""
        if not campaign.start_date or not campaign.end_date:
            return {"error": "Campaign dates not set"}
        
        # Calculate campaign progress
        total_days = (campaign.end_date - campaign.start_date).days
        elapsed_days = (date.today() - campaign.start_date).days
        remaining_days = (campaign.end_date - date.today()).days
        
        if elapsed_days <= 0:
            return {"error": "Campaign not started"}
        
        if remaining_days <= 0:
            return {"error": "Campaign completed"}
        
        # Calculate growth rates
        current_reach = performance_summary.get("total_reach", 0)
        current_posts = performance_summary.get("total_posts", 0)
        
        # Simple linear projection (could be enhanced with trend analysis)
        daily_reach_growth = current_reach / elapsed_days if elapsed_days > 0 else 0
        daily_post_growth = current_posts / elapsed_days if elapsed_days > 0 else 0
        
        projected_final_reach = current_reach + (daily_reach_growth * remaining_days)
        projected_final_posts = current_posts + (daily_post_growth * remaining_days)
        
        # Determine confidence level
        confidence = self._determine_projection_confidence(elapsed_days)
        
        return {
            "campaign_progress": {
                "total_days": total_days,
                "elapsed_days": elapsed_days,
                "remaining_days": remaining_days,
                "progress_percentage": (elapsed_days / total_days * 100) if total_days > 0 else 0
            },
            "projections": {
                "projected_final_reach": int(projected_final_reach),
                "projected_final_posts": int(projected_final_posts),
                "projected_final_engagement": performance_summary.get("average_engagement_rate", 0),
                "confidence_level": confidence.value
            },
            "growth_rates": {
                "daily_reach_growth": daily_reach_growth,
                "daily_post_growth": daily_post_growth
            }
        }
    
    async def _get_recent_campaign_alerts(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Get recent performance alerts for campaign KOLs."""
        # Get campaign KOLs
        briefs = self.db.exec(
            select(Brief).where(Brief.campaign_id == campaign_id)
        ).all()
        
        kol_ids = [brief.kol_id for brief in briefs]
        
        if not kol_ids:
            return []
        
        # Get recent alerts (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        
        alerts = self.db.exec(
            select(PerformanceAlert).where(
                and_(
                    PerformanceAlert.kol_id.in_(kol_ids),
                    PerformanceAlert.created_at >= recent_cutoff
                )
            ).order_by(PerformanceAlert.created_at.desc()).limit(10)
        ).all()
        
        return [
            {
                "alert_id": alert.id,
                "kol_id": alert.kol_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "is_acknowledged": alert.is_acknowledged
            }
            for alert in alerts
        ]
    
    def _determine_kpi_status(self, achievement_percentage: float, campaign: Campaign) -> KPIStatus:
        """Determine KPI status based on achievement percentage and campaign timeline."""
        # Adjust thresholds based on campaign progress
        timeline_factor = 1.0
        if campaign.start_date and campaign.end_date:
            total_days = (campaign.end_date - campaign.start_date).days
            elapsed_days = (date.today() - campaign.start_date).days
            if total_days > 0 and elapsed_days > 0:
                timeline_factor = elapsed_days / total_days
        
        # Adjust expected achievement based on timeline
        expected_achievement = timeline_factor * 100
        
        if achievement_percentage >= self.kpi_thresholds["exceeded_percentage"]:
            return KPIStatus.EXCEEDED
        elif achievement_percentage >= expected_achievement * 0.8:
            return KPIStatus.ON_TRACK
        elif achievement_percentage >= expected_achievement * 0.6:
            return KPIStatus.AT_RISK
        else:
            return KPIStatus.BEHIND
    
    def _calculate_campaign_health(self, kpi_comparisons: Dict[str, KPITarget]) -> Dict[str, Any]:
        """Calculate overall campaign health score."""
        if not kpi_comparisons:
            return {"score": 0, "status": "unknown"}
        
        status_weights = {
            KPIStatus.EXCEEDED: 1.2,
            KPIStatus.ON_TRACK: 1.0,
            KPIStatus.AT_RISK: 0.6,
            KPIStatus.BEHIND: 0.3,
            KPIStatus.NOT_STARTED: 0.0
        }
        
        total_weight = 0
        weighted_score = 0
        
        for kpi in kpi_comparisons.values():
            weight = status_weights[kpi.status]
            total_weight += 1
            weighted_score += weight
        
        health_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 60:
            health_status = "fair"
        elif health_score >= 40:
            health_status = "poor"
        else:
            health_status = "critical"
        
        return {
            "score": health_score,
            "status": health_status,
            "kpis_on_track": len([k for k in kpi_comparisons.values() if k.status == KPIStatus.ON_TRACK]),
            "kpis_at_risk": len([k for k in kpi_comparisons.values() if k.status == KPIStatus.AT_RISK]),
            "kpis_behind": len([k for k in kpi_comparisons.values() if k.status == KPIStatus.BEHIND])
        }
    
    def _generate_kpi_recommendations(self, kpi_comparisons: Dict[str, KPITarget]) -> List[str]:
        """Generate recommendations based on KPI performance."""
        recommendations = []
        
        for name, kpi in kpi_comparisons.items():
            if kpi.status == KPIStatus.BEHIND:
                if "reach" in name.lower():
                    recommendations.append(f"Consider adding more KOLs or boosting content to improve {name}")
                elif "engagement" in name.lower():
                    recommendations.append(f"Review content strategy to improve {name}")
                elif "posts" in name.lower():
                    recommendations.append(f"Increase posting frequency to meet {name} target")
                else:
                    recommendations.append(f"Focus on improving {name} performance")
            
            elif kpi.status == KPIStatus.AT_RISK:
                recommendations.append(f"Monitor {name} closely and consider optimization strategies")
        
        if not recommendations:
            recommendations.append("Campaign is performing well. Continue current strategy.")
        
        return recommendations
    
    def _calculate_timeline_progress(self, campaign: Campaign) -> Dict[str, Any]:
        """Calculate campaign timeline progress."""
        if not campaign.start_date or not campaign.end_date:
            return {"error": "Campaign dates not set"}
        
        total_days = (campaign.end_date - campaign.start_date).days
        elapsed_days = (date.today() - campaign.start_date).days
        remaining_days = (campaign.end_date - date.today()).days
        
        progress_percentage = (elapsed_days / total_days * 100) if total_days > 0 else 0
        progress_percentage = max(0, min(100, progress_percentage))  # Clamp to 0-100
        
        return {
            "total_days": total_days,
            "elapsed_days": max(0, elapsed_days),
            "remaining_days": max(0, remaining_days),
            "progress_percentage": progress_percentage,
            "is_overdue": remaining_days < 0,
            "days_overdue": abs(remaining_days) if remaining_days < 0 else 0
        }
    
    async def _get_deliverables_status(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign deliverables status."""
        # This would track specific deliverables like posts, videos, etc.
        # For now, return a placeholder structure
        
        briefs = self.db.exec(
            select(Brief).where(Brief.campaign_id == campaign_id)
        ).all()
        
        total_deliverables = len(briefs)  # Each brief represents a deliverable
        completed_deliverables = len([b for b in briefs if b.status == "completed"])
        
        return {
            "total_deliverables": total_deliverables,
            "completed_deliverables": completed_deliverables,
            "completion_rate": (completed_deliverables / total_deliverables * 100) if total_deliverables > 0 else 0,
            "pending_deliverables": total_deliverables - completed_deliverables
        }
    
    def _estimate_completion_date(
        self,
        campaign: Campaign,
        completion_percentage: float,
        timeline_progress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate campaign completion date."""
        if completion_percentage >= 100:
            return {
                "status": "completed",
                "estimated_date": None,
                "confidence": "high"
            }
        
        if timeline_progress.get("remaining_days", 0) <= 0:
            return {
                "status": "overdue",
                "estimated_date": campaign.end_date.isoformat() if campaign.end_date else None,
                "confidence": "high"
            }
        
        # Simple linear projection
        elapsed_days = timeline_progress.get("elapsed_days", 0)
        if elapsed_days > 0 and completion_percentage > 0:
            days_per_percent = elapsed_days / completion_percentage
            remaining_percent = 100 - completion_percentage
            estimated_additional_days = days_per_percent * remaining_percent
            
            estimated_date = date.today() + timedelta(days=int(estimated_additional_days))
            
            # Determine confidence based on current progress
            if completion_percentage > 50:
                confidence = "high"
            elif completion_percentage > 25:
                confidence = "medium"
            else:
                confidence = "low"
            
            return {
                "status": "in_progress",
                "estimated_date": estimated_date.isoformat(),
                "estimated_additional_days": int(estimated_additional_days),
                "confidence": confidence
            }
        
        return {
            "status": "insufficient_data",
            "estimated_date": None,
            "confidence": "low"
        }
    
    def _generate_completion_status_summary(
        self,
        completion_percentage: float,
        timeline_progress: Dict[str, Any],
        campaign: Campaign
    ) -> Dict[str, Any]:
        """Generate campaign completion status summary."""
        timeline_percentage = timeline_progress.get("progress_percentage", 0)
        
        if completion_percentage >= 100:
            status = "completed"
            message = "Campaign completed successfully"
        elif timeline_progress.get("is_overdue", False):
            status = "overdue"
            message = f"Campaign is {timeline_progress.get('days_overdue', 0)} days overdue"
        elif completion_percentage >= timeline_percentage * 0.9:
            status = "on_track"
            message = "Campaign is on track for completion"
        elif completion_percentage >= timeline_percentage * 0.7:
            status = "at_risk"
            message = "Campaign completion is at risk"
        else:
            status = "behind_schedule"
            message = "Campaign is behind schedule"
        
        return {
            "status": status,
            "message": message,
            "completion_vs_timeline": completion_percentage - timeline_percentage
        }
    
    async def _get_campaign_posts(self, kol_id: int, campaign_id: int) -> List[Post]:
        """Get posts related to a specific campaign."""
        # This would typically use campaign hashtags or keywords to match posts
        # For now, get recent posts from the KOL during campaign period
        
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign or not campaign.start_date:
            return []
        
        start_date = datetime.combine(campaign.start_date, datetime.min.time())
        end_date = datetime.combine(campaign.end_date, datetime.max.time()) if campaign.end_date else datetime.utcnow()
        
        posts = self.db.exec(
            select(Post).where(
                and_(
                    Post.kol_id == kol_id,
                    Post.posted_at >= start_date,
                    Post.posted_at <= end_date
                )
            )
        ).all()
        
        return list(posts)
    
    def _calculate_campaign_specific_performance(self, posts: List[Post]) -> Dict[str, Any]:
        """Calculate performance metrics for campaign-specific posts."""
        if not posts:
            return {
                "total_posts": 0,
                "avg_likes": 0,
                "avg_comments": 0,
                "avg_views": 0,
                "total_engagement": 0
            }
        
        total_likes = sum(post.likes_count or 0 for post in posts)
        total_comments = sum(post.comments_count or 0 for post in posts)
        total_views = sum(post.views_count or 0 for post in posts if post.views_count)
        
        return {
            "total_posts": len(posts),
            "avg_likes": total_likes / len(posts),
            "avg_comments": total_comments / len(posts),
            "avg_views": total_views / len(posts) if posts else 0,
            "total_engagement": total_likes + total_comments,
            "engagement_per_post": (total_likes + total_comments) / len(posts)
        }
    
    def _determine_projection_confidence(self, elapsed_days: int) -> ProjectionConfidence:
        """Determine confidence level for projections based on data availability."""
        if elapsed_days >= self.projection_thresholds["high_confidence_days"]:
            return ProjectionConfidence.HIGH
        elif elapsed_days >= self.projection_thresholds["medium_confidence_days"]:
            return ProjectionConfidence.MEDIUM
        else:
            return ProjectionConfidence.LOW