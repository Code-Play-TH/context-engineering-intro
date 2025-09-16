"""
AI-Powered Content Monitoring API Endpoints

Provides comprehensive content monitoring and analysis functionality:
- Real-time content monitoring and verification
- AI-powered content analysis and classification
- Brand safety and compliance checking
- Performance prediction and optimization
- Automated content moderation and flagging
- Content quality assessment and recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.content_monitoring import (
    ContentAnalysis, ContentFlag, ComplianceCheck, PerformancePrediction,
    BrandSafetyReport, ContentModeration
)
from app.models.campaigns import CampaignContent
from app.models.kols import KOL
from app.schemas.content_monitoring import (
    ContentAnalysisCreate, ContentAnalysisResponse, ContentAnalysisUpdate,
    ContentFlagCreate, ContentFlagResponse, ComplianceCheckResponse,
    PerformancePredictionResponse, BrandSafetyReportResponse,
    ContentModerationResponse, ContentMonitoringFilters,
    ContentAnalyticsRequest, ContentAnalyticsResponse,
    BulkContentAnalysisRequest, AIModelPrediction
)
from app.services.content_monitoring.ai_analyzer import AIContentAnalyzer
from app.services.content_monitoring.compliance_checker import ComplianceChecker
from app.services.content_monitoring.brand_safety import BrandSafetyAnalyzer
from app.tasks.content_monitoring import (
    analyze_content_batch, monitor_campaign_content,
    generate_compliance_report, update_performance_predictions
)
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content-monitoring", tags=["Content Monitoring"])


@router.post("/analyze", response_model=ContentAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_content(
    analysis_data: ContentAnalysisCreate,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ContentAnalysisResponse:
    """
    Analyze content using AI-powered analysis tools.

    Args:
        analysis_data: Content analysis configuration
        db: Database session
        current_user: Current authenticated user

    Returns:
        Content analysis results
    """
    try:
        # Initialize AI analyzer
        analyzer = AIContentAnalyzer()

        # Perform comprehensive content analysis
        analysis_result = await analyzer.analyze_content(
            content_url=analysis_data.content_url,
            content_text=analysis_data.content_text,
            media_urls=analysis_data.media_urls,
            analysis_types=analysis_data.analysis_types,
            platform=analysis_data.platform
        )

        # Create analysis record
        analysis = ContentAnalysis(
            content_url=analysis_data.content_url,
            content_text=analysis_data.content_text,
            media_urls=analysis_data.media_urls,
            platform=analysis_data.platform,
            campaign_id=analysis_data.campaign_id,
            kol_id=analysis_data.kol_id,
            analysis_types=analysis_data.analysis_types,

            # AI Analysis Results
            sentiment_score=analysis_result.get("sentiment", {}).get("score", 0),
            sentiment_label=analysis_result.get("sentiment", {}).get("label", "neutral"),
            emotion_scores=analysis_result.get("emotions", {}),
            topics=analysis_result.get("topics", []),
            entities=analysis_result.get("entities", []),
            hashtags_detected=analysis_result.get("hashtags", []),
            mentions_detected=analysis_result.get("mentions", []),

            # Content Classification
            content_categories=analysis_result.get("categories", []),
            content_type_detected=analysis_result.get("content_type", "unknown"),
            language_detected=analysis_result.get("language", "unknown"),

            # Quality Assessment
            quality_score=analysis_result.get("quality", {}).get("score", 0),
            engagement_prediction=analysis_result.get("engagement_prediction", 0),
            virality_score=analysis_result.get("virality_score", 0),

            # Brand Safety
            brand_safety_score=analysis_result.get("brand_safety", {}).get("score", 0),
            safety_flags=analysis_result.get("brand_safety", {}).get("flags", []),

            # Compliance
            compliance_score=analysis_result.get("compliance", {}).get("score", 0),
            compliance_issues=analysis_result.get("compliance", {}).get("issues", []),

            # Additional Metadata
            ai_confidence=analysis_result.get("confidence", 0),
            processing_time=analysis_result.get("processing_time", 0),
            analysis_version=analyzer.get_model_version(),

            status="completed",
            created_by=current_user.id
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        # Generate flags if issues detected
        await _generate_content_flags(db, analysis, analysis_result)

        logger.info(f"Content analysis completed: {analysis.id}")
        return ContentAnalysisResponse.model_validate(analysis)

    except Exception as e:
        await db.rollback()
        logger.error(f"Content analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content analysis failed"
        )


@router.post("/upload-analyze", response_model=ContentAnalysisResponse)
async def analyze_uploaded_content(
    file: UploadFile = File(...),
    platform: str = Query(..., description="Social media platform"),
    analysis_types: List[str] = Query(..., description="Types of analysis to perform"),
    campaign_id: Optional[int] = Query(None, description="Associated campaign ID"),
    kol_id: Optional[int] = Query(None, description="Associated KOL ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ContentAnalysisResponse:
    """
    Analyze uploaded media content.

    Args:
        file: Uploaded media file
        platform: Social media platform
        analysis_types: Types of analysis to perform
        campaign_id: Associated campaign ID
        kol_id: Associated KOL ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Content analysis results
    """
    try:
        # Validate file type and size
        if not file.content_type.startswith(('image/', 'video/', 'audio/')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only media files (image, video, audio) are supported"
            )

        # Save uploaded file temporarily
        file_path = await _save_uploaded_file(file)

        # Create analysis request
        analysis_data = ContentAnalysisCreate(
            content_url=None,
            content_text="",
            media_urls=[file_path],
            platform=platform,
            campaign_id=campaign_id,
            kol_id=kol_id,
            analysis_types=analysis_types
        )

        # Perform analysis
        result = await analyze_content(analysis_data, db, current_user)

        # Clean up temporary file
        await _cleanup_temp_file(file_path)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Uploaded content analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze uploaded content"
        )


@router.get("/analyses", response_model=List[ContentAnalysisResponse])
async def list_content_analyses(
    filters: ContentMonitoringFilters = Depends(),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[ContentAnalysisResponse]:
    """
    List content analyses with filtering options.

    Args:
        filters: Content monitoring filters
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of content analyses
    """
    try:
        # Build query with filters
        query = select(ContentAnalysis)

        if filters.platform:
            query = query.where(ContentAnalysis.platform.in_(filters.platform))

        if filters.campaign_id:
            query = query.where(ContentAnalysis.campaign_id.in_(filters.campaign_id))

        if filters.kol_id:
            query = query.where(ContentAnalysis.kol_id.in_(filters.kol_id))

        if filters.sentiment:
            query = query.where(ContentAnalysis.sentiment_label.in_(filters.sentiment))

        if filters.status:
            query = query.where(ContentAnalysis.status.in_(filters.status))

        if filters.min_quality_score:
            query = query.where(ContentAnalysis.quality_score >= filters.min_quality_score)

        if filters.max_quality_score:
            query = query.where(ContentAnalysis.quality_score <= filters.max_quality_score)

        if filters.min_brand_safety_score:
            query = query.where(ContentAnalysis.brand_safety_score >= filters.min_brand_safety_score)

        if filters.has_flags is not None:
            if filters.has_flags:
                query = query.where(ContentAnalysis.safety_flags != [])
            else:
                query = query.where(ContentAnalysis.safety_flags == [])

        if filters.date_from:
            query = query.where(ContentAnalysis.created_at >= filters.date_from)

        if filters.date_to:
            query = query.where(ContentAnalysis.created_at <= filters.date_to)

        # Order by creation date (newest first)
        query = query.order_by(ContentAnalysis.created_at.desc())

        # Execute paginated query
        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return [ContentAnalysisResponse.model_validate(analysis) for analysis in result.items]

    except Exception as e:
        logger.error(f"Failed to list content analyses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content analyses"
        )


@router.get("/analyses/{analysis_id}", response_model=ContentAnalysisResponse)
async def get_content_analysis(
    analysis_id: int = Path(..., description="Analysis ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ContentAnalysisResponse:
    """
    Get specific content analysis by ID.

    Args:
        analysis_id: Analysis identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Content analysis details
    """
    try:
        query = select(ContentAnalysis).where(ContentAnalysis.id == analysis_id)
        result = await db.execute(query)
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content analysis not found"
            )

        return ContentAnalysisResponse.model_validate(analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content analysis"
        )


@router.post("/bulk-analyze", response_model=Dict[str, Any])
async def bulk_analyze_content(
    request: BulkContentAnalysisRequest,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze multiple content items in bulk.

    Args:
        request: Bulk analysis request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Bulk analysis task information
    """
    try:
        # Validate request
        if len(request.content_items) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 content items allowed per bulk request"
            )

        # Schedule bulk analysis task
        task = analyze_content_batch.delay(
            content_items=[item.model_dump() for item in request.content_items],
            analysis_config=request.analysis_config.model_dump(),
            user_id=current_user.id
        )

        return {
            "task_id": task.id,
            "status": "scheduled",
            "content_items_count": len(request.content_items),
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk content analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule bulk content analysis"
        )


@router.get("/flags", response_model=List[ContentFlagResponse])
async def list_content_flags(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    flag_type: Optional[str] = Query(None, description="Filter by flag type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    campaign_id: Optional[int] = Query(None, description="Filter by campaign"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[ContentFlagResponse]:
    """
    List content flags and violations.

    Args:
        severity: Filter by severity level
        flag_type: Filter by flag type
        status: Filter by status
        campaign_id: Filter by campaign
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of content flags
    """
    try:
        query = select(ContentFlag)

        if severity:
            query = query.where(ContentFlag.severity == severity)

        if flag_type:
            query = query.where(ContentFlag.flag_type == flag_type)

        if status:
            query = query.where(ContentFlag.status == status)

        if campaign_id:
            # Join with ContentAnalysis to filter by campaign
            query = query.join(ContentAnalysis).where(ContentAnalysis.campaign_id == campaign_id)

        query = query.order_by(ContentFlag.created_at.desc())

        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return [ContentFlagResponse.model_validate(flag) for flag in result.items]

    except Exception as e:
        logger.error(f"Failed to list content flags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content flags"
        )


@router.put("/flags/{flag_id}", response_model=ContentFlagResponse)
async def update_content_flag(
    flag_id: int = Path(..., description="Flag ID"),
    status: str = Query(..., description="New status"),
    resolution_notes: Optional[str] = Query(None, description="Resolution notes"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ContentFlagResponse:
    """
    Update content flag status and resolution.

    Args:
        flag_id: Flag identifier
        status: New flag status
        resolution_notes: Resolution notes
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated content flag
    """
    try:
        query = select(ContentFlag).where(ContentFlag.id == flag_id)
        result = await db.execute(query)
        flag = result.scalar_one_or_none()

        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content flag not found"
            )

        # Update flag
        flag.status = status
        flag.resolution_notes = resolution_notes
        flag.resolved_at = datetime.utcnow() if status == "resolved" else None
        flag.resolved_by = current_user.id if status == "resolved" else None

        await db.commit()
        await db.refresh(flag)

        logger.info(f"Content flag updated: {flag.id} -> {status}")
        return ContentFlagResponse.model_validate(flag)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update content flag {flag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content flag"
        )


@router.get("/compliance/{campaign_id}", response_model=ComplianceCheckResponse)
async def get_campaign_compliance(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ComplianceCheckResponse:
    """
    Get compliance status for campaign content.

    Args:
        campaign_id: Campaign identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Campaign compliance report
    """
    try:
        # Get latest compliance check for campaign
        query = select(ComplianceCheck).where(
            ComplianceCheck.campaign_id == campaign_id
        ).order_by(ComplianceCheck.created_at.desc()).limit(1)

        result = await db.execute(query)
        compliance_check = result.scalar_one_or_none()

        if not compliance_check:
            # Generate new compliance check
            task = generate_compliance_report.delay(campaign_id)

            return ComplianceCheckResponse(
                id=0,
                campaign_id=campaign_id,
                overall_score=0,
                compliance_issues=[],
                recommendations=[],
                check_date=datetime.utcnow(),
                status="generating",
                task_id=task.id
            )

        return ComplianceCheckResponse.model_validate(compliance_check)

    except Exception as e:
        logger.error(f"Failed to get campaign compliance {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign compliance"
        )


@router.get("/performance-predictions", response_model=List[PerformancePredictionResponse])
async def get_performance_predictions(
    campaign_id: Optional[int] = Query(None, description="Filter by campaign"),
    kol_id: Optional[int] = Query(None, description="Filter by KOL"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    confidence_threshold: float = Query(0.7, description="Minimum confidence threshold"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[PerformancePredictionResponse]:
    """
    Get AI-powered performance predictions for content.

    Args:
        campaign_id: Filter by campaign
        kol_id: Filter by KOL
        platform: Filter by platform
        confidence_threshold: Minimum confidence threshold
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of performance predictions
    """
    try:
        query = select(PerformancePrediction).where(
            PerformancePrediction.confidence >= confidence_threshold
        )

        if campaign_id:
            query = query.where(PerformancePrediction.campaign_id == campaign_id)

        if kol_id:
            query = query.where(PerformancePrediction.kol_id == kol_id)

        if platform:
            query = query.where(PerformancePrediction.platform == platform)

        query = query.order_by(PerformancePrediction.predicted_engagement.desc())

        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return [PerformancePredictionResponse.model_validate(pred) for pred in result.items]

    except Exception as e:
        logger.error(f"Failed to get performance predictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance predictions"
        )


@router.post("/monitor-campaign/{campaign_id}", response_model=Dict[str, Any])
async def start_campaign_monitoring(
    campaign_id: int = Path(..., description="Campaign ID"),
    monitoring_config: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start real-time monitoring for campaign content.

    Args:
        campaign_id: Campaign identifier
        monitoring_config: Monitoring configuration
        db: Database session
        current_user: Current authenticated user

    Returns:
        Monitoring task information
    """
    try:
        # Verify campaign exists
        from app.models.campaigns import Campaign
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Start monitoring task
        task = monitor_campaign_content.delay(
            campaign_id=campaign_id,
            config=monitoring_config or {}
        )

        return {
            "monitoring_id": task.id,
            "campaign_id": campaign_id,
            "status": "started",
            "monitoring_config": monitoring_config,
            "started_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start campaign monitoring {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start campaign monitoring"
        )


@router.get("/brand-safety/{analysis_id}", response_model=BrandSafetyReportResponse)
async def get_brand_safety_report(
    analysis_id: int = Path(..., description="Analysis ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> BrandSafetyReportResponse:
    """
    Get detailed brand safety report for content analysis.

    Args:
        analysis_id: Content analysis identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Brand safety report
    """
    try:
        # Get content analysis
        analysis_query = select(ContentAnalysis).where(ContentAnalysis.id == analysis_id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content analysis not found"
            )

        # Get brand safety report
        query = select(BrandSafetyReport).where(
            BrandSafetyReport.content_analysis_id == analysis_id
        ).order_by(BrandSafetyReport.created_at.desc()).limit(1)

        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            # Generate brand safety report
            safety_analyzer = BrandSafetyAnalyzer()
            safety_result = await safety_analyzer.analyze_brand_safety(
                content_text=analysis.content_text,
                media_urls=analysis.media_urls,
                context={
                    "platform": analysis.platform,
                    "campaign_id": analysis.campaign_id
                }
            )

            report = BrandSafetyReport(
                content_analysis_id=analysis_id,
                overall_score=safety_result.get("overall_score", 0),
                risk_categories=safety_result.get("risk_categories", {}),
                detected_risks=safety_result.get("detected_risks", []),
                recommendations=safety_result.get("recommendations", []),
                confidence=safety_result.get("confidence", 0),
                analysis_version="1.0"
            )

            db.add(report)
            await db.commit()
            await db.refresh(report)

        return BrandSafetyReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get brand safety report {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve brand safety report"
        )


# Helper functions
async def _generate_content_flags(
    db: AsyncSession,
    analysis: ContentAnalysis,
    analysis_result: Dict[str, Any]
):
    """Generate content flags based on analysis results."""
    try:
        flags_to_create = []

        # Check brand safety issues
        if analysis.brand_safety_score < 0.7:  # Threshold for concern
            for flag_info in analysis.safety_flags:
                flag = ContentFlag(
                    content_analysis_id=analysis.id,
                    flag_type="brand_safety",
                    severity="medium" if analysis.brand_safety_score > 0.5 else "high",
                    description=flag_info.get("description", "Brand safety concern detected"),
                    confidence=flag_info.get("confidence", 0),
                    auto_generated=True,
                    status="pending"
                )
                flags_to_create.append(flag)

        # Check compliance issues
        if analysis.compliance_score < 0.8:  # Threshold for compliance
            for issue in analysis.compliance_issues:
                flag = ContentFlag(
                    content_analysis_id=analysis.id,
                    flag_type="compliance",
                    severity="high",
                    description=issue.get("description", "Compliance issue detected"),
                    confidence=issue.get("confidence", 0),
                    auto_generated=True,
                    status="pending"
                )
                flags_to_create.append(flag)

        # Add all flags to database
        for flag in flags_to_create:
            db.add(flag)

        await db.commit()

    except Exception as e:
        logger.error(f"Failed to generate content flags: {str(e)}")


async def _save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file temporarily and return path."""
    import uuid
    import aiofiles

    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'tmp'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"/tmp/uploads/{unique_filename}"

    # Ensure directory exists
    import os
    os.makedirs("/tmp/uploads", exist_ok=True)

    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    return file_path


async def _cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    import os
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")