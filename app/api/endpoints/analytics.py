"""
Advanced Analytics and Reporting API Endpoints

Provides comprehensive analytics and reporting functionality:
- KOL performance analytics and insights
- Campaign performance tracking and ROI analysis
- Social media engagement metrics and trends
- Content performance analytics
- Platform-specific analytics and comparisons
- Custom dashboard data and visualizations
- Export functionality for reports and data
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.kols import KOL, KOLSocialMedia, KOLPerformance
from app.models.campaigns import Campaign, CampaignCollaboration, CampaignContent
from app.models.content_monitoring import ContentAnalysis, PerformancePrediction
from app.schemas.analytics import (
    AnalyticsRequest, AnalyticsResponse, KOLAnalyticsResponse,
    CampaignAnalyticsResponse, ContentAnalyticsResponse, PlatformAnalyticsResponse,
    DashboardResponse, ExportRequest, ExportResponse, TimeRange, MetricType,
    VisualizationData, ComparisonAnalysis, TrendAnalysis, ROIAnalysis
)
from app.services.analytics.analytics_engine import AnalyticsEngine
from app.services.analytics.report_generator import ReportGenerator
from app.services.analytics.data_exporter import DataExporter
from app.tasks.analytics import (
    generate_analytics_report, generate_kol_insights,
    update_performance_metrics, export_analytics_data
)
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for dashboard data"),
    include_predictions: bool = Query(True, description="Include performance predictions"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> DashboardResponse:
    """
    Get comprehensive dashboard data with key metrics and insights.

    Args:
        time_range: Time range for the analytics data
        include_predictions: Whether to include performance predictions
        db: Database session
        current_user: Current authenticated user

    Returns:
        Dashboard data with key metrics and visualizations
    """
    try:
        logger.info(f"Generating dashboard data for time range: {time_range}")

        analytics_engine = AnalyticsEngine()

        # Generate dashboard data
        dashboard_data = await analytics_engine.generate_dashboard_data(
            time_range=time_range,
            include_predictions=include_predictions,
            user_id=current_user.id,
            db=db
        )

        return DashboardResponse(**dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard data generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard data: {str(e)}"
        )


@router.get("/kols", response_model=List[KOLAnalyticsResponse])
async def get_kol_analytics(
    kol_ids: Optional[List[int]] = Query(None, description="Specific KOL IDs to analyze"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for analytics"),
    metrics: List[MetricType] = Query(default_factory=list, description="Specific metrics to include"),
    include_comparisons: bool = Query(False, description="Include peer comparisons"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[KOLAnalyticsResponse]:
    """
    Get comprehensive KOL performance analytics.

    Args:
        kol_ids: Optional list of specific KOL IDs
        time_range: Time range for the analytics
        metrics: Specific metrics to include in analysis
        include_comparisons: Whether to include peer comparisons
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of KOL analytics responses
    """
    try:
        logger.info(f"Generating KOL analytics for {len(kol_ids) if kol_ids else 'all'} KOLs")

        analytics_engine = AnalyticsEngine()

        # Get KOL analytics
        kol_analytics = await analytics_engine.analyze_kol_performance(
            kol_ids=kol_ids,
            time_range=time_range,
            metrics=metrics,
            include_comparisons=include_comparisons,
            pagination=pagination,
            user_id=current_user.id,
            db=db
        )

        return [KOLAnalyticsResponse(**analytics) for analytics in kol_analytics]

    except Exception as e:
        logger.error(f"KOL analytics generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate KOL analytics: {str(e)}"
        )


@router.get("/campaigns", response_model=List[CampaignAnalyticsResponse])
async def get_campaign_analytics(
    campaign_ids: Optional[List[int]] = Query(None, description="Specific campaign IDs to analyze"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for analytics"),
    include_roi: bool = Query(True, description="Include ROI analysis"),
    include_predictions: bool = Query(False, description="Include performance predictions"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[CampaignAnalyticsResponse]:
    """
    Get comprehensive campaign performance analytics.

    Args:
        campaign_ids: Optional list of specific campaign IDs
        time_range: Time range for the analytics
        include_roi: Whether to include ROI analysis
        include_predictions: Whether to include performance predictions
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of campaign analytics responses
    """
    try:
        logger.info(f"Generating campaign analytics for {len(campaign_ids) if campaign_ids else 'all'} campaigns")

        analytics_engine = AnalyticsEngine()

        # Get campaign analytics
        campaign_analytics = await analytics_engine.analyze_campaign_performance(
            campaign_ids=campaign_ids,
            time_range=time_range,
            include_roi=include_roi,
            include_predictions=include_predictions,
            pagination=pagination,
            user_id=current_user.id,
            db=db
        )

        return [CampaignAnalyticsResponse(**analytics) for analytics in campaign_analytics]

    except Exception as e:
        logger.error(f"Campaign analytics generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate campaign analytics: {str(e)}"
        )


@router.get("/content", response_model=ContentAnalyticsResponse)
async def get_content_analytics(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for analytics"),
    include_sentiment: bool = Query(True, description="Include sentiment analysis"),
    include_engagement_trends: bool = Query(True, description="Include engagement trends"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ContentAnalyticsResponse:
    """
    Get comprehensive content performance analytics.

    Args:
        content_type: Optional content type filter
        platform: Optional platform filter
        time_range: Time range for the analytics
        include_sentiment: Whether to include sentiment analysis
        include_engagement_trends: Whether to include engagement trends
        db: Database session
        current_user: Current authenticated user

    Returns:
        Content analytics response
    """
    try:
        logger.info(f"Generating content analytics for {content_type or 'all'} content on {platform or 'all platforms'}")

        analytics_engine = AnalyticsEngine()

        # Get content analytics
        content_analytics = await analytics_engine.analyze_content_performance(
            content_type=content_type,
            platform=platform,
            time_range=time_range,
            include_sentiment=include_sentiment,
            include_engagement_trends=include_engagement_trends,
            user_id=current_user.id,
            db=db
        )

        return ContentAnalyticsResponse(**content_analytics)

    except Exception as e:
        logger.error(f"Content analytics generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content analytics: {str(e)}"
        )


@router.get("/platforms", response_model=List[PlatformAnalyticsResponse])
async def get_platform_analytics(
    platforms: Optional[List[str]] = Query(None, description="Specific platforms to analyze"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for analytics"),
    include_comparisons: bool = Query(True, description="Include platform comparisons"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[PlatformAnalyticsResponse]:
    """
    Get platform-specific performance analytics and comparisons.

    Args:
        platforms: Optional list of specific platforms
        time_range: Time range for the analytics
        include_comparisons: Whether to include platform comparisons
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of platform analytics responses
    """
    try:
        logger.info(f"Generating platform analytics for {platforms or 'all platforms'}")

        analytics_engine = AnalyticsEngine()

        # Get platform analytics
        platform_analytics = await analytics_engine.analyze_platform_performance(
            platforms=platforms,
            time_range=time_range,
            include_comparisons=include_comparisons,
            user_id=current_user.id,
            db=db
        )

        return [PlatformAnalyticsResponse(**analytics) for analytics in platform_analytics]

    except Exception as e:
        logger.error(f"Platform analytics generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate platform analytics: {str(e)}"
        )


@router.get("/trends", response_model=TrendAnalysis)
async def get_trend_analysis(
    metric_type: MetricType = Query(..., description="Type of metric to analyze trends for"),
    time_range: TimeRange = Query(TimeRange.LAST_90_DAYS, description="Time range for trend analysis"),
    granularity: str = Query("daily", description="Trend granularity (daily, weekly, monthly)"),
    include_forecasts: bool = Query(False, description="Include trend forecasts"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> TrendAnalysis:
    """
    Get trend analysis for specific metrics.

    Args:
        metric_type: Type of metric to analyze
        time_range: Time range for the analysis
        granularity: Granularity of the trend data
        include_forecasts: Whether to include forecasts
        db: Database session
        current_user: Current authenticated user

    Returns:
        Trend analysis response
    """
    try:
        logger.info(f"Generating trend analysis for {metric_type} with {granularity} granularity")

        analytics_engine = AnalyticsEngine()

        # Get trend analysis
        trend_analysis = await analytics_engine.analyze_trends(
            metric_type=metric_type,
            time_range=time_range,
            granularity=granularity,
            include_forecasts=include_forecasts,
            user_id=current_user.id,
            db=db
        )

        return TrendAnalysis(**trend_analysis)

    except Exception as e:
        logger.error(f"Trend analysis generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend analysis: {str(e)}"
        )


@router.get("/comparisons", response_model=ComparisonAnalysis)
async def get_comparison_analysis(
    entity_type: str = Query(..., description="Type of entity to compare (kols, campaigns, content)"),
    entity_ids: List[int] = Query(..., description="Entity IDs to compare"),
    metrics: List[MetricType] = Query(..., description="Metrics to compare"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for comparison"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ComparisonAnalysis:
    """
    Get comparative analysis between entities.

    Args:
        entity_type: Type of entities to compare
        entity_ids: IDs of entities to compare
        metrics: Metrics to include in comparison
        time_range: Time range for the comparison
        db: Database session
        current_user: Current authenticated user

    Returns:
        Comparison analysis response
    """
    try:
        logger.info(f"Generating comparison analysis for {entity_type} entities")

        analytics_engine = AnalyticsEngine()

        # Get comparison analysis
        comparison_analysis = await analytics_engine.compare_entities(
            entity_type=entity_type,
            entity_ids=entity_ids,
            metrics=metrics,
            time_range=time_range,
            user_id=current_user.id,
            db=db
        )

        return ComparisonAnalysis(**comparison_analysis)

    except Exception as e:
        logger.error(f"Comparison analysis generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comparison analysis: {str(e)}"
        )


@router.get("/roi", response_model=ROIAnalysis)
async def get_roi_analysis(
    campaign_ids: Optional[List[int]] = Query(None, description="Specific campaign IDs for ROI analysis"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for ROI analysis"),
    include_projections: bool = Query(False, description="Include ROI projections"),
    breakdown_by: Optional[str] = Query(None, description="Break down ROI by (platform, kol, content_type)"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ROIAnalysis:
    """
    Get ROI (Return on Investment) analysis for campaigns.

    Args:
        campaign_ids: Optional list of specific campaign IDs
        time_range: Time range for the analysis
        include_projections: Whether to include ROI projections
        breakdown_by: Optional breakdown dimension
        db: Database session
        current_user: Current authenticated user

    Returns:
        ROI analysis response
    """
    try:
        logger.info(f"Generating ROI analysis for {len(campaign_ids) if campaign_ids else 'all'} campaigns")

        analytics_engine = AnalyticsEngine()

        # Get ROI analysis
        roi_analysis = await analytics_engine.analyze_roi(
            campaign_ids=campaign_ids,
            time_range=time_range,
            include_projections=include_projections,
            breakdown_by=breakdown_by,
            user_id=current_user.id,
            db=db
        )

        return ROIAnalysis(**roi_analysis)

    except Exception as e:
        logger.error(f"ROI analysis generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ROI analysis: {str(e)}"
        )


@router.post("/reports/generate", response_model=Dict[str, Any])
async def generate_custom_report(
    report_request: AnalyticsRequest,
    async_processing: bool = Query(False, description="Process report asynchronously"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate custom analytics report based on specified parameters.

    Args:
        report_request: Report configuration and parameters
        async_processing: Whether to process asynchronously
        db: Database session
        current_user: Current authenticated user

    Returns:
        Report generation response or task ID for async processing
    """
    try:
        logger.info(f"Generating custom analytics report: {report_request.report_name}")

        if async_processing:
            # Generate report asynchronously
            task = generate_analytics_report.delay(
                report_request.dict(),
                current_user.id
            )

            return {
                "task_id": task.id,
                "status": "processing",
                "message": "Report generation started",
                "estimated_completion": datetime.utcnow() + timedelta(minutes=10)
            }
        else:
            # Generate report synchronously
            report_generator = ReportGenerator()
            report_data = await report_generator.generate_report(
                report_request, current_user.id, db
            )

            return {
                "status": "completed",
                "report_data": report_data,
                "generated_at": datetime.utcnow()
            }

    except Exception as e:
        logger.error(f"Custom report generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom report: {str(e)}"
        )


@router.get("/reports/{report_id}", response_model=AnalyticsResponse)
async def get_report(
    report_id: str = Path(..., description="Report ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> AnalyticsResponse:
    """
    Get a previously generated analytics report.

    Args:
        report_id: ID of the report to retrieve
        db: Database session
        current_user: Current authenticated user

    Returns:
        Analytics report response
    """
    try:
        logger.info(f"Retrieving analytics report: {report_id}")

        # Get report from database
        # In production, this would query actual report records
        report_data = {
            "report_id": report_id,
            "report_name": "Custom Analytics Report",
            "generated_at": datetime.utcnow(),
            "data": {},
            "visualizations": [],
            "insights": [],
            "recommendations": []
        }

        return AnalyticsResponse(**report_data)

    except Exception as e:
        logger.error(f"Report retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )


@router.post("/export", response_model=ExportResponse)
async def export_analytics_data(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ExportResponse:
    """
    Export analytics data in various formats.

    Args:
        export_request: Export configuration and parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Export response with download information
    """
    try:
        logger.info(f"Exporting analytics data in {export_request.format} format")

        # Start export task
        task = export_analytics_data.delay(
            export_request.dict(),
            current_user.id
        )

        return ExportResponse(
            task_id=task.id,
            status="processing",
            format=export_request.format,
            estimated_completion=datetime.utcnow() + timedelta(minutes=5)
        )

    except Exception as e:
        logger.error(f"Analytics data export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics data: {str(e)}"
        )


@router.get("/export/{task_id}/download")
async def download_exported_data(
    task_id: str = Path(..., description="Export task ID"),
    current_user = Depends(get_current_user)
) -> StreamingResponse:
    """
    Download exported analytics data.

    Args:
        task_id: ID of the export task
        current_user: Current authenticated user

    Returns:
        Streaming response with the exported file
    """
    try:
        logger.info(f"Downloading exported data for task: {task_id}")

        data_exporter = DataExporter()
        file_stream, filename, content_type = await data_exporter.get_exported_file(
            task_id, current_user.id
        )

        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Data download failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export file not found: {task_id}"
        )


@router.get("/insights/kols/{kol_id}", response_model=Dict[str, Any])
async def get_kol_insights(
    kol_id: int = Path(..., description="KOL ID"),
    insight_types: List[str] = Query(default_factory=list, description="Types of insights to generate"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for insights"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get AI-powered insights for a specific KOL.

    Args:
        kol_id: ID of the KOL
        insight_types: Types of insights to generate
        time_range: Time range for the insights
        db: Database session
        current_user: Current authenticated user

    Returns:
        KOL insights and recommendations
    """
    try:
        logger.info(f"Generating insights for KOL {kol_id}")

        # Generate insights asynchronously
        task = generate_kol_insights.delay(kol_id, insight_types, time_range.value)

        return {
            "kol_id": kol_id,
            "task_id": task.id,
            "status": "generating",
            "message": "Insights generation started"
        }

    except Exception as e:
        logger.error(f"KOL insights generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate KOL insights: {str(e)}"
        )


@router.get("/visualizations/{visualization_type}", response_model=VisualizationData)
async def get_visualization_data(
    visualization_type: str = Path(..., description="Type of visualization"),
    entity_type: Optional[str] = Query(None, description="Entity type for visualization"),
    entity_ids: Optional[List[int]] = Query(None, description="Specific entity IDs"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS, description="Time range for visualization"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> VisualizationData:
    """
    Get data formatted for specific visualization types.

    Args:
        visualization_type: Type of visualization (chart, graph, heatmap, etc.)
        entity_type: Optional entity type filter
        entity_ids: Optional specific entity IDs
        time_range: Time range for the data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Visualization data response
    """
    try:
        logger.info(f"Generating {visualization_type} visualization data")

        analytics_engine = AnalyticsEngine()

        # Get visualization data
        viz_data = await analytics_engine.generate_visualization_data(
            visualization_type=visualization_type,
            entity_type=entity_type,
            entity_ids=entity_ids,
            time_range=time_range,
            user_id=current_user.id,
            db=db
        )

        return VisualizationData(**viz_data)

    except Exception as e:
        logger.error(f"Visualization data generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate visualization data: {str(e)}"
        )


@router.post("/metrics/update", response_model=Dict[str, Any])
async def update_metrics(
    force_update: bool = Query(False, description="Force update even if recently updated"),
    entity_types: Optional[List[str]] = Query(None, description="Specific entity types to update"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trigger manual update of performance metrics.

    Args:
        force_update: Whether to force update
        entity_types: Optional specific entity types to update
        db: Database session
        current_user: Current authenticated user

    Returns:
        Update status and information
    """
    try:
        logger.info("Triggering manual metrics update")

        # Start metrics update task
        task = update_performance_metrics.delay(
            force_update=force_update,
            entity_types=entity_types,
            user_id=current_user.id
        )

        return {
            "task_id": task.id,
            "status": "updating",
            "message": "Metrics update started",
            "entity_types": entity_types or "all"
        }

    except Exception as e:
        logger.error(f"Metrics update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update metrics: {str(e)}"
        )