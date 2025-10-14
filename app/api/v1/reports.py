"""
Report Generation API endpoints.
"""
import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.report_generation import ReportType, GenerationStatus
from app.services.report_generation_service import ReportGenerationService
from app.schemas.report_template import TemplateResponse

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportGenerationRequest(BaseModel):
    """Request schema for report generation."""
    template_id: int
    report_type: ReportType


class ReportGenerationResponse(BaseModel):
    """Response schema for report generation."""
    id: int
    campaign_id: int
    template_id: int
    report_type: ReportType
    status: GenerationStatus
    file_path: str = None
    download_url: str = None
    error_message: str = None
    generated_at: str
    expires_at: str = None
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Response schema for report list."""
    reports: List[ReportGenerationResponse]
    total: int
    limit: int
    offset: int


@router.post("/campaigns/{campaign_id}/generate", response_model=ReportGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    campaign_id: int,
    request: ReportGenerationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Generate a report for a campaign.
    
    This endpoint queues a background task to generate the report.
    Use the returned ID to check the generation status.
    
    - **campaign_id**: Campaign ID to generate report for
    - **template_id**: Template ID to use for generation
    - **report_type**: Type of report (powerpoint or pdf)
    
    Returns a 202 Accepted status with the generation job details.
    """
    service = ReportGenerationService(session)
    
    try:
        generation = await service.generate_report(
            campaign_id=campaign_id,
            template_id=request.template_id,
            report_type=request.report_type,
            generated_by=current_user.id
        )
        
        return ReportGenerationResponse(
            id=generation.id,
            campaign_id=generation.campaign_id,
            template_id=generation.template_id,
            report_type=generation.report_type,
            status=generation.status,
            file_path=generation.file_path,
            download_url=generation.download_url,
            error_message=generation.error_message,
            generated_at=generation.generated_at.isoformat(),
            expires_at=generation.expires_at.isoformat() if generation.expires_at else None
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}", response_model=ReportListResponse)
async def list_campaign_reports(
    campaign_id: int,
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all reports for a campaign.
    
    Returns a paginated list of all reports generated for the specified campaign.
    
    - **campaign_id**: Campaign ID to list reports for
    - **limit**: Number of results to return (max 100)
    - **offset**: Number of results to skip for pagination
    """
    service = ReportGenerationService(session)
    
    reports = await service.get_campaign_reports(
        campaign_id=campaign_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    report_responses = []
    for report in reports:
        report_responses.append(ReportGenerationResponse(
            id=report.id,
            campaign_id=report.campaign_id,
            template_id=report.template_id,
            report_type=report.report_type,
            status=report.status,
            file_path=report.file_path,
            download_url=report.download_url,
            error_message=report.error_message,
            generated_at=report.generated_at.isoformat(),
            expires_at=report.expires_at.isoformat() if report.expires_at else None
        ))
    
    return ReportListResponse(
        reports=report_responses,
        total=len(reports),  # TODO: Get actual total count
        limit=limit,
        offset=offset
    )


@router.get("/{generation_id}/status", response_model=ReportGenerationResponse)
async def get_report_status(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the status of a report generation.
    
    Returns the current status of the report generation job.
    
    - **generation_id**: Report generation ID
    """
    service = ReportGenerationService(session)
    
    generation = await service.get_generation_status(generation_id, current_user.id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report generation not found or access denied"
        )
    
    return ReportGenerationResponse(
        id=generation.id,
        campaign_id=generation.campaign_id,
        template_id=generation.template_id,
        report_type=generation.report_type,
        status=generation.status,
        file_path=generation.file_path,
        download_url=generation.download_url,
        error_message=generation.error_message,
        generated_at=generation.generated_at.isoformat(),
        expires_at=generation.expires_at.isoformat() if generation.expires_at else None
    )


@router.get("/{generation_id}/download")
async def download_report(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Download a generated report.
    
    Returns the generated report file for download.
    Only works for completed reports that haven't expired.
    
    - **generation_id**: Report generation ID
    """
    service = ReportGenerationService(session)
    
    # Get generation details
    generation = await service.get_generation_status(generation_id, current_user.id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report generation not found or access denied"
        )
    
    if generation.status != GenerationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready for download. Status: {generation.status.value}"
        )
    
    if generation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Report has expired and is no longer available for download"
        )
    
    if not generation.file_path or not os.path.exists(generation.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    # Determine media type based on file extension
    file_extension = os.path.splitext(generation.file_path)[1].lower()
    if file_extension == '.pptx':
        media_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    elif file_extension == '.pdf':
        media_type = 'application/pdf'
    else:
        media_type = 'application/octet-stream'
    
    # Generate filename for download
    filename = f"campaign_{generation.campaign_id}_report_{generation.id}{file_extension}"
    
    return FileResponse(
        path=generation.file_path,
        media_type=media_type,
        filename=filename
    )


@router.delete("/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a generated report.
    
    Removes the report file and marks the generation record as deleted.
    Only the user who generated the report can delete it.
    
    - **generation_id**: Report generation ID
    """
    service = ReportGenerationService(session)
    
    # Get generation details
    generation = await service.get_generation_status(generation_id, current_user.id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report generation not found or access denied"
        )
    
    # Delete file if it exists
    if generation.file_path and os.path.exists(generation.file_path):
        try:
            os.remove(generation.file_path)
        except OSError:
            pass  # File might be in use or already deleted
    
    # Update generation record
    await service.update_generation_status(
        generation_id,
        GenerationStatus.FAILED,  # Mark as failed to indicate it's no longer available
        file_path=None,
        download_url=None,
        error_message="Report deleted by user"
    )


# Storage management endpoints
@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get storage statistics for the report system.
    
    Returns information about disk usage, file counts, and storage health.
    Requires admin or campaign manager role.
    """
    # TODO: Add role-based access control
    # if current_user.role not in ['admin', 'campaign_manager']:
    #     raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    from app.services.file_storage_service import file_storage_service
    
    storage_stats = file_storage_service.get_storage_stats()
    disk_space = file_storage_service.get_available_space()
    
    return {
        "storage_stats": storage_stats,
        "disk_space": disk_space,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/storage/cleanup")
async def trigger_storage_cleanup(
    current_user: User = Depends(get_current_user)
):
    """
    Trigger manual storage cleanup.
    
    Manually triggers the cleanup of expired reports and old files.
    Requires admin role.
    """
    # TODO: Add role-based access control
    # if current_user.role != 'admin':
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from app.tasks.report_tasks import cleanup_expired_reports_task
        
        # Queue cleanup task
        task = cleanup_expired_reports_task.delay()
        
        return {
            "message": "Storage cleanup task queued successfully",
            "task_id": task.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue cleanup task: {str(e)}"
        )


# Health check endpoint for report generation system
@router.get("/health")
async def report_system_health():
    """
    Check the health of the report generation system.
    
    Returns system status and basic metrics.
    """
    from app.services.file_storage_service import file_storage_service
    
    # Get basic storage stats
    disk_space = file_storage_service.get_available_space()
    
    # Check if we have enough free space (at least 1GB)
    low_space_warning = disk_space.get('free_gb', 0) < 1.0
    
    # TODO: Add actual health checks
    # - Check if Celery workers are running
    # - Check if Redis is accessible
    
    status_value = "warning" if low_space_warning else "healthy"
    
    return {
        "status": status_value,
        "message": "Report generation system is operational",
        "disk_space_gb": disk_space.get('free_gb', 0),
        "low_space_warning": low_space_warning,
        "timestamp": datetime.utcnow().isoformat()
    }