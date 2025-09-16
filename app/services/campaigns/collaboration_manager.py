"""
Collaboration Management Service

Handles the workflow and business logic for KOL-Campaign collaborations:
- Invitation management and automation
- Approval workflows and status tracking
- Performance monitoring and evaluation
- Communication and notification management
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.campaigns import Campaign, CampaignBrief
from app.models.collaboration import Collaboration
from app.models.kols import KOL
from app.services.communication.factory import communication_factory
from app.tasks.communication import send_campaign_notifications

logger = logging.getLogger(__name__)


class CollaborationManager:
    """
    Service for managing KOL-Campaign collaborations with automated workflows.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_collaboration_invitation(
        self,
        campaign_id: int,
        kol_ids: List[int],
        invitation_data: Dict[str, Any],
        created_by: int
    ) -> Dict[str, Any]:
        """
        Create collaboration invitations for multiple KOLs.

        Args:
            campaign_id: Campaign identifier
            kol_ids: List of KOL identifiers to invite
            invitation_data: Invitation configuration and compensation details
            created_by: User creating the invitations

        Returns:
            Results of invitation creation process
        """
        results = {
            "invitation_id": f"inv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "campaign_id": campaign_id,
            "sent_count": 0,
            "failed_count": 0,
            "scheduled_count": 0,
            "errors": []
        }

        try:
            # Verify campaign exists and is in valid state
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            if campaign.status not in ["draft", "approved"]:
                raise ValueError("Campaign must be in draft or approved status for invitations")

            # Process each KOL invitation
            for kol_id in kol_ids:
                try:
                    # Check if KOL exists and is eligible
                    kol = await self._get_kol(kol_id)
                    if not kol:
                        results["failed_count"] += 1
                        results["errors"].append({
                            "kol_id": kol_id,
                            "error": "KOL not found"
                        })
                        continue

                    if kol.status != "active":
                        results["failed_count"] += 1
                        results["errors"].append({
                            "kol_id": kol_id,
                            "error": "KOL is not active"
                        })
                        continue

                    # Check for existing collaboration
                    existing = await self._get_existing_collaboration(campaign_id, kol_id)
                    if existing:
                        results["failed_count"] += 1
                        results["errors"].append({
                            "kol_id": kol_id,
                            "error": "Collaboration already exists"
                        })
                        continue

                    # Create collaboration record
                    collaboration = await self._create_collaboration(
                        campaign_id, kol_id, invitation_data, created_by
                    )

                    # Send invitation notification
                    if invitation_data.get("send_immediately", True):
                        await self._send_invitation_notification(
                            collaboration, kol, campaign, invitation_data
                        )
                        results["sent_count"] += 1
                    else:
                        results["scheduled_count"] += 1

                except Exception as e:
                    results["failed_count"] += 1
                    results["errors"].append({
                        "kol_id": kol_id,
                        "error": str(e)
                    })
                    logger.error(f"Failed to create invitation for KOL {kol_id}: {str(e)}")

            await self.db.commit()

            logger.info(f"Collaboration invitations processed: {results}")
            return results

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create collaboration invitations: {str(e)}")
            raise

    async def process_collaboration_response(
        self,
        collaboration_id: int,
        response: str,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process KOL response to collaboration invitation.

        Args:
            collaboration_id: Collaboration identifier
            response: Response action (accept, reject, negotiate)
            response_data: Additional response data

        Returns:
            Processing results
        """
        try:
            collaboration = await self._get_collaboration(collaboration_id)
            if not collaboration:
                raise ValueError(f"Collaboration {collaboration_id} not found")

            if collaboration.status != "pending":
                raise ValueError("Collaboration is not in pending status")

            # Process different response types
            if response == "accept":
                collaboration.status = "approved"
                collaboration.approved_at = datetime.utcnow()

                # Send confirmation notification
                await self._send_collaboration_notification(
                    collaboration, "collaboration_accepted"
                )

            elif response == "reject":
                collaboration.status = "rejected"
                collaboration.rejected_at = datetime.utcnow()
                collaboration.rejection_reason = response_data.get("reason")

                # Send rejection notification
                await self._send_collaboration_notification(
                    collaboration, "collaboration_rejected"
                )

            elif response == "negotiate":
                collaboration.status = "negotiating"
                # Store negotiation terms
                if response_data:
                    collaboration.negotiation_terms = response_data.get("terms", {})

                # Send negotiation notification
                await self._send_collaboration_notification(
                    collaboration, "collaboration_negotiation"
                )

            else:
                raise ValueError(f"Invalid response type: {response}")

            collaboration.responded_at = datetime.utcnow()
            await self.db.commit()

            logger.info(f"Collaboration response processed: {collaboration_id} - {response}")
            return {
                "success": True,
                "collaboration_id": collaboration_id,
                "new_status": collaboration.status,
                "processed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to process collaboration response: {str(e)}")
            raise

    async def evaluate_collaboration_performance(
        self,
        collaboration_id: int
    ) -> Dict[str, Any]:
        """
        Evaluate collaboration performance and generate insights.

        Args:
            collaboration_id: Collaboration identifier

        Returns:
            Performance evaluation results
        """
        try:
            collaboration = await self._get_collaboration(collaboration_id)
            if not collaboration:
                raise ValueError(f"Collaboration {collaboration_id} not found")

            # Get collaboration metrics
            performance_data = await self._calculate_collaboration_metrics(collaboration)

            # Generate performance insights
            insights = await self._generate_performance_insights(collaboration, performance_data)

            # Update collaboration performance record
            collaboration.performance_score = performance_data.get("overall_score", 0)
            collaboration.last_evaluated = datetime.utcnow()

            await self.db.commit()

            return {
                "collaboration_id": collaboration_id,
                "performance_metrics": performance_data,
                "insights": insights,
                "evaluation_date": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to evaluate collaboration performance: {str(e)}")
            raise

    async def get_collaboration_analytics(
        self,
        campaign_id: Optional[int] = None,
        kol_id: Optional[int] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive collaboration analytics.

        Args:
            campaign_id: Optional campaign filter
            kol_id: Optional KOL filter
            date_range: Optional date range filter

        Returns:
            Collaboration analytics data
        """
        try:
            # Build base query
            query = select(Collaboration)

            if campaign_id:
                query = query.where(Collaboration.campaign_id == campaign_id)

            if kol_id:
                query = query.where(Collaboration.kol_id == kol_id)

            if date_range:
                start_date, end_date = date_range
                query = query.where(
                    and_(
                        Collaboration.created_at >= start_date,
                        Collaboration.created_at <= end_date
                    )
                )

            result = await self.db.execute(query)
            collaborations = result.scalars().all()

            # Calculate analytics
            analytics = {
                "total_collaborations": len(collaborations),
                "status_distribution": {},
                "success_rate": 0,
                "avg_response_time": 0,
                "performance_summary": {},
                "trends": {}
            }

            # Status distribution
            status_counts = {}
            response_times = []
            total_performance = 0
            performance_count = 0

            for collab in collaborations:
                # Status distribution
                status = collab.status
                status_counts[status] = status_counts.get(status, 0) + 1

                # Response time calculation
                if collab.responded_at and collab.created_at:
                    response_time = (collab.responded_at - collab.created_at).total_seconds() / 3600  # hours
                    response_times.append(response_time)

                # Performance aggregation
                if collab.performance_score:
                    total_performance += collab.performance_score
                    performance_count += 1

            analytics["status_distribution"] = status_counts

            # Calculate success rate (approved + completed / total)
            successful = status_counts.get("approved", 0) + status_counts.get("completed", 0)
            analytics["success_rate"] = (successful / len(collaborations) * 100) if collaborations else 0

            # Average response time
            analytics["avg_response_time"] = sum(response_times) / len(response_times) if response_times else 0

            # Performance summary
            analytics["performance_summary"] = {
                "avg_performance_score": total_performance / performance_count if performance_count else 0,
                "evaluated_collaborations": performance_count,
                "top_performers": await self._get_top_performing_collaborations(collaborations)
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get collaboration analytics: {str(e)}")
            raise

    # Helper methods
    async def _get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID."""
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_kol(self, kol_id: int) -> Optional[KOL]:
        """Get KOL by ID."""
        query = select(KOL).where(KOL.id == kol_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_collaboration(self, collaboration_id: int) -> Optional[Collaboration]:
        """Get collaboration by ID."""
        query = select(Collaboration).where(Collaboration.id == collaboration_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_existing_collaboration(self, campaign_id: int, kol_id: int) -> Optional[Collaboration]:
        """Check for existing collaboration between campaign and KOL."""
        query = select(Collaboration).where(
            and_(
                Collaboration.campaign_id == campaign_id,
                Collaboration.kol_id == kol_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _create_collaboration(
        self,
        campaign_id: int,
        kol_id: int,
        invitation_data: Dict[str, Any],
        created_by: int
    ) -> Collaboration:
        """Create collaboration record."""
        collaboration = Collaboration(
            campaign_id=campaign_id,
            kol_id=kol_id,
            compensation_amount=invitation_data.get("compensation", {}).get("amount"),
            compensation_type=invitation_data.get("compensation", {}).get("type"),
            deliverables=invitation_data.get("deliverables", {}),
            timeline=invitation_data.get("timeline", {}),
            status="pending",
            invitation_sent_at=datetime.utcnow(),
            created_by=created_by
        )

        self.db.add(collaboration)
        await self.db.flush()  # Get the ID without committing
        return collaboration

    async def _send_invitation_notification(
        self,
        collaboration: Collaboration,
        kol: KOL,
        campaign: Campaign,
        invitation_data: Dict[str, Any]
    ):
        """Send collaboration invitation notification."""
        notification_data = {
            "type": "collaboration_invitation",
            "collaboration_id": collaboration.id,
            "campaign_id": campaign.id,
            "kol_id": kol.id,
            "message": invitation_data.get("message", ""),
            "compensation": collaboration.compensation_amount,
            "deadline": invitation_data.get("deadline")
        }

        # Schedule notification task
        send_campaign_notifications.delay([notification_data])

    async def _send_collaboration_notification(
        self,
        collaboration: Collaboration,
        notification_type: str
    ):
        """Send collaboration status notification."""
        notification_data = {
            "type": notification_type,
            "collaboration_id": collaboration.id,
            "campaign_id": collaboration.campaign_id,
            "kol_id": collaboration.kol_id,
            "status": collaboration.status
        }

        # Schedule notification task
        send_campaign_notifications.delay([notification_data])

    async def _calculate_collaboration_metrics(
        self,
        collaboration: Collaboration
    ) -> Dict[str, Any]:
        """Calculate performance metrics for collaboration."""
        # This would integrate with content performance data
        # For now, return placeholder metrics
        return {
            "overall_score": 85.0,
            "deliverables_completed": 5,
            "deliverables_total": 6,
            "avg_engagement_rate": 4.2,
            "total_reach": 150000,
            "timeline_adherence": 90.0,
            "quality_score": 88.0
        }

    async def _generate_performance_insights(
        self,
        collaboration: Collaboration,
        performance_data: Dict[str, Any]
    ) -> List[str]:
        """Generate performance insights and recommendations."""
        insights = []

        # Analyze performance and generate insights
        if performance_data.get("overall_score", 0) >= 90:
            insights.append("Excellent collaboration performance - consider for future premium campaigns")

        if performance_data.get("timeline_adherence", 0) < 80:
            insights.append("Timeline adherence below expectations - may need closer project management")

        if performance_data.get("avg_engagement_rate", 0) > 5.0:
            insights.append("Outstanding engagement rates - content resonates well with audience")

        return insights

    async def _get_top_performing_collaborations(
        self,
        collaborations: List[Collaboration]
    ) -> List[Dict[str, Any]]:
        """Get top performing collaborations from the list."""
        # Sort by performance score and return top 5
        sorted_collabs = sorted(
            [c for c in collaborations if c.performance_score],
            key=lambda x: x.performance_score or 0,
            reverse=True
        )[:5]

        return [
            {
                "collaboration_id": collab.id,
                "kol_id": collab.kol_id,
                "campaign_id": collab.campaign_id,
                "performance_score": collab.performance_score
            }
            for collab in sorted_collabs
        ]


# Factory function for creating collaboration manager instances
def create_collaboration_manager(db_session: AsyncSession) -> CollaborationManager:
    """
    Create collaboration manager instance.

    Args:
        db_session: Database session

    Returns:
        CollaborationManager instance
    """
    return CollaborationManager(db_session)