"""
PDF Generation Service for creating PDF reports from templates.
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

from app.models.report_template import ReportTemplate
from app.services.data_population_service import DataPopulationService
from app.services.chart_data_service import ChartDataService
from app.utils.pdf_utils import (
    PDFLayoutManager,
    PDFStyler,
    PDFChartGenerator,
    PDFTableGenerator,
    PDFImageHandler
)


class PDFGenerationService:
    """Service for generating PDF reports from templates."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.data_service = DataPopulationService(session)
        self.chart_service = ChartDataService(session)
    
    async def generate_pdf(
        self, 
        campaign_id: int, 
        template: ReportTemplate
    ) -> str:
        """
        Generate PDF report from template.
        
        Args:
            campaign_id: Campaign ID
            template: ReportTemplate instance
            
        Returns:
            File path of generated PDF file
        """
        # Get populated template data
        template_data = await self.data_service.populate_template_variables(template, campaign_id)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaign_{campaign_id}_report_{timestamp}.pdf"
        
        # Ensure uploads/reports directory exists
        reports_dir = "uploads/reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        file_path = os.path.join(reports_dir, filename)
        
        # Create PDF document
        campaign_name = template_data.get('{{campaign_name}}', 'Campaign Report')
        doc = PDFLayoutManager.create_document(file_path, campaign_name)
        
        # Build story (content)
        story = []
        
        # Process template structure
        template_structure = template.structure
        pages_config = template_structure.get('pages', [])
        
        for page_idx, page_config in enumerate(pages_config):
            await self._process_page(story, page_config, template_data, campaign_id)
            
            # Add page break between pages (except for the last page)
            if page_idx < len(pages_config) - 1:
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        
        return file_path
    
    async def _process_page(
        self, 
        story: List, 
        page_config: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int
    ):
        """Process a single page based on configuration."""
        page_type = page_config.get('type', 'content')
        page_title = page_config.get('title', '')
        elements = page_config.get('elements', [])
        
        # Handle different page types
        if page_type == 'cover':
            await self._process_cover_page(story, page_config, template_data)
        elif page_type == 'content':
            await self._process_content_page(story, page_config, template_data, campaign_id)
        else:
            # Default content page
            await self._process_content_page(story, page_config, template_data, campaign_id)
    
    async def _process_cover_page(
        self, 
        story: List, 
        page_config: Dict[str, Any], 
        template_data: Dict[str, Any]
    ):
        """Process a cover page."""
        elements = page_config.get('elements', [])
        
        # Process cover page elements
        for element in elements:
            await self._process_element(story, element, template_data, None)
    
    async def _process_content_page(
        self, 
        story: List, 
        page_config: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int
    ):
        """Process a content page."""
        page_title = page_config.get('title', '')
        elements = page_config.get('elements', [])
        
        # Add page title if provided
        if page_title:
            styles = PDFStyler.get_styles()
            title_text = self._replace_variables(page_title, template_data)
            story.append(Paragraph(title_text, styles['CustomHeading1']))
            story.append(Spacer(1, 12))
        
        # Process page elements
        for element in elements:
            await self._process_element(story, element, template_data, campaign_id)
    
    async def _process_element(
        self, 
        story: List, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: Optional[int]
    ):
        """Process a single page element."""
        element_type = element.get('type')
        
        if element_type == 'text':
            await self._add_text_element(story, element, template_data)
        
        elif element_type == 'chart':
            if campaign_id:
                await self._add_chart_element(story, element, template_data, campaign_id)
        
        elif element_type == 'table':
            if campaign_id:
                await self._add_table_element(story, element, template_data, campaign_id)
        
        elif element_type == 'image':
            await self._add_image_element(story, element, template_data)
        
        elif element_type == 'spacer':
            await self._add_spacer_element(story, element)
    
    async def _add_text_element(
        self, 
        story: List, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any]
    ):
        """Add a text element to the story."""
        content = element.get('content', '')
        style_name = element.get('style', 'normal')
        font_size = element.get('font_size', None)
        color = element.get('color', None)
        
        # Replace variables in content
        text_content = self._replace_variables(content, template_data)
        
        # Get styles
        styles = PDFStyler.get_styles()
        
        # Map style names
        style_mapping = {
            'title': 'CustomTitle',
            'subtitle': 'CustomSubtitle',
            'heading1': 'CustomHeading1',
            'heading2': 'CustomHeading2',
            'heading3': 'CustomHeading3',
            'normal': 'CustomBody',
            'caption': 'CustomCaption'
        }
        
        pdf_style_name = style_mapping.get(style_name, 'CustomBody')
        paragraph_style = styles[pdf_style_name]
        
        # Create custom style if font_size or color specified
        if font_size or color:
            from reportlab.lib.styles import ParagraphStyle
            custom_style = ParagraphStyle(
                name='CustomElement',
                parent=paragraph_style,
                fontSize=font_size or paragraph_style.fontSize,
                textColor=color or paragraph_style.textColor
            )
            paragraph_style = custom_style
        
        # Add paragraph
        story.append(Paragraph(text_content, paragraph_style))
    
    async def _add_chart_element(
        self, 
        story: List, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int
    ):
        """Add a chart element to the story."""
        chart_type = element.get('chart_type', 'bar')
        data_source = element.get('data_source', 'kol_performance')
        title = element.get('title', '')
        width = element.get('width', 6)
        height = element.get('height', 4)
        
        # Replace variables in title
        chart_title = self._replace_variables(title, template_data)
        
        # Create chart configuration
        chart_config = {
            'chart_type': chart_type,
            'data_source': data_source,
            'title': chart_title,
            'x_axis': element.get('x_axis', ''),
            'y_axis': element.get('y_axis', ''),
            'series': element.get('series', []),
            'colors': element.get('colors', [])
        }
        
        # Generate chart data
        chart_data = await self.chart_service.generate_chart_data(chart_config, campaign_id)
        
        # Create chart image based on type
        if chart_type == 'bar' or chart_type == 'column':
            chart_image = PDFChartGenerator.create_bar_chart(chart_data, width, height)
        elif chart_type == 'horizontal_bar':
            chart_image = PDFChartGenerator.create_horizontal_bar_chart(chart_data, width, height)
        elif chart_type == 'stacked_bar' or chart_type == 'stacked_column':
            chart_image = PDFChartGenerator.create_stacked_bar_chart(chart_data, width, height)
        elif chart_type == 'line':
            chart_image = PDFChartGenerator.create_line_chart(chart_data, width, height)
        elif chart_type == 'area':
            chart_image = PDFChartGenerator.create_area_chart(chart_data, width, height)
        elif chart_type == 'pie':
            chart_image = PDFChartGenerator.create_pie_chart(chart_data, width, height)
        elif chart_type == 'donut':
            chart_image = PDFChartGenerator.create_donut_chart(chart_data, width, height)
        else:
            # Default to bar chart
            chart_image = PDFChartGenerator.create_bar_chart(chart_data, width, height)
        
        # Add chart to story
        story.append(chart_image)
        story.append(Spacer(1, 12))
    
    async def _add_table_element(
        self, 
        story: List, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int
    ):
        """Add a table element to the story."""
        data_source = element.get('data_source', 'campaign_summary')
        columns = element.get('columns', [])
        
        # Generate table data based on data source
        if data_source == 'campaign_summary':
            table_data = await self.chart_service.generate_chart_data(
                {'data_source': 'campaign_summary'}, 
                campaign_id
            )
        elif data_source == 'campaign_kpis':
            # TODO: Implement KPI table data generation
            table_data = {
                'columns': ['KPI', 'Target', 'Actual', 'Achievement %'],
                'data': [
                    ['Reach', '2,000,000', '2,500,000', '125%'],
                    ['Engagement', '100,000', '125,000', '125%'],
                    ['Posts', '40', '45', '113%']
                ],
                'style': element.get('style', {})
            }
        elif data_source == 'kol_detailed_metrics':
            # TODO: Implement detailed KOL metrics table
            table_data = {
                'columns': ['KOL Name', 'Followers', 'Posts', 'Avg Engagement', 'Total Reach'],
                'data': [
                    ['KOL #1', '500,000', '12', '3.2%', '500,000'],
                    ['KOL #2', '750,000', '8', '2.8%', '750,000'],
                    ['KOL #3', '300,000', '15', '4.1%', '300,000']
                ],
                'style': element.get('style', {})
            }
        else:
            # Default empty table
            table_data = {
                'columns': columns or ['Metric', 'Value'],
                'data': [['No Data', 'N/A']],
                'style': element.get('style', {})
            }
        
        # Create table
        table = PDFTableGenerator.create_table(table_data, PDFLayoutManager.CONTENT_WIDTH)
        
        if table:
            story.append(table)
            story.append(Spacer(1, 12))
    
    async def _add_image_element(
        self, 
        story: List, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any]
    ):
        """Add an image element to the story."""
        source = element.get('source', '')
        fallback = element.get('fallback', 'Image not available')
        width = element.get('width', 2)
        height = element.get('height', 1)
        
        # Replace variables in source path
        image_path = self._replace_variables(source, template_data)
        
        # Handle different image sources
        if image_path.startswith('{{') and image_path.endswith('}}'):
            # Variable not replaced, create placeholder
            image_element = PDFImageHandler._create_image_placeholder(width, height, fallback)
        else:
            # Convert relative paths to absolute
            if not os.path.isabs(image_path):
                image_path = os.path.join('uploads', 'images', image_path)
            
            image_element = PDFImageHandler.create_image(image_path, width, height, fallback)
        
        # Add image to story
        story.append(image_element)
        story.append(Spacer(1, 12))
    
    async def _add_spacer_element(
        self, 
        story: List, 
        element: Dict[str, Any]
    ):
        """Add a spacer element to the story."""
        height = element.get('height', 12)
        story.append(Spacer(1, height))
    
    def _replace_variables(self, text: str, template_data: Dict[str, Any]) -> str:
        """Replace template variables in text."""
        if not text or not template_data:
            return text
        
        result = text
        for variable, value in template_data.items():
            result = result.replace(variable, str(value))
        
        return result


# Dependency function for FastAPI
async def get_pdf_generation_service(session: AsyncSession) -> PDFGenerationService:
    """Get PDFGenerationService instance."""
    return PDFGenerationService(session)