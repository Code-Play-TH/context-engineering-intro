"""
Content tracking service for monitoring campaign content performance.

This module handles content lifecycle tracking, checkpoint analytics (D+1/3/7),
performance monitoring, and automated reporting.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.campaign_content import CampaignContent, ContentStatus
from app.models.collaboration import Collaboration
from app.models.campaign import Campaign
from app.models.kol import KOL
from app.utils.datetime_utils import get_current_utc, time_ago
from app.utils.metrics_normalization import (
    calculate_engagement_rate,
    calculate_virality_score,
    normalize_metrics,
    Platform
)
import logging

logger = logging.getLogger(__name__)


class CheckpointType:
    """Checkpoint timing constants."""
    D_PLUS_1 = "d+1"  # 1 day after publish
    D_PLUS_3 = "d+3"  # 3 days after publish
    D_PLUS_7 = "d+7"  # 7 days after publish
    D_PLUS_14 = "d+14"  # 14 days after publish
    D_PLUS_30 = "d+30"  # 30 days after publish


class ContentTrackingService:
    """
    Service for tracking content performance and checkpoints.

    Handles:
    - Content lifecycle monitoring
    - Performance metrics tracking
    - Checkpoint analytics (D+1, D+3, D+7)
    - Trend analysis
    - Automated reporting
    """

    def __init__(self, db: Session):
        """
        Initialize content tracking service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def track_content_publication(
        self,
        content_id: int,
        publish_date: datetime,
        initial_metrics: Optional[Dict[str, Any]] = None
    ) -> Optional[CampaignContent]:
        """
        Track content publication and initialize metrics.

        Args:
            content_id (int): Content ID.
            publish_date (datetime): Publication datetime.
            initial_metrics (Optional[Dict[str, Any]]): Initial metrics.

        Returns:
            Optional[CampaignContent]: Updated content object.
        """
        content = self.db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content:
            logger.error(f"Content not found: {content_id}")
            return None

        content.status = ContentStatus.PUBLISHED
        content.published_at = publish_date

        if initial_metrics:
            content.metrics = initial_metrics
            content.last_metrics_update = get_current_utc()

        self.db.commit()
        self.db.refresh(content)

        logger.info(f"Content published: {content_id}")
        return content

    def update_content_metrics(
        self,
        content_id: int,
        new_metrics: Dict[str, Any]
    ) -> Optional[CampaignContent]:
        """
        Update content performance metrics.

        Args:
            content_id (int): Content ID.
            new_metrics (Dict[str, Any]): New metrics data.

        Returns:
            Optional[CampaignContent]: Updated content object.
        """
        content = self.db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content:
            logger.error(f"Content not found: {content_id}")
            return None

        # Merge with existing metrics
        current_metrics = content.metrics or {}
        content.metrics = {**current_metrics, **new_metrics}
        content.last_metrics_update = get_current_utc()

        # Update calculated fields
        if "engagement_count" in new_metrics and "reach" in new_metrics:
            content.engagement_rate = calculate_engagement_rate(
                engagement_count=new_metrics["engagement_count"],
                followers=0,  # Use reach instead
                reach=new_metrics["reach"]
            )

        if "reach" in new_metrics:
            content.reach = new_metrics["reach"]

        if "impressions" in new_metrics:
            content.impressions = new_metrics["impressions"]

        self.db.commit()
        self.db.refresh(content)

        logger.info(f"Metrics updated for content {content_id}")
        return content

    def get_checkpoint_content(
        self,
        checkpoint_type: str,
        tolerance_hours: int = 2
    ) -> List[CampaignContent]:
        """
        Get content that needs checkpoint analysis.

        Args:
            checkpoint_type (str): Checkpoint type (d+1, d+3, d+7, etc.).
            tolerance_hours (int): Tolerance window in hours.

        Returns:
            List[CampaignContent]: Content ready for checkpoint.
        """
        now = get_current_utc()

        # Calculate target date range based on checkpoint type
        if checkpoint_type == CheckpointType.D_PLUS_1:
            target_days = 1
        elif checkpoint_type == CheckpointType.D_PLUS_3:
            target_days = 3
        elif checkpoint_type == CheckpointType.D_PLUS_7:
            target_days = 7
        elif checkpoint_type == CheckpointType.D_PLUS_14:
            target_days = 14
        elif checkpoint_type == CheckpointType.D_PLUS_30:
            target_days = 30
        else:
            logger.warning(f"Unknown checkpoint type: {checkpoint_type}")
            return []

        # Calculate date range
        target_date = now - timedelta(days=target_days)
        start_date = target_date - timedelta(hours=tolerance_hours)
        end_date = target_date + timedelta(hours=tolerance_hours)

        # Query published content within date range
        content_list = self.db.query(CampaignContent).filter(
            and_(
                CampaignContent.status == ContentStatus.PUBLISHED,
                CampaignContent.published_at >= start_date,
                CampaignContent.published_at <= end_date
            )
        ).all()

        logger.info(f"Found {len(content_list)} content items for {checkpoint_type} checkpoint")
        return content_list

    def analyze_checkpoint(
        self,
        content_id: int,
        checkpoint_type: str
    ) -> Dict[str, Any]:
        """
        Analyze content performance at checkpoint.

        Args:
            content_id (int): Content ID.
            checkpoint_type (str): Checkpoint type.

        Returns:
            Dict[str, Any]: Checkpoint analysis results.
        """
        content = self.db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content:
            return {"error": "Content not found"}

        metrics = content.metrics or {}

        # Calculate key performance indicators
        analysis = {
            "content_id": content_id,
            "checkpoint": checkpoint_type,
            "analyzed_at": get_current_utc().isoformat(),
            "published_at": content.published_at.isoformat() if content.published_at else None,
            "days_since_publish": (get_current_utc() - content.published_at).days if content.published_at else 0,
            "metrics": {
                "reach": metrics.get("reach", 0),
                "impressions": metrics.get("impressions", 0),
                "engagement_count": metrics.get("engagement_count", 0),
                "engagement_rate": content.engagement_rate or 0,
                "likes": metrics.get("likes", 0),
                "comments": metrics.get("comments", 0),
                "shares": metrics.get("shares", 0),
                "saves": metrics.get("saves", 0),
                "views": metrics.get("views", 0)
            }
        }

        # Calculate additional insights
        if "reach" in metrics and metrics["reach"] > 0:
            analysis["reach_to_engagement_ratio"] = round(
                metrics.get("engagement_count", 0) / metrics["reach"] * 100, 2
            )

        if "impressions" in metrics and "reach" in metrics and metrics["reach"] > 0:
            analysis["frequency"] = round(metrics["impressions"] / metrics["reach"], 2)

        # Performance rating
        analysis["performance_rating"] = self._calculate_performance_rating(
            content, checkpoint_type
        )

        return analysis

    def _calculate_performance_rating(
        self,
        content: CampaignContent,
        checkpoint_type: str
    ) -> str:
        """
        Calculate performance rating for content.

        Args:
            content (CampaignContent): Content object.
            checkpoint_type (str): Checkpoint type.

        Returns:
            str: Performance rating (excellent/good/average/poor).
        """
        engagement_rate = content.engagement_rate or 0

        # Different thresholds based on checkpoint
        if checkpoint_type == CheckpointType.D_PLUS_1:
            if engagement_rate >= 5:
                return "excellent"
            elif engagement_rate >= 3:
                return "good"
            elif engagement_rate >= 1.5:
                return "average"
            else:
                return "poor"

        elif checkpoint_type in [CheckpointType.D_PLUS_3, CheckpointType.D_PLUS_7]:
            if engagement_rate >= 4:
                return "excellent"
            elif engagement_rate >= 2.5:
                return "good"
            elif engagement_rate >= 1:
                return "average"
            else:
                return "poor"

        else:
            # D+14, D+30
            if engagement_rate >= 3:
                return "excellent"
            elif engagement_rate >= 2:
                return "good"
            elif engagement_rate >= 0.8:
                return "average"
            else:
                return "poor"

    def get_content_performance_trend(
        self,
        content_id: int
    ) -> Dict[str, Any]:
        """
        Get performance trend across all checkpoints.

        Args:
            content_id (int): Content ID.

        Returns:
            Dict[str, Any]: Performance trend data.
        """
        content = self.db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content or not content.published_at:
            return {"error": "Content not found or not published"}

        now = get_current_utc()
        days_since_publish = (now - content.published_at).days

        # Analyze all applicable checkpoints
        checkpoints = []

        for checkpoint in [CheckpointType.D_PLUS_1, CheckpointType.D_PLUS_3,
                          CheckpointType.D_PLUS_7, CheckpointType.D_PLUS_14,
                          CheckpointType.D_PLUS_30]:

            checkpoint_days = int(checkpoint.split('+')[1])

            if days_since_publish >= checkpoint_days:
                analysis = self.analyze_checkpoint(content_id, checkpoint)
                checkpoints.append(analysis)

        return {
            "content_id": content_id,
            "published_at": content.published_at.isoformat(),
            "days_since_publish": days_since_publish,
            "checkpoints": checkpoints,
            "trend_summary": self._calculate_trend_summary(checkpoints)
        }

    def _calculate_trend_summary(self, checkpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall trend from checkpoints."""
        if not checkpoints:
            return {"trend": "no_data"}

        # Get engagement rates from checkpoints
        rates = [cp["metrics"]["engagement_rate"] for cp in checkpoints]

        if len(rates) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trend
        first_rate = rates[0]
        last_rate = rates[-1]

        if last_rate > first_rate * 1.2:
            trend = "growing"
        elif last_rate < first_rate * 0.8:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "initial_engagement": first_rate,
            "current_engagement": last_rate,
            "change_percentage": round(((last_rate - first_rate) / first_rate * 100) if first_rate > 0 else 0, 2)
        }

    def get_campaign_content_summary(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Get summary of all content for a campaign.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            Dict[str, Any]: Campaign content summary.
        """
        content_list = self.db.query(CampaignContent).filter(
            CampaignContent.campaign_id == campaign_id
        ).all()

        total_content = len(content_list)
        published_content = [c for c in content_list if c.status == ContentStatus.PUBLISHED]

        # Calculate aggregate metrics
        total_reach = sum(c.reach or 0 for c in published_content)
        total_impressions = sum(c.impressions or 0 for c in published_content)
        total_engagement = sum(
            c.metrics.get("engagement_count", 0) if c.metrics else 0
            for c in published_content
        )

        avg_engagement_rate = (
            sum(c.engagement_rate or 0 for c in published_content) / len(published_content)
            if published_content else 0
        )

        # Performance distribution
        performance_ratings = [
            self._calculate_performance_rating(c, CheckpointType.D_PLUS_7)
            for c in published_content
            if c.published_at and (get_current_utc() - c.published_at).days >= 7
        ]

        return {
            "campaign_id": campaign_id,
            "total_content": total_content,
            "published_content": len(published_content),
            "pending_approval": len([c for c in content_list if c.status == ContentStatus.PENDING_REVIEW]),
            "aggregate_metrics": {
                "total_reach": total_reach,
                "total_impressions": total_impressions,
                "total_engagement": total_engagement,
                "avg_engagement_rate": round(avg_engagement_rate, 2)
            },
            "performance_distribution": {
                "excellent": performance_ratings.count("excellent"),
                "good": performance_ratings.count("good"),
                "average": performance_ratings.count("average"),
                "poor": performance_ratings.count("poor")
            },
            "generated_at": get_current_utc().isoformat()
        }

    def get_kol_content_performance(
        self,
        kol_id: int,
        campaign_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get content performance summary for a KOL.

        Args:
            kol_id (int): KOL ID.
            campaign_id (Optional[int]): Filter by campaign.

        Returns:
            Dict[str, Any]: KOL content performance summary.
        """
        query = self.db.query(CampaignContent).filter(
            CampaignContent.kol_id == kol_id
        )

        if campaign_id:
            query = query.filter(CampaignContent.campaign_id == campaign_id)

        content_list = query.all()
        published_content = [c for c in content_list if c.status == ContentStatus.PUBLISHED]

        if not published_content:
            return {
                "kol_id": kol_id,
                "total_content": len(content_list),
                "published_content": 0,
                "message": "No published content found"
            }

        # Calculate KOL performance metrics
        avg_engagement_rate = sum(c.engagement_rate or 0 for c in published_content) / len(published_content)
        total_reach = sum(c.reach or 0 for c in published_content)

        return {
            "kol_id": kol_id,
            "campaign_id": campaign_id,
            "total_content": len(content_list),
            "published_content": len(published_content),
            "performance": {
                "avg_engagement_rate": round(avg_engagement_rate, 2),
                "total_reach": total_reach,
                "total_engagement": sum(
                    c.metrics.get("engagement_count", 0) if c.metrics else 0
                    for c in published_content
                )
            },
            "content_breakdown": {
                "posts": len([c for c in published_content if c.content_type == "post"]),
                "stories": len([c for c in published_content if c.content_type == "story"]),
                "videos": len([c for c in published_content if c.content_type == "video"]),
                "reels": len([c for c in published_content if c.content_type == "reel"])
            }
        }

    def identify_underperforming_content(
        self,
        campaign_id: int,
        threshold_days: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identify underperforming content that needs attention.

        Args:
            campaign_id (int): Campaign ID.
            threshold_days (int): Days threshold for check.

        Returns:
            List[Dict[str, Any]]: List of underperforming content.
        """
        cutoff_date = get_current_utc() - timedelta(days=threshold_days)

        content_list = self.db.query(CampaignContent).filter(
            and_(
                CampaignContent.campaign_id == campaign_id,
                CampaignContent.status == ContentStatus.PUBLISHED,
                CampaignContent.published_at <= cutoff_date
            )
        ).all()

        underperforming = []

        for content in content_list:
            rating = self._calculate_performance_rating(content, CheckpointType.D_PLUS_3)

            if rating in ["poor", "average"]:
                underperforming.append({
                    "content_id": content.id,
                    "kol_id": content.kol_id,
                    "published_at": content.published_at.isoformat(),
                    "days_since_publish": (get_current_utc() - content.published_at).days,
                    "engagement_rate": content.engagement_rate or 0,
                    "reach": content.reach or 0,
                    "performance_rating": rating,
                    "content_url": content.content_url
                })

        return underperforming


def get_content_tracking_service(db: Session) -> ContentTrackingService:
    """
    Dependency for FastAPI to inject ContentTrackingService.

    Args:
        db (Session): Database session.

    Returns:
        ContentTrackingService: Service instance.
    """
    return ContentTrackingService(db)
