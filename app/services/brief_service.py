"""Brief service for managing KOL briefs and templates."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlmodel import Session, select, func, or_, and_
from fastapi import HTTPException, status

from app.models.brief import Brief, BriefStatus
from app.models.brief_template import BriefTemplate
from app.models.campaign import Campaign
from app.models.kol import KOL
from app.models.user import User


class BriefService:
    """Service for managing briefs and brief templates."""

    def __init__(self, db: Session):
        self.db = db

    def create_brief(
        self,
        title: str,
        content: str,
        campaign_id: int,
        kol_id: int,
        created_by: int,
        template_id: Optional[int] = None,
        brief_data: Optional[Dict[str, Any]] = None,
        internal_notes: Optional[str] = None
    ) -> Brief:
        """Create a new brief."""
        # Validate campaign exists
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Validate KOL exists
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Validate template if provided
        if template_id:
            template = self.db.exec(
                select(BriefTemplate).where(
                    BriefTemplate.id == template_id,
                    BriefTemplate.is_active == True
                )
            ).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Brief template not found or inactive"
                )

        # Check for existing brief for this campaign-KOL combination
        existing_brief = self.db.exec(
            select(Brief).where(
                Brief.campaign_id == campaign_id,
                Brief.kol_id == kol_id,
                Brief.status != BriefStatus.REJECTED
            )
        ).first()
        
        if existing_brief:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brief already exists for this campaign and KOL"
            )

        # Create brief
        brief = Brief(
            title=title,
            content=content,
            brief_data=brief_data or {},
            campaign_id=campaign_id,
            kol_id=kol_id,
            template_id=template_id,
            created_by=created_by,
            internal_notes=internal_notes,
            status=BriefStatus.DRAFT
        )

        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        return brief

    def get_brief(self, brief_id: int) -> Optional[Brief]:
        """Get brief by ID."""
        return self.db.get(Brief, brief_id)

    def list_briefs(
        self,
        skip: int = 0,
        limit: int = 50,
        campaign_id: Optional[int] = None,
        kol_id: Optional[int] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Brief], int]:
        """List briefs with filters and pagination."""
        statement = select(Brief)
        
        # Apply filters
        if campaign_id:
            statement = statement.where(Brief.campaign_id == campaign_id)
        if kol_id:
            statement = statement.where(Brief.kol_id == kol_id)
        if status:
            statement = statement.where(Brief.status == status)
        if created_by:
            statement = statement.where(Brief.created_by == created_by)
        if search:
            statement = statement.where(
                or_(
                    Brief.title.ilike(f"%{search}%"),
                    Brief.content.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        count_statement = select(func.count(Brief.id))
        if campaign_id:
            count_statement = count_statement.where(Brief.campaign_id == campaign_id)
        if kol_id:
            count_statement = count_statement.where(Brief.kol_id == kol_id)
        if status:
            count_statement = count_statement.where(Brief.status == status)
        if created_by:
            count_statement = count_statement.where(Brief.created_by == created_by)
        if search:
            count_statement = count_statement.where(
                or_(
                    Brief.title.ilike(f"%{search}%"),
                    Brief.content.ilike(f"%{search}%")
                )
            )
        
        total = self.db.exec(count_statement).one()
        
        # Apply pagination and ordering
        statement = statement.order_by(Brief.created_at.desc())
        statement = statement.offset(skip).limit(limit)
        briefs = self.db.exec(statement).all()
        
        return list(briefs), total

    def update_brief(
        self,
        brief_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        brief_data: Optional[Dict[str, Any]] = None,
        internal_notes: Optional[str] = None,
        status: Optional[str] = None
    ) -> Brief:
        """Update a brief."""
        brief = self.get_brief(brief_id)
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief not found"
            )

        # Check if brief can be edited
        if not brief.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brief with status '{brief.status}' cannot be edited"
            )

        # Update fields
        if title is not None:
            brief.title = title
        if content is not None:
            brief.content = content
        if brief_data is not None:
            brief.brief_data = brief_data
        if internal_notes is not None:
            brief.internal_notes = internal_notes
        if status is not None:
            brief.status = status

        brief.updated_at = datetime.utcnow()

        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        return brief

    def update_brief_status(
        self,
        brief_id: int,
        status: str,
        user_id: int,
        kol_feedback: Optional[str] = None
    ) -> Brief:
        """Update brief status with workflow validation."""
        brief = self.get_brief(brief_id)
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief not found"
            )

        # Validate status transition
        valid_transitions = {
            BriefStatus.DRAFT: [BriefStatus.PENDING_REVIEW],
            BriefStatus.PENDING_REVIEW: [BriefStatus.APPROVED, BriefStatus.REJECTED, BriefStatus.DRAFT],
            BriefStatus.APPROVED: [BriefStatus.SENT],
            BriefStatus.SENT: [BriefStatus.ACKNOWLEDGED],
            BriefStatus.ACKNOWLEDGED: [BriefStatus.IN_PROGRESS],
            BriefStatus.IN_PROGRESS: [BriefStatus.COMPLETED],
            BriefStatus.REJECTED: [BriefStatus.DRAFT],
            BriefStatus.COMPLETED: []  # Final state
        }

        if status not in [s.value for s in valid_transitions.get(brief.status, [])]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{brief.status}' to '{status}'"
            )

        # Update status and related fields
        brief.status = status
        brief.updated_at = datetime.utcnow()

        if status == BriefStatus.APPROVED:
            brief.approved_by = user_id
            brief.approved_at = datetime.utcnow()
        elif status == BriefStatus.SENT:
            brief.sent_at = datetime.utcnow()
        elif status == BriefStatus.ACKNOWLEDGED:
            brief.acknowledged_at = datetime.utcnow()

        if kol_feedback:
            brief.kol_feedback = kol_feedback

        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        return brief

    def delete_brief(self, brief_id: int) -> None:
        """Delete a brief (only if in draft status)."""
        brief = self.get_brief(brief_id)
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief not found"
            )

        if brief.status != BriefStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft briefs can be deleted"
            )

        self.db.delete(brief)
        self.db.commit()

    def generate_brief_from_template(
        self,
        template_id: int,
        campaign_id: int,
        kol_id: int,
        created_by: int,
        variables: Dict[str, Any]
    ) -> Brief:
        """Generate a brief from a template with variable substitution."""
        template = self.db.exec(
            select(BriefTemplate).where(
                BriefTemplate.id == template_id,
                BriefTemplate.is_active == True
            )
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or inactive"
            )

        # Substitute variables in template content
        content = template.content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        # Generate title from template name and campaign
        campaign = self.db.get(Campaign, campaign_id)
        title = f"{template.name} - {campaign.name if campaign else 'Campaign'}"

        return self.create_brief(
            title=title,
            content=content,
            campaign_id=campaign_id,
            kol_id=kol_id,
            created_by=created_by,
            template_id=template_id,
            brief_data=variables
        )

    def create_bulk_briefs(
        self,
        campaign_id: int,
        kol_ids: List[int],
        template_id: int,
        created_by: int,
        variables: Dict[str, Any]
    ) -> List[Brief]:
        """Create briefs for multiple KOLs using a template."""
        briefs = []
        errors = []

        for kol_id in kol_ids:
            try:
                brief = self.generate_brief_from_template(
                    template_id=template_id,
                    campaign_id=campaign_id,
                    kol_id=kol_id,
                    created_by=created_by,
                    variables=variables
                )
                briefs.append(brief)
            except Exception as e:
                errors.append(f"KOL {kol_id}: {str(e)}")

        if errors and not briefs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create any briefs: {'; '.join(errors)}"
            )

        return briefs

    # Brief Template methods
    def create_brief_template(
        self,
        name: str,
        content: str,
        created_by: int,
        description: Optional[str] = None,
        category: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        is_default: bool = False
    ) -> BriefTemplate:
        """Create a new brief template."""
        template = BriefTemplate(
            name=name,
            description=description,
            content=content,
            variables=variables or {},
            category=category,
            is_default=is_default,
            created_by=created_by
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_brief_template(self, template_id: int) -> Optional[BriefTemplate]:
        """Get brief template by ID."""
        return self.db.get(BriefTemplate, template_id)

    def list_brief_templates(
        self,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[BriefTemplate], int]:
        """List brief templates with filters."""
        statement = select(BriefTemplate)
        
        if category:
            statement = statement.where(BriefTemplate.category == category)
        if is_active is not None:
            statement = statement.where(BriefTemplate.is_active == is_active)
        
        # Get total count
        count_statement = select(func.count(BriefTemplate.id))
        if category:
            count_statement = count_statement.where(BriefTemplate.category == category)
        if is_active is not None:
            count_statement = count_statement.where(BriefTemplate.is_active == is_active)
        
        total = self.db.exec(count_statement).one()
        
        # Apply pagination and ordering
        statement = statement.order_by(BriefTemplate.created_at.desc())
        statement = statement.offset(skip).limit(limit)
        templates = self.db.exec(statement).all()
        
        return list(templates), total

    def update_brief_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None
    ) -> BriefTemplate:
        """Update a brief template."""
        template = self.get_brief_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief template not found"
            )

        # Update fields
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if content is not None:
            template.content = content
        if category is not None:
            template.category = category
        if variables is not None:
            template.variables = variables
        if is_active is not None:
            template.is_active = is_active
        if is_default is not None:
            template.is_default = is_default

        template.updated_at = datetime.utcnow()

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_brief_template(self, template_id: int) -> None:
        """Delete a brief template (soft delete by setting inactive)."""
        template = self.get_brief_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief template not found"
            )

        # Check if template is being used by any briefs
        briefs_using_template = self.db.exec(
            select(func.count(Brief.id)).where(Brief.template_id == template_id)
        ).one()

        if briefs_using_template > 0:
            # Soft delete - just deactivate
            template.is_active = False
            template.updated_at = datetime.utcnow()
            self.db.add(template)
            self.db.commit()
        else:
            # Hard delete if no briefs are using it
            self.db.delete(template)
            self.db.commit()

    def get_brief_stats(self, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Get brief statistics."""
        base_query = select(func.count(Brief.id))
        
        if campaign_id:
            base_query = base_query.where(Brief.campaign_id == campaign_id)
        
        total_briefs = self.db.exec(base_query).one()
        
        # Get status breakdown
        status_query = select(Brief.status, func.count(Brief.id)).group_by(Brief.status)
        if campaign_id:
            status_query = status_query.where(Brief.campaign_id == campaign_id)
        
        status_counts = dict(self.db.exec(status_query).all())
        
        return {
            "total_briefs": total_briefs,
            "status_breakdown": status_counts,
            "draft": status_counts.get(BriefStatus.DRAFT, 0),
            "pending_review": status_counts.get(BriefStatus.PENDING_REVIEW, 0),
            "approved": status_counts.get(BriefStatus.APPROVED, 0),
            "sent": status_counts.get(BriefStatus.SENT, 0),
            "in_progress": status_counts.get(BriefStatus.IN_PROGRESS, 0),
            "completed": status_counts.get(BriefStatus.COMPLETED, 0),
            "rejected": status_counts.get(BriefStatus.REJECTED, 0)
        }