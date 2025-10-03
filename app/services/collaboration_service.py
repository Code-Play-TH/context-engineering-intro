"""
Collaboration service for managing KOL-Campaign collaborations.

This module handles the collaboration lifecycle between KOLs and campaigns,
including deliverable tracking, content approval, and payment management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.collaboration import Collaboration, CollaborationStatus
from app.models.campaign_content import CampaignContent, ContentStatus
from app.models.campaign import Campaign
from app.models.kol import KOL
from app.utils.datetime_utils import get_current_utc
import logging

logger = logging.getLogger(__name__)


class CollaborationService:
    """
    Service for managing KOL-Campaign collaborations.

    Handles:
    - Collaboration lifecycle
    - Deliverable tracking
    - Content submission and approval
    - Payment tracking
    """

    def __init__(self, db: Session):
        """
        Initialize collaboration service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def get_collaboration(self, collaboration_id: int) -> Optional[Collaboration]:
        """
        Get collaboration by ID.

        Args:
            collaboration_id (int): Collaboration ID.

        Returns:
            Optional[Collaboration]: Collaboration object or None.
        """
        return self.db.query(Collaboration).filter(
            Collaboration.id == collaboration_id
        ).first()

    def update_deliverables(
        self,
        collaboration_id: int,
        deliverables: Dict[str, Any]
    ) -> Optional[Collaboration]:
        """
        Update collaboration deliverables.

        Args:
            collaboration_id (int): Collaboration ID.
            deliverables (Dict[str, Any]): Updated deliverables.

        Returns:
            Optional[Collaboration]: Updated collaboration or None.
        """
        collaboration = self.get_collaboration(collaboration_id)

        if not collaboration:
            logger.error(f"Collaboration not found: {collaboration_id}")
            return None

        collaboration.deliverables = deliverables
        collaboration.updated_at = get_current_utc()

        self.db.commit()
        self.db.refresh(collaboration)

        logger.info(f"Deliverables updated for collaboration {collaboration_id}")
        return collaboration

    def submit_content(
        self,
        collaboration_id: int,
        content_type: str,
        content_url: str,
        platform: str,
        submitted_by: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[CampaignContent]:
        """
        Submit content for collaboration.

        Args:
            collaboration_id (int): Collaboration ID.
            content_type (str): Type of content (post, story, video, etc.).
            content_url (str): URL to the content.
            platform (str): Platform where content is posted.
            submitted_by (int): User ID submitting the content.
            metadata (Optional[Dict[str, Any]]): Additional metadata.

        Returns:
            Optional[CampaignContent]: Created content object or None.

        Raises:
            ValueError: If validation fails.
        """
        collaboration = self.get_collaboration(collaboration_id)

        if not collaboration:
            raise ValueError(f"Collaboration not found: {collaboration_id}")

        if collaboration.status not in [CollaborationStatus.IN_PROGRESS, CollaborationStatus.ACCEPTED]:
            raise ValueError(
                f"Cannot submit content for collaboration in status: {collaboration.status}"
            )

        # Create content record
        content = CampaignContent(
            collaboration_id=collaboration_id,
            campaign_id=collaboration.campaign_id,
            kol_id=collaboration.kol_id,
            content_type=content_type,
            content_url=content_url,
            platform=platform,
            status=ContentStatus.PENDING_REVIEW,
            metadata=metadata or {}
        )

        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)

        logger.info(f"Content submitted for collaboration {collaboration_id}")
        return content

    def approve_content(
        self,
        content_id: int,
        approved_by: int,
        notes: Optional[str] = None
    ) -> Optional[CampaignContent]:
        """
        Approve submitted content.

        Args:
            content_id (int): Content ID.
            approved_by (int): User ID approving the content.
            notes (Optional[str]): Approval notes.

        Returns:
            Optional[CampaignContent]: Updated content object or None.
        """
        content = self.db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content:
            logger.error(f"Content not found: {content_id}")
            return None

        content.status = ContentStatus.APPROVED
        content.approved_at = get_current_utc()
        content.approved_by = approved_by

        if notes:
            content.metadata = content.metadata or {}
            content.metadata["approval_notes"] = notes

        self.db.commit()
        self.db.refresh(content)

        logger.info(f"Content {content_id} approved by user {approved_by}")
        return content

    def reject_content(
        self,
        content_id: int,
        rejected_by: int,
        reason: str
    ) -> Optional[CampaignContent]:
        """
        Reject submitted content.

        Args:
            content_id (int): Content ID.
            rejected_by (int): User ID rejecting the content.
            reason (str): Rejection reason.

        Returns:
            Optional[CampaignContent]: Updated content object or None.
        """
        content = self.db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content:
            logger.error(f"Content not found: {content_id}")
            return None

        content.status = ContentStatus.REJECTED
        content.metadata = content.metadata or {}
        content.metadata["rejection_reason"] = reason
        content.metadata["rejected_by"] = rejected_by
        content.metadata["rejected_at"] = get_current_utc().isoformat()

        self.db.commit()
        self.db.refresh(content)

        logger.info(f"Content {content_id} rejected by user {rejected_by}")
        return content

    def get_collaboration_content(
        self,
        collaboration_id: int,
        status: Optional[ContentStatus] = None
    ) -> List[CampaignContent]:
        """
        Get all content for collaboration.

        Args:
            collaboration_id (int): Collaboration ID.
            status (Optional[ContentStatus]): Filter by status.

        Returns:
            List[CampaignContent]: List of content objects.
        """
        query = self.db.query(CampaignContent).filter(
            CampaignContent.collaboration_id == collaboration_id
        )

        if status:
            query = query.filter(CampaignContent.status == status)

        return query.order_by(CampaignContent.created_at.desc()).all()

    def get_collaboration_progress(self, collaboration_id: int) -> Dict[str, Any]:
        """
        Get collaboration progress summary.

        Args:
            collaboration_id (int): Collaboration ID.

        Returns:
            Dict[str, Any]: Progress summary.
        """
        collaboration = self.get_collaboration(collaboration_id)

        if not collaboration:
            return {}

        # Get all content
        all_content = self.get_collaboration_content(collaboration_id)

        content_by_status = {
            "pending": len([c for c in all_content if c.status == ContentStatus.PENDING_REVIEW]),
            "approved": len([c for c in all_content if c.status == ContentStatus.APPROVED]),
            "rejected": len([c for c in all_content if c.status == ContentStatus.REJECTED]),
            "published": len([c for c in all_content if c.status == ContentStatus.PUBLISHED]),
            "total": len(all_content)
        }

        # Calculate completion percentage
        deliverables = collaboration.deliverables or {}
        expected_count = deliverables.get("total_posts", 0)

        completion_percentage = 0
        if expected_count > 0:
            completion_percentage = min(100, (content_by_status["published"] / expected_count) * 100)

        return {
            "collaboration_id": collaboration_id,
            "status": collaboration.status.value,
            "content": content_by_status,
            "deliverables": deliverables,
            "expected_count": expected_count,
            "completion_percentage": round(completion_percentage, 2),
            "compensation": collaboration.compensation,
            "created_at": collaboration.created_at,
            "updated_at": collaboration.updated_at
        }

    def mark_collaboration_complete(
        self,
        collaboration_id: int,
        completed_by: int
    ) -> Optional[Collaboration]:
        """
        Mark collaboration as completed.

        Args:
            collaboration_id (int): Collaboration ID.
            completed_by (int): User ID marking as complete.

        Returns:
            Optional[Collaboration]: Updated collaboration or None.

        Raises:
            ValueError: If validation fails.
        """
        collaboration = self.get_collaboration(collaboration_id)

        if not collaboration:
            raise ValueError(f"Collaboration not found: {collaboration_id}")

        # Verify all deliverables are met
        progress = self.get_collaboration_progress(collaboration_id)

        if progress["completion_percentage"] < 100:
            raise ValueError(
                f"Cannot complete collaboration. Progress: {progress['completion_percentage']}%"
            )

        collaboration.status = CollaborationStatus.COMPLETED
        collaboration.updated_at = get_current_utc()

        self.db.commit()
        self.db.refresh(collaboration)

        logger.info(f"Collaboration {collaboration_id} marked as complete by user {completed_by}")
        return collaboration

    def get_kol_collaborations(
        self,
        kol_id: int,
        status: Optional[CollaborationStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all collaborations for a KOL.

        Args:
            kol_id (int): KOL ID.
            status (Optional[CollaborationStatus]): Filter by status.

        Returns:
            List[Dict[str, Any]]: List of collaborations with campaign details.
        """
        query = self.db.query(Collaboration, Campaign).join(
            Campaign, Collaboration.campaign_id == Campaign.id
        ).filter(Collaboration.kol_id == kol_id)

        if status:
            query = query.filter(Collaboration.status == status)

        results = query.order_by(Collaboration.created_at.desc()).all()

        return [
            {
                "collaboration_id": collab.id,
                "campaign": {
                    "id": campaign.id,
                    "name": campaign.name,
                    "status": campaign.status.value,
                    "start_date": campaign.start_date,
                    "end_date": campaign.end_date
                },
                "compensation": collab.compensation,
                "deliverables": collab.deliverables,
                "status": collab.status.value,
                "created_at": collab.created_at,
                "updated_at": collab.updated_at
            }
            for collab, campaign in results
        ]

    def get_payment_summary(self, collaboration_id: int) -> Dict[str, Any]:
        """
        Get payment summary for collaboration.

        Args:
            collaboration_id (int): Collaboration ID.

        Returns:
            Dict[str, Any]: Payment summary.
        """
        collaboration = self.get_collaboration(collaboration_id)

        if not collaboration:
            return {}

        campaign = self.db.query(Campaign).filter(
            Campaign.id == collaboration.campaign_id
        ).first()

        payment_status = "pending"
        if collaboration.status == CollaborationStatus.COMPLETED:
            payment_status = "ready_for_payment"
        elif collaboration.status in [CollaborationStatus.REJECTED, CollaborationStatus.CANCELLED]:
            payment_status = "cancelled"

        return {
            "collaboration_id": collaboration_id,
            "compensation": collaboration.compensation,
            "currency": campaign.currency if campaign else "USD",
            "payment_status": payment_status,
            "collaboration_status": collaboration.status.value,
            "kol_id": collaboration.kol_id,
            "campaign_id": collaboration.campaign_id
        }


def get_collaboration_service(db: Session) -> CollaborationService:
    """
    Dependency for FastAPI to inject CollaborationService.

    Args:
        db (Session): Database session.

    Returns:
        CollaborationService: Service instance.
    """
    return CollaborationService(db)
