"""
Report Generation Service for orchestrating report generation.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from celery import current_app as celery_app

from app.models.report_template import ReportTemplate
from app.models.report_generation import ReportGeneration, ReportType, GenerationStatus
from app.models.campaign import Campaign
from app.services.powerpoint_generation_service import PowerPointGenerationService
from app.services.pdf_generation_service import PDFGenerationService
from app.services.report_template_service import ReportTemplateService
# from app.tasks.report_tasks import generate_report_task  # Import moved to avoid circular dependency


class ReportGenerationService:
    """Service for orchestrating report generation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.template_service = ReportTemplateService(session)
        self.powerpoint_service = PowerPointGenerationService(session)
        self.pdf_service = PDFGenerationService(session)
    
    async def generate_report(
        self, 
        campaign_id: int, 
        template_id: int, 
        report_type: ReportType,
        generated_by: int
    ) -> ReportGeneration:
        """
        Generate a report (PowerPoint or PDF) from a template.
        
        Args:
            campaign_id: Campaign ID
            template_id: Template ID
            report_type: Type of report (powerpoint or pdf)
            generated_by: User ID who requested the generation
            
        Returns:
            ReportGeneration instance with job details
        """
        # Validate campaign exists
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Validate template exists and user has access
        template = await self.template_service.get_template(template_id, generated_by)
        if not template:
            raise ValueError(f"Template {template_id} not found or access denied")
        
        # Validate template type matches report type
        if template.template_type.value != report_type.value:
            raise ValueError(f"Template type {template.template_type} does not match requested report type {report_type}")
        
        # Create report generation record
        report_generation = ReportGeneration(
            campaign_id=campaign_id,
            template_id=template_id,
            report_type=report_type,
            status=GenerationStatus.PENDING,
            generated_by=generated_by,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.session.add(report_generation)
        await self.session.commit()
        await self.session.refresh(report_generation)
        
        # Queue background task for report generation
        try:
            from app.tasks.report_tasks import generate_report_task  # Import here to avoid circular dependency
            
            task = generate_report_task.delay(
                report_generation.id,
                campaign_id,
                template_id,
                report_type.value
            )
            
            # Update with task ID for tracking (if ReportGeneration model has task_id field)
            # report_generation.task_id = task.id
            await self.session.commit()
            
        except Exception as e:
            # If task queueing fails, mark as failed
            report_generation.status = GenerationStatus.FAILED
            report_generation.error_message = f"Failed to queue generation task: {str(e)}"
            await self.session.commit()
            raise
        
        # Increment template usage count
        await self.template_service.increment_usage_count(template_id)
        
        return report_generation
    
    async def get_generation_status(self, generation_id: int, user_id: int) -> Optional[ReportGeneration]:
        """
        Get the status of a report generation.
        
        Args:
            generation_id: Report generation ID
            user_id: User ID for access control
            
        Returns:
            ReportGeneration instance or None if not found/no access
        """
        query = (
            select(ReportGeneration)
            .where(
                ReportGeneration.id == generation_id,
                ReportGeneration.generated_by == user_id
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_generation_status(
        self, 
        generation_id: int, 
        status: GenerationStatus,
        file_path: Optional[str] = None,
        download_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[ReportGeneration]:
        """
        Update the status of a report generation.
        
        Args:
            generation_id: Report generation ID
            status: New status
            file_path: File path if generation completed
            download_url: Download URL if generation completed
            error_message: Error message if generation failed
            
        Returns:
            Updated ReportGeneration instance or None if not found
        """
        generation = await self.session.get(ReportGeneration, generation_id)
        if not generation:
            return None
        
        generation.status = status
        
        if file_path:
            generation.file_path = file_path
        
        if download_url:
            generation.download_url = download_url
        
        if error_message:
            generation.error_message = error_message
        
        await self.session.commit()
        await self.session.refresh(generation)
        
        return generation
    
    async def generate_report_sync(
        self, 
        campaign_id: int, 
        template_id: int, 
        report_type: ReportType
    ) -> str:
        """
        Generate a report synchronously (for background tasks).
        
        Args:
            campaign_id: Campaign ID
            template_id: Template ID
            report_type: Type of report (powerpoint or pdf)
            
        Returns:
            File path of generated report
        """
        # Get template
        template = await self.session.get(ReportTemplate, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Generate report based on type
        if report_type == ReportType.POWERPOINT:
            file_path = await self.powerpoint_service.generate_powerpoint(campaign_id, template)
        elif report_type == ReportType.PDF:
            file_path = await self.pdf_service.generate_pdf(campaign_id, template)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        return file_path
    
    async def get_campaign_reports(
        self, 
        campaign_id: int, 
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[ReportGeneration]:
        """
        Get all reports for a campaign.
        
        Args:
            campaign_id: Campaign ID
            user_id: User ID for access control
            limit: Number of results to return
            offset: Number of results to skip
            
        Returns:
            List of ReportGeneration instances
        """
        # Check if user has access to campaign
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            return []
        
        # TODO: Add proper campaign access control
        # For now, allow access to all users
        
        query = (
            select(ReportGeneration)
            .where(ReportGeneration.campaign_id == campaign_id)
            .order_by(ReportGeneration.generated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_download_url(self, generation_id: int, user_id: int) -> Optional[str]:
        """
        Get download URL for a generated report.
        
        Args:
            generation_id: Report generation ID
            user_id: User ID for access control
            
        Returns:
            Download URL or None if not found/expired/no access
        """
        generation = await self.get_generation_status(generation_id, user_id)
        
        if not generation:
            return None
        
        if generation.status != GenerationStatus.COMPLETED:
            return None
        
        if generation.is_expired:
            return None
        
        if not generation.file_path or not os.path.exists(generation.file_path):
            return None
        
        # Generate download URL (relative to uploads directory)
        if generation.file_path.startswith('uploads/'):
            return f"/{generation.file_path}"
        else:
            return f"/uploads/reports/{os.path.basename(generation.file_path)}"
    
    async def cleanup_expired_reports(self) -> int:
        """
        Clean up expired report files.
        
        Returns:
            Number of files cleaned up
        """
        # Get expired reports
        query = (
            select(ReportGeneration)
            .where(
                ReportGeneration.expires_at < datetime.utcnow(),
                ReportGeneration.status == GenerationStatus.COMPLETED,
                ReportGeneration.file_path.isnot(None)
            )
        )
        
        result = await self.session.execute(query)
        expired_reports = result.scalars().all()
        
        cleaned_count = 0
        
        for report in expired_reports:
            if report.file_path and os.path.exists(report.file_path):
                try:
                    os.remove(report.file_path)
                    cleaned_count += 1
                except OSError:
                    pass  # File might be in use or already deleted
                
                # Clear file path from database
                report.file_path = None
                report.download_url = None
        
        await self.session.commit()
        
        return cleaned_count
    
    async def _get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID."""
        return await self.session.get(Campaign, campaign_id)


# Dependency function for FastAPI
async def get_report_generation_service(session: AsyncSession) -> ReportGenerationService:
    """Get ReportGenerationService instance."""
    return ReportGenerationService(session)