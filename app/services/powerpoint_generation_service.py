"""
PowerPoint Generation Service for creating PowerPoint reports from templates.
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pptx import Presentation
from pptx.dml.color import RGBColor
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_template import ReportTemplate
from app.services.data_population_service import DataPopulationService
from app.services.chart_data_service import ChartDataService
from app.utils.powerpoint_utils import (
    PowerPointLayoutManager,
    PowerPointStyler,
    PowerPointChartGenerator,
    PowerPointTableGenerator,
    PowerPointImageHandler
)


class PowerPointGenerationService:
    """Service for generating PowerPoint reports from templates."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.data_service = DataPopulationService(session)
        self.chart_service = ChartDataService(session)
    
    async def generate_powerpoint(
        self, 
        campaign_id: int, 
        template: ReportTemplate
    ) -> str:
        """
        Generate PowerPoint report from template.
        
        Args:
            campaign_id: Campaign ID
            template: ReportTemplate instance
            
        Returns:
            File path of generated PowerPoint file
        """
        # Create new presentation
        prs = Presentation()
        
        # Get populated template data
        template_data = await self.data_service.populate_template_variables(template, campaign_id)
        
        # Process each slide in the template
        template_structure = template.structure
        slides_config = template_structure.get('slides', [])
        
        for slide_config in slides_config:
            slide = prs.slides.add_slide(prs.slide_layouts[0])  # Use blank layout
            await self._process_slide(slide, slide_config, template_data, campaign_id)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaign_{campaign_id}_report_{timestamp}.pptx"
        
        # Ensure uploads/reports directory exists
        reports_dir = "uploads/reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        file_path = os.path.join(reports_dir, filename)
        
        # Save presentation
        prs.save(file_path)
        
        return file_path
    
    async def _process_slide(
        self, 
        slide, 
        slide_config: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int
    ):
        """Process a single slide based on configuration."""
        layout_type = slide_config.get('layout', 'content')
        slide_title = slide_config.get('title', '')
        elements = slide_config.get('elements', [])
        
        # Set up slide layout
        if layout_type == 'title_slide':
            # Title slide layout
            title_text = self._replace_variables(slide_title, template_data)
            subtitle_text = slide_config.get('subtitle', '')
            if subtitle_text:
                subtitle_text = self._replace_variables(subtitle_text, template_data)
            
            PowerPointLayoutManager.create_title_layout(slide, title_text, subtitle_text)
        
        elif layout_type == 'content':
            # Content slide layout
            title_text = self._replace_variables(slide_title, template_data)
            content_y = PowerPointLayoutManager.create_content_layout(slide, title_text)
        
        # Process slide elements
        for element in elements:
            await self._process_element(slide, element, template_data, campaign_id)
    
    async def _process_element(
        self, 
        slide, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int
    ):
        """Process a single slide element."""
        element_type = element.get('type')
        position = element.get('position', {})
        
        x = position.get('x', 1)
        y = position.get('y', 2)
        width = position.get('width', 8)
        height = position.get('height', 1)
        
        if element_type == 'text':
            await self._add_text_element(slide, element, template_data, x, y, width, height)
        
        elif element_type == 'chart':
            await self._add_chart_element(slide, element, template_data, campaign_id, x, y, width, height)
        
        elif element_type == 'table':
            await self._add_table_element(slide, element, template_data, campaign_id, x, y, width, height)
        
        elif element_type == 'image':
            await self._add_image_element(slide, element, template_data, x, y, width, height)
    
    async def _add_text_element(
        self, 
        slide, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        x: float, 
        y: float, 
        width: float, 
        height: float
    ):
        """Add a text element to the slide."""
        content = element.get('content', '')
        style = element.get('style', {})
        
        # Replace variables in content
        text_content = self._replace_variables(content, template_data)
        
        # Create text box
        abs_x, abs_y, abs_width, abs_height = PowerPointLayoutManager.get_position(x, y, width, height)
        
        text_shape = slide.shapes.add_textbox(abs_x, abs_y, abs_width, abs_height)
        text_frame = text_shape.text_frame
        
        # Apply styling
        style_name = self._get_style_name(style)
        PowerPointStyler.apply_text_style(text_frame, style_name, text_content)
        
        # Apply custom styling if provided
        if style:
            paragraph = text_frame.paragraphs[0]
            font = paragraph.font
            
            if 'font' in style:
                font.name = style['font']
            
            if 'size' in style:
                font.size = style['size']
            
            if 'bold' in style:
                font.bold = style['bold']
            
            if 'color' in style:
                # Parse color (assuming hex format like #1f4e79)
                color_hex = style['color'].lstrip('#')
                if len(color_hex) == 6:
                    r = int(color_hex[0:2], 16)
                    g = int(color_hex[2:4], 16)
                    b = int(color_hex[4:6], 16)
                    font.color.rgb = RGBColor(r, g, b)
    
    async def _add_chart_element(
        self, 
        slide, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int,
        x: float, 
        y: float, 
        width: float, 
        height: float
    ):
        """Add a chart element to the slide."""
        chart_type = element.get('chart_type', 'bar')
        data_source = element.get('data_source', 'kol_performance')
        title = element.get('title', '')
        
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
        
        # Add chart to slide based on type
        if chart_type == 'bar' or chart_type == 'column':
            PowerPointChartGenerator.add_bar_chart(slide, chart_data, x, y, width, height)
        
        elif chart_type == 'stacked_bar' or chart_type == 'stacked_column':
            PowerPointChartGenerator.add_stacked_bar_chart(slide, chart_data, x, y, width, height)
        
        elif chart_type == 'line':
            PowerPointChartGenerator.add_line_chart(slide, chart_data, x, y, width, height)
        
        elif chart_type == 'area':
            PowerPointChartGenerator.add_area_chart(slide, chart_data, x, y, width, height)
        
        elif chart_type == 'pie':
            PowerPointChartGenerator.add_pie_chart(slide, chart_data, x, y, width, height)
        
        elif chart_type == 'donut':
            PowerPointChartGenerator.add_donut_chart(slide, chart_data, x, y, width, height)
        
        else:
            # Default to bar chart for unknown types
            PowerPointChartGenerator.add_bar_chart(slide, chart_data, x, y, width, height)
    
    async def _add_table_element(
        self, 
        slide, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        campaign_id: int,
        x: float, 
        y: float, 
        width: float, 
        height: float
    ):
        """Add a table element to the slide."""
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
                ]
            }
        else:
            # Default empty table
            table_data = {
                'columns': columns or ['Metric', 'Value'],
                'data': [['No Data', 'N/A']]
            }
        
        # Add table to slide
        PowerPointTableGenerator.add_table(slide, table_data, x, y, width, height)
    
    async def _add_image_element(
        self, 
        slide, 
        element: Dict[str, Any], 
        template_data: Dict[str, Any],
        x: float, 
        y: float, 
        width: float, 
        height: float
    ):
        """Add an image element to the slide."""
        source = element.get('source', '')
        fallback = element.get('fallback', '')
        
        # Replace variables in source path
        image_path = self._replace_variables(source, template_data)
        
        # Handle different image sources
        if image_path.startswith('{{') and image_path.endswith('}}'):
            # Variable not replaced, use fallback
            image_path = fallback
        
        # Convert relative paths to absolute
        if not os.path.isabs(image_path):
            image_path = os.path.join('uploads', 'images', image_path)
        
        fallback_path = None
        if fallback and not os.path.isabs(fallback):
            fallback_path = os.path.join('uploads', 'images', fallback)
        
        # Add image to slide
        PowerPointImageHandler.add_image(slide, image_path, x, y, width, height, fallback_path)
    
    def _replace_variables(self, text: str, template_data: Dict[str, Any]) -> str:
        """Replace template variables in text."""
        if not text or not template_data:
            return text
        
        result = text
        for variable, value in template_data.items():
            result = result.replace(variable, str(value))
        
        return result
    
    def _get_style_name(self, style: Dict[str, Any]) -> str:
        """Get style name from style configuration."""
        size = style.get('size', 14)
        bold = style.get('bold', False)
        
        # Map size and bold to style names
        if size >= 40:
            return 'title'
        elif size >= 30:
            return 'heading1'
        elif size >= 20:
            return 'heading2'
        elif size >= 16:
            return 'heading3'
        elif bold:
            return 'heading3'
        else:
            return 'body'


# Dependency function for FastAPI
async def get_powerpoint_generation_service(session: AsyncSession) -> PowerPointGenerationService:
    """Get PowerPointGenerationService instance."""
    return PowerPointGenerationService(session)