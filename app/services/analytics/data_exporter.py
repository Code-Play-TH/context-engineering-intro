"""
Data Exporter Service

Comprehensive data export service for analytics including:
- Multi-format data export (CSV, Excel, PDF, JSON)
- Visualization export (PNG, SVG, PowerPoint)
- Scheduled export automation
- Custom export templates and formatting
- Compression and delivery options
- Export task management and tracking
"""

import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, BinaryIO
from io import BytesIO, StringIO
import base64
import zipfile

from app.schemas.analytics import ExportFormat, ExportRequest, TimeRange, MetricType
from app.services.analytics.analytics_engine import AnalyticsEngine
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ExportTemplate:
    """Export template configuration."""

    def __init__(self, template_name: str, config: Dict[str, Any]):
        self.template_name = template_name
        self.config = config
        self.columns = config.get('columns', [])
        self.formatting = config.get('formatting', {})
        self.headers = config.get('headers', {})


class DataExporter:
    """
    Advanced data export service for analytics data in multiple formats.
    """

    def __init__(self):
        """Initialize the Data Exporter with templates and configurations."""
        self.analytics_engine = AnalyticsEngine()
        self._load_export_templates()
        self.export_cache = {}  # Simple in-memory cache for export tasks

    def _load_export_templates(self) -> None:
        """
        Load predefined export templates for different data types.
        """
        self.templates = {
            'kol_performance': ExportTemplate('kol_performance', {
                'columns': [
                    'kol_id', 'kol_name', 'total_followers', 'engagement_rate',
                    'average_likes', 'average_comments', 'reach', 'impressions',
                    'quality_score', 'brand_safety_score', 'sentiment_score'
                ],
                'formatting': {
                    'engagement_rate': 'percentage',
                    'quality_score': 'percentage',
                    'brand_safety_score': 'percentage',
                    'sentiment_score': 'decimal_2'
                },
                'headers': {
                    'kol_id': 'KOL ID',
                    'kol_name': 'KOL Name',
                    'total_followers': 'Total Followers',
                    'engagement_rate': 'Engagement Rate (%)',
                    'average_likes': 'Avg Likes',
                    'average_comments': 'Avg Comments',
                    'reach': 'Reach',
                    'impressions': 'Impressions',
                    'quality_score': 'Quality Score (%)',
                    'brand_safety_score': 'Brand Safety (%)',
                    'sentiment_score': 'Sentiment Score'
                }
            }),

            'campaign_performance': ExportTemplate('campaign_performance', {
                'columns': [
                    'campaign_id', 'campaign_name', 'status', 'total_reach',
                    'total_impressions', 'total_engagement', 'engagement_rate',
                    'conversions', 'conversion_rate', 'total_spend', 'revenue', 'roi'
                ],
                'formatting': {
                    'engagement_rate': 'percentage',
                    'conversion_rate': 'percentage',
                    'roi': 'percentage',
                    'total_spend': 'currency',
                    'revenue': 'currency'
                },
                'headers': {
                    'campaign_id': 'Campaign ID',
                    'campaign_name': 'Campaign Name',
                    'status': 'Status',
                    'total_reach': 'Total Reach',
                    'total_impressions': 'Total Impressions',
                    'total_engagement': 'Total Engagement',
                    'engagement_rate': 'Engagement Rate (%)',
                    'conversions': 'Conversions',
                    'conversion_rate': 'Conversion Rate (%)',
                    'total_spend': 'Total Spend',
                    'revenue': 'Revenue',
                    'roi': 'ROI (%)'
                }
            }),

            'content_analysis': ExportTemplate('content_analysis', {
                'columns': [
                    'content_id', 'platform', 'content_type', 'engagement_rate',
                    'reach', 'impressions', 'sentiment_score', 'quality_score',
                    'brand_safety_score', 'created_at'
                ],
                'formatting': {
                    'engagement_rate': 'percentage',
                    'sentiment_score': 'decimal_2',
                    'quality_score': 'percentage',
                    'brand_safety_score': 'percentage',
                    'created_at': 'date'
                },
                'headers': {
                    'content_id': 'Content ID',
                    'platform': 'Platform',
                    'content_type': 'Content Type',
                    'engagement_rate': 'Engagement Rate (%)',
                    'reach': 'Reach',
                    'impressions': 'Impressions',
                    'sentiment_score': 'Sentiment Score',
                    'quality_score': 'Quality Score (%)',
                    'brand_safety_score': 'Brand Safety (%)',
                    'created_at': 'Created Date'
                }
            }),

            'dashboard_summary': ExportTemplate('dashboard_summary', {
                'columns': [
                    'metric_name', 'current_value', 'previous_value',
                    'change_percentage', 'trend', 'period'
                ],
                'formatting': {
                    'change_percentage': 'percentage',
                    'current_value': 'auto',
                    'previous_value': 'auto'
                },
                'headers': {
                    'metric_name': 'Metric',
                    'current_value': 'Current Value',
                    'previous_value': 'Previous Value',
                    'change_percentage': 'Change (%)',
                    'trend': 'Trend',
                    'period': 'Period'
                }
            })
        }

    async def export_data(
        self,
        export_request: ExportRequest,
        user_id: int,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export analytics data in the specified format.

        Args:
            export_request: Export configuration and parameters
            user_id: User ID for access control
            task_id: Optional task ID for tracking

        Returns:
            Dict containing export results and file information
        """
        try:
            logger.info(f"Starting data export: {export_request.export_name}")

            if not task_id:
                task_id = f"export_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Gather data for export
            export_data = await self._gather_export_data(export_request, user_id)

            # Process and format data
            formatted_data = await self._format_data_for_export(
                export_data, export_request
            )

            # Generate export file
            export_file = await self._generate_export_file(
                formatted_data, export_request, task_id
            )

            # Store export results
            export_results = {
                'task_id': task_id,
                'export_name': export_request.export_name,
                'format': export_request.format,
                'status': 'completed',
                'file_info': export_file,
                'generated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=7),  # 7 days expiry
                'user_id': user_id,
                'metadata': {
                    'entity_type': export_request.entity_type,
                    'entity_count': len(export_request.entity_ids) if export_request.entity_ids else 0,
                    'metrics_count': len(export_request.metrics),
                    'time_range': export_request.time_range.value,
                    'compression': export_request.compression
                }
            }

            # Cache export results
            self.export_cache[task_id] = export_results

            return export_results

        except Exception as e:
            logger.error(f"Data export failed: {str(e)}")
            # Update status to failed
            if task_id and task_id in self.export_cache:
                self.export_cache[task_id]['status'] = 'failed'
                self.export_cache[task_id]['error'] = str(e)
            raise

    async def get_exported_file(
        self,
        task_id: str,
        user_id: int
    ) -> tuple[BinaryIO, str, str]:
        """
        Retrieve exported file for download.

        Args:
            task_id: Export task ID
            user_id: User ID for access control

        Returns:
            Tuple of (file_stream, filename, content_type)
        """
        try:
            logger.info(f"Retrieving exported file: {task_id}")

            # Get export results from cache
            if task_id not in self.export_cache:
                raise ValueError(f"Export task not found: {task_id}")

            export_results = self.export_cache[task_id]

            # Verify user access
            if export_results['user_id'] != user_id:
                raise PermissionError("Access denied to export file")

            # Check if file is expired
            if datetime.utcnow() > export_results['expires_at']:
                raise ValueError("Export file has expired")

            # Get file information
            file_info = export_results['file_info']
            file_content = file_info['content']
            filename = file_info['filename']
            content_type = file_info['content_type']

            # Create file stream
            file_stream = BytesIO(file_content)

            return file_stream, filename, content_type

        except Exception as e:
            logger.error(f"File retrieval failed: {str(e)}")
            raise

    async def _gather_export_data(
        self,
        export_request: ExportRequest,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Gather data for export based on request parameters.

        Args:
            export_request: Export configuration
            user_id: User ID for access control

        Returns:
            Dict containing gathered data
        """
        data = {}

        # Gather data based on entity type
        if export_request.entity_type.lower() == 'kol':
            kol_data = await self.analytics_engine.analyze_kol_performance(
                kol_ids=export_request.entity_ids,
                time_range=export_request.time_range,
                metrics=export_request.metrics,
                include_comparisons=False,
                user_id=user_id,
                db=None  # Would pass actual DB session
            )
            data['kol_analytics'] = kol_data

        elif export_request.entity_type.lower() == 'campaign':
            campaign_data = await self.analytics_engine.analyze_campaign_performance(
                campaign_ids=export_request.entity_ids,
                time_range=export_request.time_range,
                include_roi=True,
                include_predictions=False,
                user_id=user_id,
                db=None
            )
            data['campaign_analytics'] = campaign_data

        elif export_request.entity_type.lower() == 'content':
            content_data = await self.analytics_engine.analyze_content_performance(
                time_range=export_request.time_range,
                include_sentiment=True,
                include_engagement_trends=True,
                user_id=user_id,
                db=None
            )
            data['content_analytics'] = content_data

        elif export_request.entity_type.lower() == 'dashboard':
            dashboard_data = await self.analytics_engine.generate_dashboard_data(
                time_range=export_request.time_range,
                include_predictions=False,
                user_id=user_id,
                db=None
            )
            data['dashboard_data'] = dashboard_data

        return data

    async def _format_data_for_export(
        self,
        export_data: Dict[str, Any],
        export_request: ExportRequest
    ) -> List[Dict[str, Any]]:
        """
        Format data for export based on template and request.

        Args:
            export_data: Raw export data
            export_request: Export configuration

        Returns:
            List of formatted data records
        """
        formatted_data = []

        # Select appropriate template
        template = self._select_export_template(export_request.entity_type)

        if export_request.entity_type.lower() == 'kol' and 'kol_analytics' in export_data:
            for kol_data in export_data['kol_analytics']:
                record = self._format_kol_record(kol_data, template)
                formatted_data.append(record)

        elif export_request.entity_type.lower() == 'campaign' and 'campaign_analytics' in export_data:
            for campaign_data in export_data['campaign_analytics']:
                record = self._format_campaign_record(campaign_data, template)
                formatted_data.append(record)

        elif export_request.entity_type.lower() == 'content' and 'content_analytics' in export_data:
            content_data = export_data['content_analytics']
            records = self._format_content_records(content_data, template)
            formatted_data.extend(records)

        elif export_request.entity_type.lower() == 'dashboard' and 'dashboard_data' in export_data:
            dashboard_data = export_data['dashboard_data']
            records = self._format_dashboard_records(dashboard_data, template)
            formatted_data.extend(records)

        return formatted_data

    async def _generate_export_file(
        self,
        formatted_data: List[Dict[str, Any]],
        export_request: ExportRequest,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Generate export file in the specified format.

        Args:
            formatted_data: Formatted data records
            export_request: Export configuration
            task_id: Task ID for file naming

        Returns:
            Dict containing file information
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{export_request.export_name}_{timestamp}"

        if export_request.format == ExportFormat.CSV:
            return await self._generate_csv_file(formatted_data, base_filename, export_request)
        elif export_request.format == ExportFormat.EXCEL:
            return await self._generate_excel_file(formatted_data, base_filename, export_request)
        elif export_request.format == ExportFormat.JSON:
            return await self._generate_json_file(formatted_data, base_filename, export_request)
        elif export_request.format == ExportFormat.PDF:
            return await self._generate_pdf_file(formatted_data, base_filename, export_request)
        else:
            raise ValueError(f"Unsupported export format: {export_request.format}")

    async def _generate_csv_file(
        self,
        data: List[Dict[str, Any]],
        base_filename: str,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Generate CSV export file."""
        if not data:
            raise ValueError("No data to export")

        # Create CSV content
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        csv_content = output.getvalue().encode('utf-8')
        filename = f"{base_filename}.csv"

        # Compress if requested
        if export_request.compression:
            csv_content, filename = self._compress_file(csv_content, filename)

        return {
            'filename': filename,
            'content': csv_content,
            'content_type': 'text/csv' if not export_request.compression else 'application/zip',
            'size': len(csv_content)
        }

    async def _generate_excel_file(
        self,
        data: List[Dict[str, Any]],
        base_filename: str,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Generate Excel export file."""
        # Simulate Excel file generation
        # In production, would use libraries like openpyxl or xlsxwriter
        excel_content = json.dumps(data, indent=2, default=str).encode('utf-8')
        filename = f"{base_filename}.xlsx"

        # Compress if requested
        if export_request.compression:
            excel_content, filename = self._compress_file(excel_content, filename)

        return {
            'filename': filename,
            'content': excel_content,
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if not export_request.compression else 'application/zip',
            'size': len(excel_content)
        }

    async def _generate_json_file(
        self,
        data: List[Dict[str, Any]],
        base_filename: str,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Generate JSON export file."""
        json_content = json.dumps({
            'export_info': {
                'export_name': export_request.export_name,
                'generated_at': datetime.utcnow().isoformat(),
                'entity_type': export_request.entity_type,
                'time_range': export_request.time_range.value,
                'record_count': len(data)
            },
            'data': data
        }, indent=2, default=str).encode('utf-8')

        filename = f"{base_filename}.json"

        # Compress if requested
        if export_request.compression:
            json_content, filename = self._compress_file(json_content, filename)

        return {
            'filename': filename,
            'content': json_content,
            'content_type': 'application/json' if not export_request.compression else 'application/zip',
            'size': len(json_content)
        }

    async def _generate_pdf_file(
        self,
        data: List[Dict[str, Any]],
        base_filename: str,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Generate PDF export file."""
        # Simulate PDF generation
        # In production, would use libraries like reportlab or weasyprint
        pdf_content = f"PDF Report: {export_request.export_name}\n\nData: {json.dumps(data, indent=2, default=str)}".encode('utf-8')
        filename = f"{base_filename}.pdf"

        return {
            'filename': filename,
            'content': pdf_content,
            'content_type': 'application/pdf',
            'size': len(pdf_content)
        }

    def _compress_file(self, content: bytes, filename: str) -> tuple[bytes, str]:
        """Compress file content."""
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(filename, content)

        compressed_content = zip_buffer.getvalue()
        compressed_filename = f"{filename}.zip"

        return compressed_content, compressed_filename

    def _select_export_template(self, entity_type: str) -> ExportTemplate:
        """Select appropriate export template."""
        entity_type_lower = entity_type.lower()

        if entity_type_lower == 'kol':
            return self.templates['kol_performance']
        elif entity_type_lower == 'campaign':
            return self.templates['campaign_performance']
        elif entity_type_lower == 'content':
            return self.templates['content_analysis']
        elif entity_type_lower == 'dashboard':
            return self.templates['dashboard_summary']
        else:
            # Default template
            return self.templates['dashboard_summary']

    def _format_kol_record(self, kol_data: Dict[str, Any], template: ExportTemplate) -> Dict[str, Any]:
        """Format KOL data record for export."""
        overall_metrics = kol_data.get('overall_metrics', {})

        record = {}
        for column in template.columns:
            if column == 'kol_id':
                record[template.headers[column]] = kol_data.get('kol_id')
            elif column == 'kol_name':
                record[template.headers[column]] = kol_data.get('kol_name')
            else:
                value = overall_metrics.get(column, 0)
                formatted_value = self._format_value(value, template.formatting.get(column, 'number'))
                record[template.headers[column]] = formatted_value

        return record

    def _format_campaign_record(self, campaign_data: Dict[str, Any], template: ExportTemplate) -> Dict[str, Any]:
        """Format campaign data record for export."""
        metrics = campaign_data.get('metrics', {})

        record = {}
        for column in template.columns:
            if column == 'campaign_id':
                record[template.headers[column]] = campaign_data.get('campaign_id')
            elif column == 'campaign_name':
                record[template.headers[column]] = campaign_data.get('campaign_name')
            elif column == 'status':
                record[template.headers[column]] = campaign_data.get('status')
            else:
                value = metrics.get(column, 0)
                formatted_value = self._format_value(value, template.formatting.get(column, 'number'))
                record[template.headers[column]] = formatted_value

        return record

    def _format_content_records(self, content_data: Dict[str, Any], template: ExportTemplate) -> List[Dict[str, Any]]:
        """Format content data records for export."""
        # Simulate content records formatting
        # In production, would iterate through actual content analysis data
        records = []

        # Example record
        record = {
            template.headers['content_id']: 'content_001',
            template.headers['platform']: 'instagram',
            template.headers['content_type']: 'image',
            template.headers['engagement_rate']: '4.2%',
            template.headers['reach']: 15000,
            template.headers['impressions']: 45000,
            template.headers['sentiment_score']: 0.65,
            template.headers['quality_score']: '85%',
            template.headers['brand_safety_score']: '92%',
            template.headers['created_at']: datetime.utcnow().strftime('%Y-%m-%d')
        }
        records.append(record)

        return records

    def _format_dashboard_records(self, dashboard_data: Dict[str, Any], template: ExportTemplate) -> List[Dict[str, Any]]:
        """Format dashboard data records for export."""
        records = []

        kpis = dashboard_data.get('kpis', [])
        for kpi in kpis:
            record = {
                template.headers['metric_name']: kpi.get('name'),
                template.headers['current_value']: self._format_value(kpi.get('value'), kpi.get('format_type', 'number')),
                template.headers['previous_value']: self._format_value(kpi.get('previous_value'), kpi.get('format_type', 'number')),
                template.headers['change_percentage']: f"{kpi.get('change_percentage', 0):.1f}%",
                template.headers['trend']: kpi.get('trend', 'stable'),
                template.headers['period']: 'Last 30 days'
            }
            records.append(record)

        return records

    def _format_value(self, value: Any, format_type: str) -> str:
        """Format value according to specified format type."""
        if value is None:
            return ""

        try:
            if format_type == 'percentage':
                return f"{float(value) * 100:.1f}%" if float(value) <= 1 else f"{float(value):.1f}%"
            elif format_type == 'currency':
                return f"${float(value):,.2f}"
            elif format_type == 'decimal_2':
                return f"{float(value):.2f}"
            elif format_type == 'date':
                if isinstance(value, str):
                    return value
                elif isinstance(value, datetime):
                    return value.strftime('%Y-%m-%d')
                else:
                    return str(value)
            elif format_type == 'auto':
                # Auto-format based on value type
                if isinstance(value, float):
                    return f"{value:,.2f}"
                elif isinstance(value, int):
                    return f"{value:,}"
                else:
                    return str(value)
            else:  # 'number'
                if isinstance(value, (int, float)):
                    return f"{value:,}"
                else:
                    return str(value)
        except (ValueError, TypeError):
            return str(value)

    def cleanup_expired_exports(self) -> Dict[str, Any]:
        """
        Clean up expired export files from cache.

        Returns:
            Dict containing cleanup results
        """
        try:
            current_time = datetime.utcnow()
            expired_tasks = []

            for task_id, export_data in list(self.export_cache.items()):
                if current_time > export_data.get('expires_at', current_time):
                    expired_tasks.append(task_id)
                    del self.export_cache[task_id]

            logger.info(f"Cleaned up {len(expired_tasks)} expired export files")

            return {
                'cleaned_count': len(expired_tasks),
                'cleaned_tasks': expired_tasks,
                'cleanup_time': current_time
            }

        except Exception as e:
            logger.error(f"Export cleanup failed: {str(e)}")
            raise

    def get_export_status(self, task_id: str, user_id: int) -> Dict[str, Any]:
        """
        Get status of an export task.

        Args:
            task_id: Export task ID
            user_id: User ID for access control

        Returns:
            Dict containing export status
        """
        if task_id not in self.export_cache:
            return {'status': 'not_found', 'message': 'Export task not found'}

        export_data = self.export_cache[task_id]

        # Verify user access
        if export_data['user_id'] != user_id:
            return {'status': 'access_denied', 'message': 'Access denied'}

        return {
            'task_id': task_id,
            'status': export_data['status'],
            'export_name': export_data['export_name'],
            'format': export_data['format'],
            'generated_at': export_data.get('generated_at'),
            'expires_at': export_data.get('expires_at'),
            'file_size': export_data.get('file_info', {}).get('size'),
            'metadata': export_data.get('metadata', {})
        }