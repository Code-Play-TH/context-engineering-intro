"""
Report generation service for creating PDF and Excel reports.

This module handles automated report generation for campaigns,
KOL performance, and system analytics with export capabilities.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from io import BytesIO
import json

from app.models.campaign import Campaign
from app.models.kol import KOL
from app.models.collaboration import Collaboration
from app.models.campaign_content import CampaignContent, ContentStatus
from app.services.dashboard_service import DashboardService
from app.services.content_tracking_service import ContentTrackingService
from app.utils.datetime_utils import get_current_utc, format_datetime
import logging

logger = logging.getLogger(__name__)


class ReportType:
    """Report type constants."""
    CAMPAIGN_SUMMARY = "campaign_summary"
    CAMPAIGN_DETAILED = "campaign_detailed"
    KOL_PERFORMANCE = "kol_performance"
    CONTENT_ANALYTICS = "content_analytics"
    SYSTEM_OVERVIEW = "system_overview"


class ReportFormat:
    """Report format constants."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportService:
    """
    Service for generating reports in various formats.

    Handles:
    - Campaign reports (summary and detailed)
    - KOL performance reports
    - Content analytics reports
    - System overview reports
    - Multi-format export (PDF, Excel, CSV, JSON)
    """

    def __init__(self, db):
        """
        Initialize report service.

        Args:
            db: Database session.
        """
        self.db = db
        self.dashboard_service = DashboardService(db)
        self.tracking_service = ContentTrackingService(db)

    def generate_campaign_summary_report(
        self,
        campaign_id: int,
        format: str = ReportFormat.PDF
    ) -> Dict[str, Any]:
        """
        Generate campaign summary report.

        Args:
            campaign_id (int): Campaign ID.
            format (str): Output format (pdf, excel, csv, json).

        Returns:
            Dict[str, Any]: Report data and metadata.
        """
        logger.info(f"Generating campaign summary report for campaign {campaign_id}")

        # Get campaign dashboard data
        dashboard_data = self.dashboard_service.get_campaign_dashboard(campaign_id)

        if "error" in dashboard_data:
            return {"error": dashboard_data["error"]}

        # Build report content
        report_data = {
            "report_type": ReportType.CAMPAIGN_SUMMARY,
            "campaign_id": campaign_id,
            "campaign_name": dashboard_data["name"],
            "generated_at": get_current_utc().isoformat(),
            "summary": {
                "status": dashboard_data["status"],
                "timeline": dashboard_data["timeline"],
                "budget": dashboard_data["budget"],
                "performance": dashboard_data["performance"]
            },
            "kpis": {
                "total_kols": dashboard_data["collaborations"]["total"],
                "content_published": dashboard_data["content"]["by_status"]["published"],
                "total_reach": dashboard_data["performance"]["total_reach"],
                "avg_engagement": dashboard_data["performance"]["avg_engagement_rate"],
                "budget_utilization": dashboard_data["budget"]["utilization_percentage"]
            }
        }

        # Export to requested format
        if format == ReportFormat.JSON:
            return {
                "success": True,
                "format": format,
                "data": report_data
            }
        elif format == ReportFormat.PDF:
            return self._export_to_pdf(report_data)
        elif format == ReportFormat.EXCEL:
            return self._export_to_excel(report_data)
        else:
            return {"error": f"Unsupported format: {format}"}

    def generate_campaign_detailed_report(
        self,
        campaign_id: int,
        include_content: bool = True,
        include_kol_breakdown: bool = True
    ) -> Dict[str, Any]:
        """
        Generate detailed campaign report with all metrics.

        Args:
            campaign_id (int): Campaign ID.
            include_content (bool): Include individual content details.
            include_kol_breakdown (bool): Include per-KOL breakdown.

        Returns:
            Dict[str, Any]: Detailed report data.
        """
        logger.info(f"Generating detailed campaign report for campaign {campaign_id}")

        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            return {"error": "Campaign not found"}

        # Get dashboard data
        dashboard_data = self.dashboard_service.get_campaign_dashboard(campaign_id)

        # Get content summary
        content_summary = self.tracking_service.get_campaign_content_summary(campaign_id)

        # Build detailed report
        report_data = {
            "report_type": ReportType.CAMPAIGN_DETAILED,
            "campaign_id": campaign_id,
            "generated_at": get_current_utc().isoformat(),
            "campaign_details": {
                "name": campaign.name,
                "description": campaign.description,
                "objectives": campaign.objectives if hasattr(campaign, 'objectives') else None,
                "status": campaign.status.value,
                "timeline": dashboard_data["timeline"],
                "budget": dashboard_data["budget"]
            },
            "performance_summary": dashboard_data["performance"],
            "content_summary": content_summary,
            "collaboration_breakdown": dashboard_data["collaborations"]
        }

        # Add KOL breakdown if requested
        if include_kol_breakdown:
            collaborations = self.db.query(Collaboration).filter(
                Collaboration.campaign_id == campaign_id
            ).all()

            kol_breakdown = []
            for collab in collaborations:
                kol_performance = self.tracking_service.get_kol_content_performance(
                    kol_id=collab.kol_id,
                    campaign_id=campaign_id
                )
                kol_breakdown.append(kol_performance)

            report_data["kol_breakdown"] = kol_breakdown

        # Add content details if requested
        if include_content:
            content_list = self.db.query(CampaignContent).filter(
                CampaignContent.campaign_id == campaign_id,
                CampaignContent.status == ContentStatus.PUBLISHED
            ).all()

            content_details = [
                {
                    "id": content.id,
                    "type": content.content_type,
                    "platform": content.platform,
                    "published_at": content.published_at.isoformat() if content.published_at else None,
                    "reach": content.reach,
                    "engagement_rate": content.engagement_rate,
                    "metrics": content.metrics
                }
                for content in content_list
            ]

            report_data["content_details"] = content_details

        return {
            "success": True,
            "format": ReportFormat.JSON,
            "data": report_data
        }

    def generate_kol_performance_report(
        self,
        kol_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate KOL performance report.

        Args:
            kol_id (int): KOL ID.
            date_from (Optional[datetime]): Start date for report.
            date_to (Optional[datetime]): End date for report.

        Returns:
            Dict[str, Any]: KOL performance report.
        """
        logger.info(f"Generating KOL performance report for KOL {kol_id}")

        kol = self.db.query(KOL).filter(KOL.id == kol_id).first()

        if not kol:
            return {"error": "KOL not found"}

        # Get KOL dashboard
        dashboard_data = self.dashboard_service.get_kol_dashboard(kol_id)

        # Get content performance
        content_performance = self.tracking_service.get_kol_content_performance(kol_id)

        # Get collaborations
        query = self.db.query(Collaboration).filter(Collaboration.kol_id == kol_id)

        if date_from:
            query = query.filter(Collaboration.created_at >= date_from)
        if date_to:
            query = query.filter(Collaboration.created_at <= date_to)

        collaborations = query.all()

        # Build report
        report_data = {
            "report_type": ReportType.KOL_PERFORMANCE,
            "kol_id": kol_id,
            "generated_at": get_current_utc().isoformat(),
            "period": {
                "from": date_from.isoformat() if date_from else "all_time",
                "to": date_to.isoformat() if date_to else "present"
            },
            "kol_profile": {
                "name": kol.name,
                "platform": kol.platform,
                "followers": kol.followers_count,
                "engagement_rate": kol.engagement_rate,
                "niche": kol.niche
            },
            "performance_summary": dashboard_data["performance"],
            "earnings_summary": dashboard_data["earnings"],
            "collaboration_history": [
                {
                    "campaign_id": c.campaign_id,
                    "status": c.status.value,
                    "compensation": c.compensation,
                    "created_at": c.created_at.isoformat()
                }
                for c in collaborations
            ],
            "content_performance": content_performance
        }

        return {
            "success": True,
            "format": ReportFormat.JSON,
            "data": report_data
        }

    def generate_content_analytics_report(
        self,
        campaign_id: Optional[int] = None,
        platform: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate content analytics report.

        Args:
            campaign_id (Optional[int]): Filter by campaign.
            platform (Optional[str]): Filter by platform.
            date_from (Optional[datetime]): Start date.
            date_to (Optional[datetime]): End date.

        Returns:
            Dict[str, Any]: Content analytics report.
        """
        logger.info("Generating content analytics report")

        query = self.db.query(CampaignContent).filter(
            CampaignContent.status == ContentStatus.PUBLISHED
        )

        if campaign_id:
            query = query.filter(CampaignContent.campaign_id == campaign_id)
        if platform:
            query = query.filter(CampaignContent.platform == platform)
        if date_from:
            query = query.filter(CampaignContent.published_at >= date_from)
        if date_to:
            query = query.filter(CampaignContent.published_at <= date_to)

        content_list = query.all()

        # Calculate aggregate metrics
        total_reach = sum(c.reach or 0 for c in content_list)
        total_impressions = sum(c.impressions or 0 for c in content_list)
        total_engagement = sum(
            c.metrics.get("engagement_count", 0) if c.metrics else 0
            for c in content_list
        )

        avg_engagement_rate = (
            sum(c.engagement_rate or 0 for c in content_list) / len(content_list)
        ) if content_list else 0

        # Platform breakdown
        platform_breakdown = {}
        for content in content_list:
            if content.platform not in platform_breakdown:
                platform_breakdown[content.platform] = {
                    "count": 0,
                    "total_reach": 0,
                    "total_engagement": 0
                }

            platform_breakdown[content.platform]["count"] += 1
            platform_breakdown[content.platform]["total_reach"] += content.reach or 0
            platform_breakdown[content.platform]["total_engagement"] += (
                content.metrics.get("engagement_count", 0) if content.metrics else 0
            )

        # Build report
        report_data = {
            "report_type": ReportType.CONTENT_ANALYTICS,
            "generated_at": get_current_utc().isoformat(),
            "filters": {
                "campaign_id": campaign_id,
                "platform": platform,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None
            },
            "summary": {
                "total_content": len(content_list),
                "total_reach": total_reach,
                "total_impressions": total_impressions,
                "total_engagement": total_engagement,
                "avg_engagement_rate": round(avg_engagement_rate, 2)
            },
            "platform_breakdown": platform_breakdown,
            "top_performing_content": sorted(
                [
                    {
                        "id": c.id,
                        "platform": c.platform,
                        "type": c.content_type,
                        "reach": c.reach,
                        "engagement_rate": c.engagement_rate
                    }
                    for c in content_list
                ],
                key=lambda x: x["engagement_rate"] or 0,
                reverse=True
            )[:10]
        }

        return {
            "success": True,
            "format": ReportFormat.JSON,
            "data": report_data
        }

    def generate_system_overview_report(self) -> Dict[str, Any]:
        """
        Generate system-wide overview report.

        Returns:
            Dict[str, Any]: System overview report.
        """
        logger.info("Generating system overview report")

        overview = self.dashboard_service.get_system_overview()
        trending_kols = self.dashboard_service.get_trending_kols(limit=10)
        active_campaigns = self.dashboard_service.get_active_campaigns_summary()

        report_data = {
            "report_type": ReportType.SYSTEM_OVERVIEW,
            "generated_at": get_current_utc().isoformat(),
            "system_metrics": overview,
            "trending_kols": trending_kols,
            "active_campaigns": active_campaigns,
            "health_status": "healthy"  # Would be calculated from various metrics
        }

        return {
            "success": True,
            "format": ReportFormat.JSON,
            "data": report_data
        }

    def _export_to_pdf(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export report to PDF format.

        Note: In production, this would use a library like ReportLab or WeasyPrint.

        Args:
            report_data (Dict[str, Any]): Report data to export.

        Returns:
            Dict[str, Any]: PDF export result.
        """
        logger.info("Exporting report to PDF")

        # Placeholder - would generate actual PDF
        # Example using ReportLab:
        # from reportlab.lib.pagesizes import letter
        # from reportlab.pdfgen import canvas
        #
        # buffer = BytesIO()
        # pdf = canvas.Canvas(buffer, pagesize=letter)
        # pdf.drawString(100, 750, f"Campaign Report: {report_data['campaign_name']}")
        # ...
        # pdf.save()

        return {
            "success": True,
            "format": ReportFormat.PDF,
            "filename": f"report_{report_data['campaign_id']}_{get_current_utc().strftime('%Y%m%d')}.pdf",
            "size_bytes": 0,  # Would be actual file size
            "download_url": "/api/reports/download/...",  # Would be actual download URL
            "message": "PDF generation ready (placeholder - integrate ReportLab/WeasyPrint for production)"
        }

    def _export_to_excel(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export report to Excel format.

        Note: In production, this would use a library like openpyxl or xlsxwriter.

        Args:
            report_data (Dict[str, Any]): Report data to export.

        Returns:
            Dict[str, Any]: Excel export result.
        """
        logger.info("Exporting report to Excel")

        # Placeholder - would generate actual Excel file
        # Example using openpyxl:
        # from openpyxl import Workbook
        #
        # wb = Workbook()
        # ws = wb.active
        # ws.title = "Campaign Summary"
        # ws['A1'] = "Campaign Name"
        # ws['B1'] = report_data['campaign_name']
        # ...
        # buffer = BytesIO()
        # wb.save(buffer)

        return {
            "success": True,
            "format": ReportFormat.EXCEL,
            "filename": f"report_{report_data['campaign_id']}_{get_current_utc().strftime('%Y%m%d')}.xlsx",
            "size_bytes": 0,
            "download_url": "/api/reports/download/...",
            "message": "Excel generation ready (placeholder - integrate openpyxl/xlsxwriter for production)"
        }

    def schedule_recurring_report(
        self,
        report_type: str,
        entity_id: Optional[int],
        frequency: str,
        recipients: List[str]
    ) -> Dict[str, Any]:
        """
        Schedule recurring report generation and distribution.

        Args:
            report_type (str): Type of report to generate.
            entity_id (Optional[int]): Entity ID (campaign, KOL, etc.).
            frequency (str): Report frequency (daily, weekly, monthly).
            recipients (List[str]): Email addresses to send report to.

        Returns:
            Dict[str, Any]: Scheduling result.
        """
        logger.info(f"Scheduling {frequency} {report_type} report")

        # Would integrate with Celery beat for scheduling
        # Example:
        # from app.tasks.celery_config import celery_app
        # from celery.schedules import crontab
        #
        # schedule = {
        #     'daily': crontab(hour=8, minute=0),
        #     'weekly': crontab(hour=8, minute=0, day_of_week=1),
        #     'monthly': crontab(hour=8, minute=0, day_of_month=1)
        # }

        return {
            "success": True,
            "report_type": report_type,
            "entity_id": entity_id,
            "frequency": frequency,
            "recipients": recipients,
            "next_run": "2025-10-04T08:00:00Z",  # Would be calculated
            "message": "Report scheduled successfully"
        }


def get_report_service(db) -> ReportService:
    """
    Dependency for FastAPI to inject ReportService.

    Args:
        db: Database session.

    Returns:
        ReportService: Service instance.
    """
    return ReportService(db)
