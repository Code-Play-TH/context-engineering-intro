"""
Report Template Service for managing report templates.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.models.report_template import ReportTemplate
from app.schemas.report_template import (
    TemplateCreate, 
    TemplateUpdate, 
    TemplateFilters,
    TemplateDuplicateRequest
)
from app.core.database import get_session


class ReportTemplateService:
    """Service for managing report templates."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_template(self, template_data: TemplateCreate, created_by: int) -> ReportTemplate:
        """
        Create a new report template.
        
        Args:
            template_data: Template creation data
            created_by: ID of the user creating the template
            
        Returns:
            Created ReportTemplate instance
        """
        template = ReportTemplate(
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            is_shared=template_data.is_shared,
            structure=template_data.structure,
            variables=template_data.variables,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        
        return template
    
    async def get_template(self, template_id: int, user_id: Optional[int] = None) -> Optional[ReportTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            user_id: Optional user ID for access control
            
        Returns:
            ReportTemplate instance or None if not found
        """
        query = select(ReportTemplate).where(ReportTemplate.id == template_id)
        
        # If user_id provided, check access permissions
        if user_id is not None:
            query = query.where(
                or_(
                    ReportTemplate.is_shared == True,
                    ReportTemplate.created_by == user_id
                )
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_templates(
        self, 
        filters: TemplateFilters, 
        user_id: Optional[int] = None
    ) -> Tuple[List[ReportTemplate], int]:
        """
        List templates with filtering and pagination.
        
        Args:
            filters: Filter criteria
            user_id: Optional user ID for access control
            
        Returns:
            Tuple of (templates list, total count)
        """
        # Base query
        query = select(ReportTemplate)
        count_query = select(func.count(ReportTemplate.id))
        
        # Access control - user can see shared templates or their own
        if user_id is not None:
            access_filter = or_(
                ReportTemplate.is_shared == True,
                ReportTemplate.created_by == user_id
            )
            query = query.where(access_filter)
            count_query = count_query.where(access_filter)
        
        # Apply filters
        conditions = []
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    ReportTemplate.name.ilike(search_term),
                    ReportTemplate.description.ilike(search_term)
                )
            )
        
        if filters.template_type:
            conditions.append(ReportTemplate.template_type == filters.template_type)
        
        if filters.is_shared is not None:
            conditions.append(ReportTemplate.is_shared == filters.is_shared)
        
        if filters.created_by:
            conditions.append(ReportTemplate.created_by == filters.created_by)
        
        if conditions:
            filter_condition = and_(*conditions)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply ordering, pagination
        query = query.order_by(ReportTemplate.created_at.desc())
        query = query.offset(filters.offset).limit(filters.limit)
        
        # Execute query
        result = await self.session.execute(query)
        templates = result.scalars().all()
        
        return list(templates), total
    
    async def update_template(
        self, 
        template_id: int, 
        template_data: TemplateUpdate, 
        user_id: int
    ) -> Optional[ReportTemplate]:
        """
        Update a template.
        
        Args:
            template_id: Template ID
            template_data: Update data
            user_id: ID of the user updating the template
            
        Returns:
            Updated ReportTemplate instance or None if not found/no access
        """
        # Get template with access check
        template = await self.get_template(template_id, user_id)
        if not template:
            return None
        
        # Check if user can edit (owner or admin)
        if template.created_by != user_id:
            return None
        
        # Update fields
        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(template)
        
        return template
    
    async def delete_template(self, template_id: int, user_id: int) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            user_id: ID of the user deleting the template
            
        Returns:
            True if deleted, False if not found/no access
        """
        # Get template with access check
        template = await self.get_template(template_id, user_id)
        if not template:
            return False
        
        # Check if user can delete (owner only)
        if template.created_by != user_id:
            return False
        
        # TODO: Check if template is used in scheduled reports
        # For now, allow deletion
        
        await self.session.delete(template)
        await self.session.commit()
        
        return True
    
    async def duplicate_template(
        self, 
        template_id: int, 
        duplicate_data: TemplateDuplicateRequest, 
        user_id: int
    ) -> Optional[ReportTemplate]:
        """
        Duplicate a template.
        
        Args:
            template_id: Template ID to duplicate
            duplicate_data: Data for the new template
            user_id: ID of the user duplicating the template
            
        Returns:
            New ReportTemplate instance or None if original not found/no access
        """
        # Get original template
        original = await self.get_template(template_id, user_id)
        if not original:
            return None
        
        # Create duplicate
        duplicate = ReportTemplate(
            name=duplicate_data.name,
            description=duplicate_data.description,
            template_type=original.template_type,
            is_shared=duplicate_data.is_shared,
            structure=original.structure.copy(),  # Deep copy the structure
            variables=original.variables.copy(),  # Copy the variables list
            created_by=user_id,
            created_at=datetime.utcnow(),
            usage_count=0  # Reset usage count for duplicate
        )
        
        self.session.add(duplicate)
        await self.session.commit()
        await self.session.refresh(duplicate)
        
        return duplicate
    
    async def increment_usage_count(self, template_id: int) -> None:
        """
        Increment the usage count for a template.
        
        Args:
            template_id: Template ID
        """
        template = await self.session.get(ReportTemplate, template_id)
        if template:
            template.usage_count += 1
            await self.session.commit()
    
    async def get_popular_templates(
        self, 
        limit: int = 10, 
        user_id: Optional[int] = None
    ) -> List[ReportTemplate]:
        """
        Get popular templates based on usage count.
        
        Args:
            limit: Number of templates to return
            user_id: Optional user ID for access control
            
        Returns:
            List of popular ReportTemplate instances
        """
        query = select(ReportTemplate).order_by(ReportTemplate.usage_count.desc())
        
        # Access control
        if user_id is not None:
            query = query.where(
                or_(
                    ReportTemplate.is_shared == True,
                    ReportTemplate.created_by == user_id
                )
            )
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


# Dependency function for FastAPI
async def get_report_template_service() -> ReportTemplateService:
    """Get ReportTemplateService instance."""
    async with get_session() as session:
        yield ReportTemplateService(session)