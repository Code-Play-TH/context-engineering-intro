"""
Dashboard service for aggregating and presenting system metrics.

This module provides dashboard data aggregation, KPI calculations,
and real-time analytics for campaigns, KOLs, and system health.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.campaign import Campaign, CampaignStatus
from app.models.kol import KOL
from app.models.collaboration import Collaboration, CollaborationStatus
from app.models.campaign_content import CampaignContent, ContentStatus
from app.models.user import User
from app.utils.datetime_utils import get_current_utc
import logging

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service for dashboard data aggregation and KPIs.

    Provides:
    - System overview metrics
    - Campaign performance dashboards
    - KOL performance dashboards
    - Real-time alerts and notifications
    """

    def __init__(self, db: Session):
        """
        Initialize dashboard service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def get_system_overview(self) -> Dict[str, Any]:
        """
        Get system-wide overview metrics.

        Returns:
            Dict[str, Any]: System overview with key metrics.
        """
        # Campaign metrics
        total_campaigns = self.db.query(func.count(Campaign.id)).scalar() or 0
        active_campaigns = self.db.query(func.count(Campaign.id)).filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).scalar() or 0

        # KOL metrics
        total_kols = self.db.query(func.count(KOL.id)).scalar() or 0
        verified_kols = self.db.query(func.count(KOL.id)).filter(
            KOL.is_verified == True
        ).scalar() or 0

        # Collaboration metrics
        total_collaborations = self.db.query(func.count(Collaboration.id)).scalar() or 0
        active_collaborations = self.db.query(func.count(Collaboration.id)).filter(
            Collaboration.status == CollaborationStatus.IN_PROGRESS
        ).scalar() or 0

        # Content metrics
        total_content = self.db.query(func.count(CampaignContent.id)).scalar() or 0
        published_content = self.db.query(func.count(CampaignContent.id)).filter(
            CampaignContent.status == ContentStatus.PUBLISHED
        ).scalar() or 0

        # User metrics
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        active_users = self.db.query(func.count(User.id)).filter(
            User.is_active == True
        ).scalar() or 0

        return {
            "generated_at": get_current_utc().isoformat(),
            "campaigns": {
                "total": total_campaigns,
                "active": active_campaigns,
                "completion_rate": round((total_campaigns - active_campaigns) / total_campaigns * 100, 2) if total_campaigns > 0 else 0
            },
            "kols": {
                "total": total_kols,
                "verified": verified_kols,
                "verification_rate": round(verified_kols / total_kols * 100, 2) if total_kols > 0 else 0
            },
            "collaborations": {
                "total": total_collaborations,
                "active": active_collaborations,
                "engagement_rate": round(active_collaborations / total_collaborations * 100, 2) if total_collaborations > 0 else 0
            },
            "content": {
                "total": total_content,
                "published": published_content,
                "publish_rate": round(published_content / total_content * 100, 2) if total_content > 0 else 0
            },
            "users": {
                "total": total_users,
                "active": active_users
            }
        }

    def get_campaign_dashboard(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get comprehensive campaign dashboard.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            Dict[str, Any]: Campaign dashboard data.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            return {"error": "Campaign not found"}

        # Get collaborations
        collaborations = self.db.query(Collaboration).filter(
            Collaboration.campaign_id == campaign_id
        ).all()

        # Get content
        content_list = self.db.query(CampaignContent).filter(
            CampaignContent.campaign_id == campaign_id
        ).all()

        # Calculate metrics
        total_budget = campaign.budget
        allocated_budget = sum(c.compensation for c in collaborations)
        remaining_budget = total_budget - allocated_budget

        total_reach = sum(c.reach or 0 for c in content_list if c.status == ContentStatus.PUBLISHED)
        total_engagement = sum(
            c.metrics.get("engagement_count", 0) if c.metrics else 0
            for c in content_list if c.status == ContentStatus.PUBLISHED
        )

        avg_engagement_rate = (
            sum(c.engagement_rate or 0 for c in content_list if c.status == ContentStatus.PUBLISHED) /
            len([c for c in content_list if c.status == ContentStatus.PUBLISHED])
        ) if any(c.status == ContentStatus.PUBLISHED for c in content_list) else 0

        # Timeline progress
        now = get_current_utc()
        total_days = (campaign.end_date - campaign.start_date).days
        elapsed_days = max(0, (now - campaign.start_date).days)
        progress = min(100, (elapsed_days / total_days * 100)) if total_days > 0 else 0

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "timeline": {
                "start_date": campaign.start_date.isoformat(),
                "end_date": campaign.end_date.isoformat(),
                "progress_percentage": round(progress, 2),
                "days_remaining": max(0, (campaign.end_date - now).days)
            },
            "budget": {
                "total": total_budget,
                "allocated": allocated_budget,
                "remaining": remaining_budget,
                "utilization_percentage": round(allocated_budget / total_budget * 100, 2) if total_budget > 0 else 0
            },
            "collaborations": {
                "total": len(collaborations),
                "by_status": {
                    "pending": len([c for c in collaborations if c.status == CollaborationStatus.PENDING]),
                    "accepted": len([c for c in collaborations if c.status == CollaborationStatus.ACCEPTED]),
                    "in_progress": len([c for c in collaborations if c.status == CollaborationStatus.IN_PROGRESS]),
                    "completed": len([c for c in collaborations if c.status == CollaborationStatus.COMPLETED])
                }
            },
            "content": {
                "total": len(content_list),
                "by_status": {
                    "pending": len([c for c in content_list if c.status == ContentStatus.PENDING_REVIEW]),
                    "approved": len([c for c in content_list if c.status == ContentStatus.APPROVED]),
                    "published": len([c for c in content_list if c.status == ContentStatus.PUBLISHED])
                }
            },
            "performance": {
                "total_reach": total_reach,
                "total_engagement": total_engagement,
                "avg_engagement_rate": round(avg_engagement_rate, 2),
                "cpe": round(allocated_budget / total_engagement, 4) if total_engagement > 0 else 0
            },
            "generated_at": get_current_utc().isoformat()
        }

    def get_kol_dashboard(self, kol_id: int) -> Dict[str, Any]:
        """
        Get KOL performance dashboard.

        Args:
            kol_id (int): KOL ID.

        Returns:
            Dict[str, Any]: KOL dashboard data.
        """
        kol = self.db.query(KOL).filter(KOL.id == kol_id).first()

        if not kol:
            return {"error": "KOL not found"}

        # Get collaborations
        collaborations = self.db.query(Collaboration).filter(
            Collaboration.kol_id == kol_id
        ).all()

        # Get content
        content_list = self.db.query(CampaignContent).filter(
            CampaignContent.kol_id == kol_id
        ).all()

        # Calculate earnings
        total_earnings = sum(c.compensation for c in collaborations if c.status == CollaborationStatus.COMPLETED)
        pending_earnings = sum(c.compensation for c in collaborations if c.status in [
            CollaborationStatus.ACCEPTED, CollaborationStatus.IN_PROGRESS
        ])

        # Performance metrics
        published_content = [c for c in content_list if c.status == ContentStatus.PUBLISHED]
        avg_engagement = (
            sum(c.engagement_rate or 0 for c in published_content) / len(published_content)
        ) if published_content else 0

        total_reach = sum(c.reach or 0 for c in published_content)

        return {
            "kol_id": kol_id,
            "name": kol.name,
            "platform": kol.platform,
            "profile": {
                "followers": kol.followers_count,
                "engagement_rate": kol.engagement_rate,
                "niche": kol.niche,
                "verified": kol.is_verified
            },
            "collaborations": {
                "total": len(collaborations),
                "active": len([c for c in collaborations if c.status == CollaborationStatus.IN_PROGRESS]),
                "completed": len([c for c in collaborations if c.status == CollaborationStatus.COMPLETED])
            },
            "content": {
                "total": len(content_list),
                "published": len(published_content),
                "pending_approval": len([c for c in content_list if c.status == ContentStatus.PENDING_REVIEW])
            },
            "earnings": {
                "total_earned": total_earnings,
                "pending": pending_earnings,
                "total_value": total_earnings + pending_earnings
            },
            "performance": {
                "avg_engagement_rate": round(avg_engagement, 2),
                "total_reach": total_reach,
                "content_approval_rate": round(
                    len([c for c in content_list if c.status in [ContentStatus.APPROVED, ContentStatus.PUBLISHED]]) /
                    len(content_list) * 100, 2
                ) if content_list else 0
            },
            "generated_at": get_current_utc().isoformat()
        }

    def get_trending_kols(self, limit: int = 10, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trending KOLs based on recent performance.

        Args:
            limit (int): Number of KOLs to return.
            platform (Optional[str]): Filter by platform.

        Returns:
            List[Dict[str, Any]]: List of trending KOLs.
        """
        query = self.db.query(KOL)

        if platform:
            query = query.filter(KOL.platform == platform)

        # Order by engagement rate and followers
        kols = query.order_by(
            (KOL.engagement_rate * KOL.followers_count).desc()
        ).limit(limit).all()

        return [
            {
                "id": kol.id,
                "name": kol.name,
                "platform": kol.platform,
                "followers": kol.followers_count,
                "engagement_rate": kol.engagement_rate,
                "niche": kol.niche,
                "trend_score": round(kol.engagement_rate * (kol.followers_count / 1000), 2)
            }
            for kol in kols
        ]

    def get_active_campaigns_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all active campaigns.

        Returns:
            List[Dict[str, Any]]: List of active campaign summaries.
        """
        campaigns = self.db.query(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).all()

        summaries = []

        for campaign in campaigns:
            # Get quick stats
            collab_count = self.db.query(func.count(Collaboration.id)).filter(
                Collaboration.campaign_id == campaign.id
            ).scalar() or 0

            content_count = self.db.query(func.count(CampaignContent.id)).filter(
                and_(
                    CampaignContent.campaign_id == campaign.id,
                    CampaignContent.status == ContentStatus.PUBLISHED
                )
            ).scalar() or 0

            summaries.append({
                "id": campaign.id,
                "name": campaign.name,
                "start_date": campaign.start_date.isoformat(),
                "end_date": campaign.end_date.isoformat(),
                "budget": campaign.budget,
                "currency": campaign.currency,
                "kols_assigned": collab_count,
                "content_published": content_count,
                "days_remaining": max(0, (campaign.end_date - get_current_utc()).days)
            })

        return summaries

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent system activity.

        Args:
            limit (int): Number of activities to return.

        Returns:
            List[Dict[str, Any]]: List of recent activities.
        """
        activities = []

        # Recent campaigns
        recent_campaigns = self.db.query(Campaign).order_by(
            Campaign.created_at.desc()
        ).limit(5).all()

        for campaign in recent_campaigns:
            activities.append({
                "type": "campaign_created",
                "timestamp": campaign.created_at.isoformat(),
                "description": f"Campaign '{campaign.name}' created",
                "entity_id": campaign.id
            })

        # Recent content
        recent_content = self.db.query(CampaignContent).filter(
            CampaignContent.status == ContentStatus.PUBLISHED
        ).order_by(CampaignContent.published_at.desc()).limit(5).all()

        for content in recent_content:
            if content.published_at:
                activities.append({
                    "type": "content_published",
                    "timestamp": content.published_at.isoformat(),
                    "description": f"Content published on {content.platform}",
                    "entity_id": content.id
                })

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:limit]


def get_dashboard_service(db: Session) -> DashboardService:
    """
    Dependency for FastAPI to inject DashboardService.

    Args:
        db (Session): Database session.

    Returns:
        DashboardService: Service instance.
    """
    return DashboardService(db)
