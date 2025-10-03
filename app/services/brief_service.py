"""
Brief service for campaign brief management.

This module handles creation, templating, and distribution of campaign briefs
to KOLs with customization and versioning support.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.campaign import Campaign
from app.models.campaign_content import CampaignBrief, BriefStatus
from app.models.kol import KOL
from app.models.collaboration import Collaboration
from app.utils.datetime_utils import get_current_utc, format_datetime
import logging

logger = logging.getLogger(__name__)


class BriefTemplate:
    """Predefined brief templates."""

    STANDARD = "standard"
    DETAILED = "detailed"
    MINIMAL = "minimal"
    CUSTOM = "custom"

    @staticmethod
    def get_standard_template() -> Dict[str, Any]:
        """Get standard brief template."""
        return {
            "sections": [
                {
                    "title": "Campaign Overview",
                    "fields": ["name", "description", "objectives", "timeline"]
                },
                {
                    "title": "Target Audience",
                    "fields": ["demographics", "interests", "behaviors"]
                },
                {
                    "title": "Content Requirements",
                    "fields": ["platforms", "content_types", "posting_schedule"]
                },
                {
                    "title": "Brand Guidelines",
                    "fields": ["tone", "messaging", "hashtags", "mentions", "prohibited_content"]
                },
                {
                    "title": "Deliverables",
                    "fields": ["deliverable_list", "deadlines", "approval_process"]
                },
                {
                    "title": "Compensation",
                    "fields": ["amount", "payment_terms", "payment_schedule"]
                }
            ]
        }

    @staticmethod
    def get_detailed_template() -> Dict[str, Any]:
        """Get detailed brief template with all fields."""
        standard = BriefTemplate.get_standard_template()
        standard["sections"].extend([
            {
                "title": "Performance Metrics",
                "fields": ["kpis", "reporting_requirements", "tracking_methods"]
            },
            {
                "title": "Legal & Compliance",
                "fields": ["disclosure_requirements", "rights_usage", "exclusivity"]
            }
        ])
        return standard

    @staticmethod
    def get_minimal_template() -> Dict[str, Any]:
        """Get minimal brief template."""
        return {
            "sections": [
                {
                    "title": "Campaign Basics",
                    "fields": ["name", "description", "timeline"]
                },
                {
                    "title": "What We Need",
                    "fields": ["deliverable_list", "deadlines"]
                },
                {
                    "title": "Compensation",
                    "fields": ["amount", "payment_terms"]
                }
            ]
        }


class BriefService:
    """
    Service for campaign brief management.

    Handles:
    - Brief generation from templates
    - Customization and personalization
    - Version control
    - Distribution to KOLs
    """

    def __init__(self, db: Session):
        """
        Initialize brief service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def create_brief(
        self,
        campaign_id: int,
        template_type: str = BriefTemplate.STANDARD,
        customization: Optional[Dict[str, Any]] = None,
        created_by: int = 1
    ) -> Optional[CampaignBrief]:
        """
        Create campaign brief from template.

        Args:
            campaign_id (int): Campaign ID.
            template_type (str): Template type to use.
            customization (Optional[Dict[str, Any]]): Custom fields.
            created_by (int): User ID creating the brief.

        Returns:
            Optional[CampaignBrief]: Created brief or None.

        Raises:
            ValueError: If campaign not found.
        """
        # Get campaign
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            raise ValueError(f"Campaign not found: {campaign_id}")

        # Get template
        if template_type == BriefTemplate.DETAILED:
            template = BriefTemplate.get_detailed_template()
        elif template_type == BriefTemplate.MINIMAL:
            template = BriefTemplate.get_minimal_template()
        else:
            template = BriefTemplate.get_standard_template()

        # Generate brief content
        brief_content = self._generate_brief_content(campaign, template, customization)

        # Create brief
        brief = CampaignBrief(
            campaign_id=campaign_id,
            title=f"{campaign.name} - Campaign Brief",
            content=brief_content,
            template_type=template_type,
            version=1,
            status=BriefStatus.DRAFT,
            created_by=created_by
        )

        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)

        logger.info(f"Brief created for campaign {campaign_id}")
        return brief

    def _generate_brief_content(
        self,
        campaign: Campaign,
        template: Dict[str, Any],
        customization: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate brief content from campaign data and template.

        Args:
            campaign (Campaign): Campaign object.
            template (Dict[str, Any]): Brief template.
            customization (Optional[Dict[str, Any]]): Custom fields.

        Returns:
            Dict[str, Any]: Generated brief content.
        """
        content = {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "generated_at": get_current_utc().isoformat(),
            "sections": []
        }

        # Fill in each section
        for section in template["sections"]:
            section_data = {
                "title": section["title"],
                "content": {}
            }

            for field in section["fields"]:
                # Get data from campaign or customization
                if customization and field in customization:
                    section_data["content"][field] = customization[field]
                elif hasattr(campaign, field):
                    section_data["content"][field] = getattr(campaign, field)
                else:
                    # Generate default content based on field
                    section_data["content"][field] = self._get_default_field_value(field, campaign)

            content["sections"].append(section_data)

        return content

    def _get_default_field_value(self, field: str, campaign: Campaign) -> Any:
        """
        Get default value for a field.

        Args:
            field (str): Field name.
            campaign (Campaign): Campaign object.

        Returns:
            Any: Default field value.
        """
        defaults = {
            "timeline": f"{format_datetime(campaign.start_date, 'date')} to {format_datetime(campaign.end_date, 'date')}",
            "posting_schedule": "To be determined with KOL",
            "approval_process": "All content must be approved before publishing",
            "payment_terms": "Net 30 days after completion",
            "disclosure_requirements": "Follow FTC guidelines for sponsored content",
            "rights_usage": "Platform-wide usage rights for campaign duration"
        }
        return defaults.get(field, "To be specified")

    def update_brief(
        self,
        brief_id: int,
        updates: Dict[str, Any],
        create_new_version: bool = False
    ) -> Optional[CampaignBrief]:
        """
        Update brief content.

        Args:
            brief_id (int): Brief ID.
            updates (Dict[str, Any]): Updates to apply.
            create_new_version (bool): Create new version instead of updating.

        Returns:
            Optional[CampaignBrief]: Updated or new brief version.
        """
        brief = self.db.query(CampaignBrief).filter(CampaignBrief.id == brief_id).first()

        if not brief:
            logger.error(f"Brief not found: {brief_id}")
            return None

        if create_new_version:
            # Create new version
            new_brief = CampaignBrief(
                campaign_id=brief.campaign_id,
                title=brief.title,
                content={**brief.content, **updates},
                template_type=brief.template_type,
                version=brief.version + 1,
                status=BriefStatus.DRAFT,
                created_by=brief.created_by
            )

            self.db.add(new_brief)
            self.db.commit()
            self.db.refresh(new_brief)

            logger.info(f"New brief version created: v{new_brief.version}")
            return new_brief
        else:
            # Update existing brief
            brief.content = {**brief.content, **updates}
            brief.updated_at = get_current_utc()

            self.db.commit()
            self.db.refresh(brief)

            logger.info(f"Brief updated: {brief_id}")
            return brief

    def publish_brief(
        self,
        brief_id: int,
        published_by: int
    ) -> Optional[CampaignBrief]:
        """
        Publish brief (make it active).

        Args:
            brief_id (int): Brief ID.
            published_by (int): User ID publishing the brief.

        Returns:
            Optional[CampaignBrief]: Published brief or None.

        Raises:
            ValueError: If brief is not in draft status.
        """
        brief = self.db.query(CampaignBrief).filter(CampaignBrief.id == brief_id).first()

        if not brief:
            logger.error(f"Brief not found: {brief_id}")
            return None

        if brief.status != BriefStatus.DRAFT:
            raise ValueError(f"Cannot publish brief in status: {brief.status}")

        brief.status = BriefStatus.PUBLISHED
        brief.published_at = get_current_utc()
        brief.updated_at = get_current_utc()

        self.db.commit()
        self.db.refresh(brief)

        logger.info(f"Brief published: {brief_id} by user {published_by}")
        return brief

    def send_brief_to_kols(
        self,
        brief_id: int,
        kol_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Send brief to specific KOLs or all campaign KOLs.

        Args:
            brief_id (int): Brief ID.
            kol_ids (Optional[List[int]]): Specific KOL IDs to send to.

        Returns:
            Dict[str, Any]: Send result summary.

        Raises:
            ValueError: If brief not found or not published.
        """
        brief = self.db.query(CampaignBrief).filter(CampaignBrief.id == brief_id).first()

        if not brief:
            raise ValueError(f"Brief not found: {brief_id}")

        if brief.status != BriefStatus.PUBLISHED:
            raise ValueError(f"Brief must be published before sending")

        # Get KOLs to send to
        if kol_ids:
            kols = self.db.query(KOL).filter(KOL.id.in_(kol_ids)).all()
        else:
            # Get all KOLs assigned to campaign
            collaborations = self.db.query(Collaboration).filter(
                Collaboration.campaign_id == brief.campaign_id
            ).all()
            kol_ids = [c.kol_id for c in collaborations]
            kols = self.db.query(KOL).filter(KOL.id.in_(kol_ids)).all()

        # Send brief to each KOL (would integrate with email/notification service)
        sent_count = 0
        failed_count = 0

        for kol in kols:
            try:
                # Here you would call email/notification service
                # For now, we'll just log
                logger.info(f"Sending brief {brief_id} to KOL {kol.id} ({kol.email})")
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send brief to KOL {kol.id}: {e}")
                failed_count += 1

        return {
            "brief_id": brief_id,
            "total_kols": len(kols),
            "sent": sent_count,
            "failed": failed_count,
            "sent_at": get_current_utc().isoformat()
        }

    def get_brief_versions(self, campaign_id: int) -> List[CampaignBrief]:
        """
        Get all brief versions for a campaign.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            List[CampaignBrief]: List of brief versions.
        """
        briefs = self.db.query(CampaignBrief).filter(
            CampaignBrief.campaign_id == campaign_id
        ).order_by(CampaignBrief.version.desc()).all()

        return briefs

    def get_latest_brief(self, campaign_id: int) -> Optional[CampaignBrief]:
        """
        Get latest published brief for campaign.

        Args:
            campaign_id (int): Campaign ID.

        Returns:
            Optional[CampaignBrief]: Latest brief or None.
        """
        brief = self.db.query(CampaignBrief).filter(
            and_(
                CampaignBrief.campaign_id == campaign_id,
                CampaignBrief.status == BriefStatus.PUBLISHED
            )
        ).order_by(CampaignBrief.version.desc()).first()

        return brief

    def archive_brief(self, brief_id: int) -> bool:
        """
        Archive a brief.

        Args:
            brief_id (int): Brief ID.

        Returns:
            bool: True if archived successfully.
        """
        brief = self.db.query(CampaignBrief).filter(CampaignBrief.id == brief_id).first()

        if not brief:
            logger.error(f"Brief not found: {brief_id}")
            return False

        brief.status = BriefStatus.ARCHIVED
        brief.updated_at = get_current_utc()

        self.db.commit()

        logger.info(f"Brief archived: {brief_id}")
        return True


def get_brief_service(db: Session) -> BriefService:
    """
    Dependency for FastAPI to inject BriefService.

    Args:
        db (Session): Database session.

    Returns:
        BriefService: Service instance.
    """
    return BriefService(db)
