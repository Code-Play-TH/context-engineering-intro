"""
Campaign service for managing campaign operations.

This module provides business logic for campaign lifecycle management,
KOL collaboration, timeline tracking, and budget allocation.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from decimal import Decimal

from app.models.campaign import Campaign, CampaignStatus
from app.models.collaboration import Collaboration, CollaborationStatus
from app.models.kol import KOL
from app.models.user import User
from app.utils.datetime_utils import get_current_utc, to_timezone
from app.utils.currency_utils import convert_currency, calculate_cost_metrics
import logging

logger = logging.getLogger(__name__)


class CampaignService:
    """
    Service for campaign lifecycle management.

    Handles:
    - Campaign CRUD operations
    - Status transitions
    - KOL assignment and collaboration
    - Timeline and milestone tracking
    - Budget allocation and monitoring
    """

    def __init__(self, db: Session):
        """
        Initialize campaign service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def create_campaign(
        self,
        name: str,
        description: str,
        budget: float,
        currency: str,
        start_date: datetime,
        end_date: datetime,
        created_by: int,
        **kwargs
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name (str): Campaign name.
            description (str): Campaign description.
            budget (float): Total budget.
            currency (str): Budget currency code.
            start_date (datetime): Campaign start date.
            end_date (datetime): Campaign end date.
            created_by (int): User ID who creates the campaign.
            **kwargs: Additional campaign fields.

        Returns:
            Campaign: Created campaign object.

        Raises:
            ValueError: If validation fails.
        """
        # Validate dates
        if end_date <= start_date:
            raise ValueError("End date must be after start date")

        if start_date < get_current_utc():
            logger.warning(f"Campaign start date is in the past: {start_date}")

        # Create campaign
        campaign = Campaign(
            name=name,
            description=description,
            budget=budget,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            status=CampaignStatus.DRAFT,
            **kwargs
        )

        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Campaign created: {campaign.id} - {campaign.name}")
        return campaign

    def update_campaign(
        self,
        campaign_id: int,
        **updates
    ) -> Optional[Campaign]:
        """
        Update campaign details.

        Args:
            campaign_id (int): Campaign ID.
            **updates: Fields to update.

        Returns:
            Optional[Campaign]: Updated campaign or None.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None

        # Update allowed fields
        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        campaign.updated_at = get_current_utc()
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Campaign updated: {campaign_id}")
        return campaign

    def change_status(
        self,
        campaign_id: int,
        new_status: CampaignStatus,
        changed_by: int
    ) -> Optional[Campaign]:
        """
        Change campaign status with validation.

        Args:
            campaign_id (int): Campaign ID.
            new_status (CampaignStatus): New status.
            changed_by (int): User ID making the change.

        Returns:
            Optional[Campaign]: Updated campaign or None.

        Raises:
            ValueError: If status transition is invalid.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None

        old_status = campaign.status

        # Validate status transition
        valid_transitions = {
            CampaignStatus.DRAFT: [CampaignStatus.PENDING_APPROVAL, CampaignStatus.CANCELLED],
            CampaignStatus.PENDING_APPROVAL: [CampaignStatus.ACTIVE, CampaignStatus.DRAFT, CampaignStatus.CANCELLED],
            CampaignStatus.ACTIVE: [CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELLED],
            CampaignStatus.PAUSED: [CampaignStatus.ACTIVE, CampaignStatus.CANCELLED],
            CampaignStatus.COMPLETED: [],  # Final state
            CampaignStatus.CANCELLED: [],  # Final state
        }

        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(
                f"Invalid status transition: {old_status} -> {new_status}"
            )

        campaign.status = new_status
        campaign.updated_at = get_current_utc()

        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Campaign {campaign_id} status changed: {old_status} -> {new_status} by user {changed_by}")
        return campaign

    def assign_kol(
        self,
        campaign_id: int,
        kol_id: int,
        compensation: float,
        deliverables: Dict[str, Any],
        assigned_by: int,
        notes: Optional[str] = None
    ) -> Optional[Collaboration]:
        """
        Assign KOL to campaign.

        Args:
            campaign_id (int): Campaign ID.
            kol_id (int): KOL ID to assign.
            compensation (float): Compensation amount.
            deliverables (Dict[str, Any]): Expected deliverables.
            assigned_by (int): User ID assigning the KOL.
            notes (Optional[str]): Additional notes.

        Returns:
            Optional[Collaboration]: Created collaboration or None.

        Raises:
            ValueError: If validation fails.
        """
        # Verify campaign exists
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Verify KOL exists
        kol = self.db.query(KOL).filter(KOL.id == kol_id).first()
        if not kol:
            raise ValueError(f"KOL not found: {kol_id}")

        # Check if already assigned
        existing = self.db.query(Collaboration).filter(
            and_(
                Collaboration.campaign_id == campaign_id,
                Collaboration.kol_id == kol_id,
                Collaboration.status != CollaborationStatus.REJECTED
            )
        ).first()

        if existing:
            raise ValueError(f"KOL {kol_id} already assigned to campaign {campaign_id}")

        # Check budget availability
        spent = self.get_allocated_budget(campaign_id)
        if spent + compensation > campaign.budget:
            raise ValueError(
                f"Insufficient budget. Available: {campaign.budget - spent}, Required: {compensation}"
            )

        # Create collaboration
        collaboration = Collaboration(
            campaign_id=campaign_id,
            kol_id=kol_id,
            compensation=compensation,
            deliverables=deliverables,
            status=CollaborationStatus.PENDING,
            notes=notes
        )

        self.db.add(collaboration)
        self.db.commit()
        self.db.refresh(collaboration)

        logger.info(f"KOL {kol_id} assigned to campaign {campaign_id} by user {assigned_by}")
        return collaboration

    def update_collaboration_status(
        self,
        collaboration_id: int,
        new_status: CollaborationStatus,
        updated_by: int
    ) -> Optional[Collaboration]:
        """
        Update collaboration status.

        Args:
            collaboration_id (int): Collaboration ID.
            new_status (CollaborationStatus): New status.
            updated_by (int): User ID making the update.

        Returns:
            Optional[Collaboration]: Updated collaboration or None.
        """
        collaboration = self.db.query(Collaboration).filter(
            Collaboration.id == collaboration_id
        ).first()

        if not collaboration:
            logger.error(f"Collaboration not found: {collaboration_id}")
            return None

        old_status = collaboration.status
        collaboration.status = new_status
        collaboration.updated_at = get_current_utc()

        self.db.commit()
        self.db.refresh(collaboration)

        logger.info(
            f"Collaboration {collaboration_id} status changed: {old_status} -> {new_status} by user {updated_by}"
        )
        return collaboration

    def get_allocated_budget(self, campaign_id: int) -> float:
        """
        Get total allocated budget for campaign.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            float: Total allocated budget.
        """
        result = self.db.query(func.sum(Collaboration.compensation)).filter(
            and_(
                Collaboration.campaign_id == campaign_id,
                Collaboration.status.in_([
                    CollaborationStatus.PENDING,
                    CollaborationStatus.ACCEPTED,
                    CollaborationStatus.IN_PROGRESS,
                    CollaborationStatus.COMPLETED
                ])
            )
        ).scalar()

        return float(result or 0)

    def get_budget_summary(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get campaign budget summary.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            Dict[str, Any]: Budget summary with allocation details.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            return {}

        allocated = self.get_allocated_budget(campaign_id)
        available = campaign.budget - allocated
        utilization_rate = (allocated / campaign.budget * 100) if campaign.budget > 0 else 0

        return {
            "total_budget": campaign.budget,
            "allocated": allocated,
            "available": available,
            "utilization_rate": round(utilization_rate, 2),
            "currency": campaign.currency,
            "status": "healthy" if utilization_rate < 90 else "warning" if utilization_rate < 100 else "over_budget"
        }

    def get_campaign_timeline(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get campaign timeline with milestones.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            Dict[str, Any]: Timeline information.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            return {}

        now = get_current_utc()
        total_days = (campaign.end_date - campaign.start_date).days
        elapsed_days = max(0, (now - campaign.start_date).days)
        remaining_days = max(0, (campaign.end_date - now).days)

        progress_percentage = min(100, (elapsed_days / total_days * 100) if total_days > 0 else 0)

        return {
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "current_date": now,
            "total_days": total_days,
            "elapsed_days": elapsed_days,
            "remaining_days": remaining_days,
            "progress_percentage": round(progress_percentage, 2),
            "status": campaign.status.value,
            "is_started": now >= campaign.start_date,
            "is_ended": now >= campaign.end_date
        }

    def get_campaign_kols(
        self,
        campaign_id: int,
        status: Optional[CollaborationStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all KOLs assigned to campaign.

        Args:
            campaign_id (int): Campaign ID.
            status (Optional[CollaborationStatus]): Filter by collaboration status.

        Returns:
            List[Dict[str, Any]]: List of KOL collaborations.
        """
        query = self.db.query(Collaboration, KOL).join(
            KOL, Collaboration.kol_id == KOL.id
        ).filter(Collaboration.campaign_id == campaign_id)

        if status:
            query = query.filter(Collaboration.status == status)

        results = query.all()

        return [
            {
                "collaboration_id": collab.id,
                "kol": {
                    "id": kol.id,
                    "name": kol.name,
                    "platform": kol.platform,
                    "followers_count": kol.followers_count,
                    "engagement_rate": kol.engagement_rate,
                    "niche": kol.niche
                },
                "compensation": collab.compensation,
                "deliverables": collab.deliverables,
                "status": collab.status.value,
                "created_at": collab.created_at,
                "updated_at": collab.updated_at
            }
            for collab, kol in results
        ]

    def get_campaign_performance(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get campaign performance metrics.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            Dict[str, Any]: Performance metrics.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            return {}

        # Get collaborations
        collaborations = self.db.query(Collaboration).filter(
            Collaboration.campaign_id == campaign_id
        ).all()

        total_kols = len(collaborations)
        active_kols = len([c for c in collaborations if c.status == CollaborationStatus.IN_PROGRESS])
        completed_kols = len([c for c in collaborations if c.status == CollaborationStatus.COMPLETED])

        # Calculate metrics
        total_compensation = sum(c.compensation for c in collaborations)

        # Get timeline
        timeline = self.get_campaign_timeline(campaign_id)

        # Get budget summary
        budget = self.get_budget_summary(campaign_id)

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "kols": {
                "total": total_kols,
                "active": active_kols,
                "completed": completed_kols,
                "pending": total_kols - active_kols - completed_kols
            },
            "budget": budget,
            "timeline": timeline,
            "total_compensation": total_compensation,
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at
        }

    def delete_campaign(self, campaign_id: int) -> bool:
        """
        Delete campaign (soft delete - mark as cancelled).

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            bool: True if deleted successfully.
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return False

        # Check if campaign can be deleted
        if campaign.status in [CampaignStatus.ACTIVE, CampaignStatus.IN_PROGRESS]:
            logger.warning(f"Cannot delete active campaign: {campaign_id}")
            return False

        campaign.status = CampaignStatus.CANCELLED
        campaign.updated_at = get_current_utc()

        self.db.commit()

        logger.info(f"Campaign cancelled: {campaign_id}")
        return True


def get_campaign_service(db: Session) -> CampaignService:
    """
    Dependency for FastAPI to inject CampaignService.

    Args:
        db (Session): Database session.

    Returns:
        CampaignService: Service instance.
    """
    return CampaignService(db)
