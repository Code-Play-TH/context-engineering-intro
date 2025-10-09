"""Brief service for managing KOL briefs and templates."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.brief import Brief, BriefStatus
from app.models.brief_template import BriefTemplate
from app.models.campaign import Campaign
from app.models.kol import KOL
from app.models.user import User
from app.schemas.brief import (
    BriefCreate, BriefUpdate, BriefStatusUpdate, BriefFilters,
    BriefTemplateCreate, BriefTemplateUpdate, GenerateBriefFromTemplate,
    BulkBriefCreate
)


class BriefService:
    """Service for managing briefs and brief templates."""

    @staticmethod
    def create_brief(db: Session, brief_data: BriefCreate, created_by: int) -> Brief:
        """Create a new brief."""
        # Validate campaign exists
        campaign = db.query(Campaign).filter(Campaign.id == brief_data.campaign_id).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Validate KOL exists
        kol = db.query(KOL).filter(KOL.id == brief_data.kol_id).first()
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Validate template if provided
        if brief_data.template_id:
            template = db.query(BriefTemplate).filter(
                BriefTemplate.id == brief_data.template_id,
                BriefTemplate.is_active == True
            ).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Brief template not found or inactive"
                )

        # Check for existing brief for this campaign-KOL combination
        existing_brief = db.query(Brief).filter(
            Brief.campaign_id == brief_data.campaign_id,
            Brief.kol_id == brief_data.kol_id,
            Brief.status != BriefStatus.REJECTED
        ).first()
        
        if existing_brief:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brief already exists for this campaign and KOL"
            )

        # Create brief
        brief = Brief(
            title=brief_data.title,
            content=brief_data.content,
            brief_data=brief_data.brief_data,
            campaign_id=brief_data.campaign_id,
            kol_id=brief_data.kol_id,
            template_id=brief_data.template_id,
            created_by=created_by,
            internal_notes=brief_data.internal_notes,
            status=BriefStatus.DRAFT
        )

        db.add(brief)
        db.commit()
        db.refresh(brief)
        return brief

    @staticmethod
    def get_brief(db: Session, brief_id: int) -> Optional[Brief]:
        """Get brief by ID with related data."""
        return db.query(Brief).options(
            joinedload(Brief.campaign),
            joinedload(Brief.kol),
            joinedload(Brief.template),
            joinedload(Brief.creator),
            joinedload(Brief.approver)
        ).filter(Brief.id == brief_id).first()

    @staticmethod
    def update_brief(db: Session, brief_id: int, brief_data: BriefUpdate, user_id: int) -> Brief:
        """Update a brief."""
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
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
        update_data = brief_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(brief, field, value)

        brief.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(brief)
        return brief

    @staticmethod
    def update_brief_status(
        db: Session, 
        brief_id: int, 
        status_data: BriefStatusUpdate, 
        user_id: int
    ) -> Brief:
        """Update brief status with workflow validation."""
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief not found"
            )

        old_status = brief.status
        new_status = status_data.status

        # Validate status transitions
        valid_transitions = {
            BriefStatus.DRAFT: [BriefStatus.PENDING_REVIEW, BriefStatus.REJECTED],
            BriefStatus.PENDING_REVIEW: [BriefStatus.APPROVED, BriefStatus.REJECTED, BriefStatus.DRAFT],
            BriefStatus.APPROVED: [BriefStatus.SENT, BriefStatus.REJECTED],
            BriefStatus.SENT: [BriefStatus.ACKNOWLEDGED, BriefStatus.IN_PROGRESS],
            BriefStatus.ACKNOWLEDGED: [BriefStatus.IN_PROGRESS],
            BriefStatus.IN_PROGRESS: [BriefStatus.COMPLETED],
            BriefStatus.REJECTED: [BriefStatus.DRAFT],
            BriefStatus.COMPLETED: []  # Final state
        }

        if new_status not in valid_transitions.get(old_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{old_status}' to '{new_status}'"
            )

        # Update status and related fields
        brief.status = new_status
        brief.updated_at = datetime.utcnow()

        if new_status == BriefStatus.APPROVED:
            brief.approved_by = user_id
            brief.approved_at = datetime.utcnow()
        elif new_status == BriefStatus.SENT:
            brief.sent_at = datetime.utcnow()
        elif new_status == BriefStatus.ACKNOWLEDGED:
            brief.acknowledged_at = datetime.utcnow()

        # Add notes if provided
        if status_data.notes:
            if brief.internal_notes:
                brief.internal_notes += f"\n\n[{datetime.utcnow()}] {status_data.notes}"
            else:
                brief.internal_notes = f"[{datetime.utcnow()}] {status_data.notes}"

        db.commit()
        db.refresh(brief)
        return brief

    @staticmethod
    def delete_brief(db: Session, brief_id: int, user_id: int) -> bool:
        """Delete a brief (only if in draft status)."""
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
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

        db.delete(brief)
        db.commit()
        return True

    @staticmethod
    def list_briefs(
        db: Session, 
        filters: BriefFilters, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Brief], int]:
        """List briefs with filtering and pagination."""
        query = db.query(Brief).options(
            joinedload(Brief.campaign),
            joinedload(Brief.kol),
            joinedload(Brief.template),
            joinedload(Brief.creator),
            joinedload(Brief.approver)
        )

        # Apply filters
        if filters.campaign_id:
            query = query.filter(Brief.campaign_id == filters.campaign_id)
        
        if filters.kol_id:
            query = query.filter(Brief.kol_id == filters.kol_id)
        
        if filters.status:
            query = query.filter(Brief.status == filters.status)
        
        if filters.created_by:
            query = query.filter(Brief.created_by == filters.created_by)
        
        if filters.approved_by:
            query = query.filter(Brief.approved_by == filters.approved_by)
        
        if filters.template_id:
            query = query.filter(Brief.template_id == filters.template_id)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Brief.title.ilike(search_term),
                    Brief.content.ilike(search_term)
                )
            )
        
        if filters.date_from:
            query = query.filter(Brief.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Brief.created_at <= filters.date_to)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        briefs = query.order_by(desc(Brief.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return briefs, total

    @staticmethod
    def generate_brief_from_template(
        db: Session, 
        generation_data: GenerateBriefFromTemplate, 
        created_by: int
    ) -> Brief:
        """Generate a brief from a template."""
        # Get template
        template = db.query(BriefTemplate).filter(
            BriefTemplate.id == generation_data.template_id,
            BriefTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or inactive"
            )

        # Get campaign and KOL for context
        campaign = db.query(Campaign).filter(Campaign.id == generation_data.campaign_id).first()
        kol = db.query(KOL).filter(KOL.id == generation_data.kol_id).first()
        
        if not campaign or not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign or KOL not found"
            )

        # Replace template variables
        content = template.content
        variables = {**template.variables, **generation_data.variable_values}
        
        # Add default variables
        default_vars = {
            "campaign_name": campaign.name,
            "kol_name": kol.name,
            "campaign_start_date": campaign.start_date.isoformat() if campaign.start_date else "",
            "campaign_end_date": campaign.end_date.isoformat() if campaign.end_date else "",
            "campaign_budget": campaign.total_budget or 0,
            "campaign_objectives": campaign.objectives or "",
        }
        variables.update(default_vars)

        # Replace placeholders in content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        # Use custom content if provided
        if generation_data.custom_content:
            content = generation_data.custom_content

        # Create brief
        brief_data = BriefCreate(
            title=f"{template.name} - {campaign.name} - {kol.name}",
            content=content,
            campaign_id=generation_data.campaign_id,
            kol_id=generation_data.kol_id,
            template_id=generation_data.template_id,
            brief_data=variables
        )

        return BriefService.create_brief(db, brief_data, created_by)

    @staticmethod
    def create_bulk_briefs(
        db: Session, 
        bulk_data: BulkBriefCreate, 
        created_by: int
    ) -> List[Brief]:
        """Create briefs for multiple KOLs."""
        briefs = []
        errors = []

        for kol_id in bulk_data.kol_ids:
            try:
                brief_data = BriefCreate(
                    title=bulk_data.title,
                    content=bulk_data.content,
                    campaign_id=bulk_data.campaign_id,
                    kol_id=kol_id,
                    template_id=bulk_data.template_id,
                    brief_data=bulk_data.brief_data
                )
                brief = BriefService.create_brief(db, brief_data, created_by)
                briefs.append(brief)
            except Exception as e:
                errors.append(f"KOL {kol_id}: {str(e)}")

        if errors and not briefs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create any briefs: {'; '.join(errors)}"
            )

        return briefs

    # Brief Template Methods
    @staticmethod
    def create_brief_template(
        db: Session, 
        template_data: BriefTemplateCreate, 
        created_by: int
    ) -> BriefTemplate:
        """Create a new brief template."""
        template = BriefTemplate(
            **template_data.dict(),
            created_by=created_by
        )

        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_brief_template(db: Session, template_id: int) -> Optional[BriefTemplate]:
        """Get brief template by ID."""
        return db.query(BriefTemplate).filter(BriefTemplate.id == template_id).first()

    @staticmethod
    def update_brief_template(
        db: Session, 
        template_id: int, 
        template_data: BriefTemplateUpdate
    ) -> BriefTemplate:
        """Update a brief template."""
        template = db.query(BriefTemplate).filter(BriefTemplate.id == template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief template not found"
            )

        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_brief_template(db: Session, template_id: int) -> bool:
        """Delete a brief template."""
        template = db.query(BriefTemplate).filter(BriefTemplate.id == template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brief template not found"
            )

        # Check if template is being used
        briefs_using_template = db.query(Brief).filter(Brief.template_id == template_id).count()
        if briefs_using_template > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete template that is being used by existing briefs"
            )

        db.delete(template)
        db.commit()
        return True

    @staticmethod
    def list_brief_templates(
        db: Session, 
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[BriefTemplate], int]:
        """List brief templates with filtering and pagination."""
        query = db.query(BriefTemplate)

        if category:
            query = query.filter(BriefTemplate.category == category)
        
        if is_active is not None:
            query = query.filter(BriefTemplate.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        templates = query.order_by(desc(BriefTemplate.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return templates, total

    @staticmethod
    def get_brief_stats(db: Session, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Get brief statistics."""
        query = db.query(Brief)
        
        if campaign_id:
            query = query.filter(Brief.campaign_id == campaign_id)

        total_briefs = query.count()

        # Count by status
        status_counts = db.query(
            Brief.status, func.count(Brief.id)
        ).group_by(Brief.status)
        
        if campaign_id:
            status_counts = status_counts.filter(Brief.campaign_id == campaign_id)
        
        by_status = {status: count for status, count in status_counts.all()}

        # Recent activity (last 10 briefs)
        recent_briefs = query.order_by(desc(Brief.updated_at)).limit(10).all()
        recent_activity = [
            {
                "id": brief.id,
                "title": brief.title,
                "status": brief.status,
                "updated_at": brief.updated_at
            }
            for brief in recent_briefs
        ]

        return {
            "total_briefs": total_briefs,
            "by_status": by_status,
            "recent_activity": recent_activity
        }