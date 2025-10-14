"""
PDF utilities for report generation using ReportLab.
"""
import os
import io
from typing import Dict, Any, List, Optional, Tuple
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, HexColor, black, white, grey
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


class PDFStyler:
    """Handles PDF styling and formatting."""
    
    # Color scheme
    COLORS = {
        'primary': HexColor('#1f4e79'),
        'secondary': HexColor('#70ad47'),
        'accent': HexColor('#ffc000'),
        'danger': HexColor('#c55a5a'),
        'text': HexColor('#444444'),
        'light_gray': HexColor('#f2f2f2'),
        'dark_gray': HexColor('#808080'),
        'white': white,
        'black': black
    }
    
    @classmethod
    def get_styles(cls):
        """Get custom PDF styles."""
        styles = getSampleStyleSheet()
        
        # Custom title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=36,
            textColor=cls.COLORS['primary'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Custom subtitle style
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Normal'],
            fontSize=24,
            textColor=cls.COLORS['text'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Custom heading styles
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=cls.COLORS['primary'],
            spaceAfter=18,
            spaceBefore=24,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=cls.COLORS['primary'],
            spaceAfter=12,
            spaceBefore=18,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=cls.COLORS['primary'],
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Custom body text
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            textColor=cls.COLORS['text'],
            spaceAfter=12,
            fontName='Helvetica'
        ))
        
        # Custom caption
        styles.add(ParagraphStyle(
            name='CustomCaption',
            parent=styles['Normal'],
            fontSize=10,
            textColor=cls.COLORS['dark_gray'],
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        return styles
    
    @classmethod
    def get_table_style(cls, header_color=None, alternating_rows=True):
        """Get standard table style."""
        header_color = header_color or cls.COLORS['primary']
        
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), cls.COLORS['white']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), cls.COLORS['white']),
            ('TEXTCOLOR', (0, 1), (-1, -1), cls.COLORS['text']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, cls.COLORS['dark_gray']),
        ]
        
        if alternating_rows:
            table_style.append(('ROWBACKGROUNDS', (0, 1), (-1, -1), [cls.COLORS['white'], cls.COLORS['light_gray']]))
        
        return TableStyle(table_style)


class PDFLayoutManager:
    """Manages PDF page layouts and positioning."""
    
    # Page settings
    PAGE_SIZE = A4
    PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
    
    # Margins
    MARGIN_LEFT = 72  # 1 inch
    MARGIN_RIGHT = 72
    MARGIN_TOP = 72
    MARGIN_BOTTOM = 72
    
    # Content area
    CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    
    @classmethod
    def create_document(cls, file_path: str, title: str = "Report"):
        """Create a PDF document with standard settings."""
        doc = SimpleDocTemplate(
            file_path,
            pagesize=cls.PAGE_SIZE,
            rightMargin=cls.MARGIN_RIGHT,
            leftMargin=cls.MARGIN_LEFT,
            topMargin=cls.MARGIN_TOP,
            bottomMargin=cls.MARGIN_BOTTOM,
            title=title
        )
        return doc
    
    @classmethod
    def add_cover_page(cls, story: List, title: str, subtitle: str = None, date: str = None):
        """Add a cover page to the story."""
        styles = PDFStyler.get_styles()
        
        # Add some space from top
        story.append(Spacer(1, 2 * inch))
        
        # Title
        story.append(Paragraph(title, styles['CustomTitle']))
        
        # Subtitle
        if subtitle:
            story.append(Paragraph(subtitle, styles['CustomSubtitle']))
        
        # Date
        if date:
            story.append(Spacer(1, 1 * inch))
            story.append(Paragraph(f"Generated on {date}", styles['CustomCaption']))
        
        # Page break
        story.append(PageBreak())


class PDFChartGenerator:
    """Generates charts for PDF documents using matplotlib."""
    
    @classmethod
    def create_bar_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create a bar chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets:
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        x_pos = range(len(labels))
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        
        if len(datasets) == 1:
            # Single series
            dataset = datasets[0]
            data = dataset.get('data', [])
            ax.bar(x_pos, data, color=colors[0], alpha=0.8)
        else:
            # Multiple series
            bar_width = 0.8 / len(datasets)
            for i, dataset in enumerate(datasets):
                data = dataset.get('data', [])
                label = dataset.get('label', f'Series {i+1}')
                offset = (i - len(datasets)/2 + 0.5) * bar_width
                x_positions = [x + offset for x in x_pos]
                ax.bar(x_positions, data, bar_width, label=label, 
                      color=colors[i % len(colors)], alpha=0.8)
            
            ax.legend()
        
        # Styling
        ax.set_xlabel('Categories')
        ax.set_ylabel('Values')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.grid(True, alpha=0.3)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def create_line_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create a line chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets:
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        
        for i, dataset in enumerate(datasets):
            data = dataset.get('data', [])
            label = dataset.get('label', f'Series {i+1}')
            ax.plot(labels, data, marker='o', linewidth=2, 
                   color=colors[i % len(colors)], label=label)
        
        if len(datasets) > 1:
            ax.legend()
        
        # Styling
        ax.set_xlabel('Time')
        ax.set_ylabel('Values')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def create_pie_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create a pie chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets or not datasets[0].get('data'):
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        data = datasets[0].get('data', [])
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        
        wedges, texts, autotexts = ax.pie(
            data, 
            labels=labels, 
            colors=colors[:len(data)],
            autopct='%1.1f%%',
            startangle=90
        )
        
        # Styling
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def create_donut_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create a donut chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets or not datasets[0].get('data'):
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        data = datasets[0].get('data', [])
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        
        wedges, texts, autotexts = ax.pie(
            data, 
            labels=labels, 
            colors=colors[:len(data)],
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85
        )
        
        # Create donut hole
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        fig.gca().add_artist(centre_circle)
        
        # Styling
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def create_area_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create an area chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets:
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        
        for i, dataset in enumerate(datasets):
            data = dataset.get('data', [])
            label = dataset.get('label', f'Series {i+1}')
            ax.fill_between(labels, data, alpha=0.7, 
                           color=colors[i % len(colors)], label=label)
        
        if len(datasets) > 1:
            ax.legend()
        
        # Styling
        ax.set_xlabel('Time')
        ax.set_ylabel('Values')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def create_stacked_bar_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create a stacked bar chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets:
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        bottom = [0] * len(labels)
        
        for i, dataset in enumerate(datasets):
            data = dataset.get('data', [])
            label = dataset.get('label', f'Series {i+1}')
            ax.bar(labels, data, bottom=bottom, label=label, 
                  color=colors[i % len(colors)], alpha=0.8)
            
            # Update bottom for stacking
            bottom = [b + d for b, d in zip(bottom, data)]
        
        if len(datasets) > 1:
            ax.legend()
        
        # Styling
        ax.set_xlabel('Categories')
        ax.set_ylabel('Values')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        plt.xticks(rotation=45)
        ax.grid(True, alpha=0.3)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def create_horizontal_bar_chart(
        cls, 
        chart_data: Dict[str, Any], 
        width: float = 6, 
        height: float = 4
    ) -> Image:
        """Create a horizontal bar chart image for PDF."""
        labels = chart_data.get('labels', [])
        datasets = chart_data.get('datasets', [])
        title = chart_data.get('title', '')
        
        if not datasets:
            return cls._create_no_data_chart(width, height, title)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Plot data
        y_pos = range(len(labels))
        colors = ['#1f4e79', '#70ad47', '#ffc000', '#c55a5a', '#e4405f', '#1877f2']
        
        if len(datasets) == 1:
            # Single series
            dataset = datasets[0]
            data = dataset.get('data', [])
            ax.barh(y_pos, data, color=colors[0], alpha=0.8)
        else:
            # Multiple series
            bar_height = 0.8 / len(datasets)
            for i, dataset in enumerate(datasets):
                data = dataset.get('data', [])
                label = dataset.get('label', f'Series {i+1}')
                offset = (i - len(datasets)/2 + 0.5) * bar_height
                y_positions = [y + offset for y in y_pos]
                ax.barh(y_positions, data, bar_height, label=label, 
                       color=colors[i % len(colors)], alpha=0.8)
            
            ax.legend()
        
        # Styling
        ax.set_ylabel('Categories')
        ax.set_xlabel('Values')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def _create_no_data_chart(cls, width: float, height: float, title: str) -> Image:
        """Create a placeholder chart when no data is available."""
        fig, ax = plt.subplots(figsize=(width, height))
        
        ax.text(0.5, 0.5, 'No Data Available', 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=16, color='#808080')
        
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)
    
    @classmethod
    def _apply_consistent_styling(cls, ax, title: str):
        """Apply consistent styling to all charts."""
        # Set title
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1f4e79', pad=20)
        
        # Set grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Set spine colors
        for spine in ax.spines.values():
            spine.set_color('#cccccc')
            spine.set_linewidth(0.5)
        
        # Set tick parameters
        ax.tick_params(colors='#666666', which='both')
        
        # Set background color
        ax.set_facecolor('#fafafa')
    
    @classmethod
    def _get_chart_colors(cls, count: int) -> List[str]:
        """Get consistent chart colors."""
        colors = [
            '#1f4e79',  # Primary blue
            '#70ad47',  # Secondary green
            '#ffc000',  # Accent yellow
            '#c55a5a',  # Danger red
            '#e4405f',  # Instagram pink
            '#1877f2',  # Facebook blue
            '#29a3f2',  # Twitter blue
            '#ff0000',  # YouTube red
            '#25d366',  # WhatsApp green
            '#833ab4'   # Instagram purple
        ]
        
        # Repeat colors if needed
        result = []
        for i in range(count):
            result.append(colors[i % len(colors)])
        
        return result


class PDFTableGenerator:
    """Generates tables for PDF documents."""
    
    @classmethod
    def create_table(
        cls, 
        table_data: Dict[str, Any], 
        width: Optional[float] = None
    ) -> Table:
        """Create a styled table for PDF."""
        data = table_data.get('data', [])
        columns = table_data.get('columns', [])
        
        if not data or not columns:
            return None
        
        # Prepare table data with headers
        table_rows = [columns] + data
        
        # Create table
        if width:
            col_widths = [width / len(columns)] * len(columns)
            table = Table(table_rows, colWidths=col_widths)
        else:
            table = Table(table_rows)
        
        # Apply styling
        style_config = table_data.get('style', {})
        header_color = style_config.get('header_color', '#1f4e79')
        alternating_rows = style_config.get('alternating_rows', True)
        
        if isinstance(header_color, str):
            header_color = HexColor(header_color)
        
        table_style = PDFStyler.get_table_style(header_color, alternating_rows)
        table.setStyle(table_style)
        
        return table


class PDFImageHandler:
    """Handles image insertion in PDF documents."""
    
    @classmethod
    def create_image(
        cls, 
        image_path: str, 
        width: float = 2, 
        height: float = 1,
        fallback_text: str = "Image not available"
    ) -> Any:
        """Create an image element for PDF."""
        if os.path.exists(image_path):
            try:
                return Image(image_path, width=width*inch, height=height*inch)
            except:
                pass
        
        # Create placeholder
        return cls._create_image_placeholder(width, height, fallback_text)
    
    @classmethod
    def _create_image_placeholder(cls, width: float, height: float, text: str) -> Image:
        """Create an image placeholder."""
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Gray background
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor='#f2f2f2', edgecolor='#808080'))
        
        # Placeholder text
        ax.text(0.5, 0.5, text, 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=10, color='#808080')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        img_buffer.seek(0)
        return Image(img_buffer, width=width*inch, height=height*inch)