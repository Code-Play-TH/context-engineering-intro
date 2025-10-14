"""
Script to seed default report templates.
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


# Default PowerPoint template structure
POWERPOINT_CAMPAIGN_SUMMARY = {
    "slides": [
        {
            "slide_number": 1,
            "layout": "title_slide",
            "elements": [
                {
                    "type": "text",
                    "content": "{{campaign_name}} - Campaign Report",
                    "position": {"x": 1, "y": 2, "width": 8, "height": 1},
                    "style": {"font": "Arial", "size": 44, "bold": True, "color": "#1f4e79"}
                },
                {
                    "type": "text",
                    "content": "Generated on {{generation_date}}",
                    "position": {"x": 1, "y": 3.5, "width": 8, "height": 0.5},
                    "style": {"font": "Arial", "size": 18, "color": "#666666"}
                },
                {
                    "type": "image",
                    "source": "{{client_logo}}",
                    "position": {"x": 8, "y": 0.5, "width": 1.5, "height": 1},
                    "fallback": "logo_placeholder.png"
                }
            ]
        },
        {
            "slide_number": 2,
            "layout": "content",
            "title": "Campaign Overview",
            "elements": [
                {
                    "type": "text",
                    "content": "Campaign: {{campaign_name}}",
                    "position": {"x": 1, "y": 1.5, "width": 8, "height": 0.5},
                    "style": {"font": "Arial", "size": 24, "bold": True}
                },
                {
                    "type": "text",
                    "content": "Duration: {{campaign_start_date}} - {{campaign_end_date}}",
                    "position": {"x": 1, "y": 2, "width": 8, "height": 0.5},
                    "style": {"font": "Arial", "size": 18}
                },
                {
                    "type": "text",
                    "content": "Total Budget: {{campaign_budget}} {{campaign_currency}}",
                    "position": {"x": 1, "y": 2.5, "width": 8, "height": 0.5},
                    "style": {"font": "Arial", "size": 18}
                },
                {
                    "type": "table",
                    "data_source": "campaign_kpis",
                    "position": {"x": 1, "y": 3.5, "width": 8, "height": 3},
                    "columns": ["KPI", "Target", "Actual", "Achievement %"],
                    "style": {"header_color": "#1f4e79", "alternating_rows": True}
                }
            ]
        },
        {
            "slide_number": 3,
            "layout": "content",
            "title": "KOL Performance",
            "elements": [
                {
                    "type": "chart",
                    "chart_type": "bar",
                    "data_source": "kol_performance",
                    "position": {"x": 1, "y": 1.5, "width": 8, "height": 4},
                    "title": "KOL Reach and Engagement",
                    "x_axis": "KOL Name",
                    "y_axis": "Metrics",
                    "series": ["Total Reach", "Total Engagement"],
                    "colors": ["#1f4e79", "#70ad47"]
                },
                {
                    "type": "text",
                    "content": "Total KOLs: {{kol_count}}",
                    "position": {"x": 1, "y": 6, "width": 4, "height": 0.5},
                    "style": {"font": "Arial", "size": 16}
                },
                {
                    "type": "text",
                    "content": "Average Engagement Rate: {{avg_engagement_rate}}%",
                    "position": {"x": 5, "y": 6, "width": 4, "height": 0.5},
                    "style": {"font": "Arial", "size": 16}
                }
            ]
        },
        {
            "slide_number": 4,
            "layout": "content",
            "title": "Campaign Results",
            "elements": [
                {
                    "type": "chart",
                    "chart_type": "donut",
                    "data_source": "kpi_achievement",
                    "position": {"x": 1, "y": 1.5, "width": 4, "height": 4},
                    "title": "KPI Achievement",
                    "colors": ["#70ad47", "#ffc000", "#c55a5a"]
                },
                {
                    "type": "table",
                    "data_source": "campaign_summary",
                    "position": {"x": 5.5, "y": 1.5, "width": 3.5, "height": 4},
                    "columns": ["Metric", "Value"],
                    "style": {"header_color": "#1f4e79"}
                }
            ]
        }
    ]
}

# Default PDF template structure
PDF_CAMPAIGN_REPORT = {
    "pages": [
        {
            "page_number": 1,
            "type": "cover",
            "elements": [
                {
                    "type": "text",
                    "content": "{{campaign_name}}",
                    "style": "title",
                    "position": {"y": 200},
                    "font_size": 36,
                    "color": "#1f4e79"
                },
                {
                    "type": "text",
                    "content": "Campaign Performance Report",
                    "style": "subtitle",
                    "position": {"y": 250},
                    "font_size": 24,
                    "color": "#666666"
                },
                {
                    "type": "text",
                    "content": "Generated on {{generation_date}}",
                    "style": "normal",
                    "position": {"y": 300},
                    "font_size": 14
                },
                {
                    "type": "image",
                    "source": "{{client_logo}}",
                    "position": {"x": 450, "y": 50, "width": 100, "height": 50},
                    "fallback": "logo_placeholder.png"
                }
            ]
        },
        {
            "page_number": 2,
            "type": "content",
            "title": "Executive Summary",
            "elements": [
                {
                    "type": "text",
                    "content": "Campaign Overview",
                    "style": "heading2",
                    "font_size": 18,
                    "color": "#1f4e79"
                },
                {
                    "type": "text",
                    "content": "Campaign Name: {{campaign_name}}",
                    "style": "normal",
                    "font_size": 12
                },
                {
                    "type": "text",
                    "content": "Duration: {{campaign_start_date}} to {{campaign_end_date}}",
                    "style": "normal",
                    "font_size": 12
                },
                {
                    "type": "text",
                    "content": "Total Budget: {{campaign_budget}} {{campaign_currency}}",
                    "style": "normal",
                    "font_size": 12
                },
                {
                    "type": "text",
                    "content": "Number of KOLs: {{kol_count}}",
                    "style": "normal",
                    "font_size": 12
                },
                {
                    "type": "spacer",
                    "height": 20
                },
                {
                    "type": "text",
                    "content": "Key Results",
                    "style": "heading2",
                    "font_size": 18,
                    "color": "#1f4e79"
                },
                {
                    "type": "table",
                    "data_source": "campaign_kpis",
                    "columns": ["KPI", "Target", "Actual", "Achievement %"],
                    "style": {
                        "header_color": "#1f4e79",
                        "header_text_color": "white",
                        "alternating_rows": True,
                        "border": True
                    }
                }
            ]
        },
        {
            "page_number": 3,
            "type": "content",
            "title": "KOL Performance Analysis",
            "elements": [
                {
                    "type": "text",
                    "content": "Individual KOL Performance",
                    "style": "heading2",
                    "font_size": 18,
                    "color": "#1f4e79"
                },
                {
                    "type": "chart",
                    "chart_type": "bar",
                    "data_source": "kol_performance",
                    "title": "KOL Reach and Engagement Comparison",
                    "width": 500,
                    "height": 300,
                    "x_axis": "KOL Name",
                    "y_axis": "Metrics",
                    "series": ["Total Reach", "Total Engagement"],
                    "colors": ["#1f4e79", "#70ad47"]
                },
                {
                    "type": "spacer",
                    "height": 20
                },
                {
                    "type": "table",
                    "data_source": "kol_detailed_metrics",
                    "columns": ["KOL Name", "Followers", "Posts", "Avg Engagement", "Total Reach"],
                    "style": {
                        "header_color": "#1f4e79",
                        "header_text_color": "white",
                        "alternating_rows": True,
                        "border": True
                    }
                }
            ]
        }
    ]
}

# Template variables for both templates
COMMON_VARIABLES = [
    "{{campaign_name}}",
    "{{campaign_start_date}}",
    "{{campaign_end_date}}",
    "{{campaign_budget}}",
    "{{campaign_currency}}",
    "{{kol_count}}",
    "{{total_reach}}",
    "{{total_engagement}}",
    "{{avg_engagement_rate}}",
    "{{generation_date}}",
    "{{client_logo}}"
]


def seed_default_templates():
    """Seed default report templates."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if templates already exist
        result = conn.execute(text("""
            SELECT COUNT(*) FROM report_templates 
            WHERE name IN ('Campaign Summary (PowerPoint)', 'Campaign Report (PDF)')
        """))
        
        if result.scalar() > 0:
            print("Default templates already exist. Skipping...")
            return
        
        # Use a default user ID (1) for the admin user
        admin_user_id = 1
        current_time = datetime.utcnow()
        
        # Insert PowerPoint template
        conn.execute(text("""
            INSERT INTO report_templates 
            (name, description, template_type, is_shared, structure, variables, created_by, created_at, usage_count)
            VALUES 
            (:name, :description, :template_type, :is_shared, :structure, :variables, :created_by, :created_at, :usage_count)
        """), {
            "name": "Campaign Summary (PowerPoint)",
            "description": "Standard PowerPoint template for campaign performance reports with charts and KPI tables",
            "template_type": "powerpoint",
            "is_shared": True,
            "structure": json.dumps(POWERPOINT_CAMPAIGN_SUMMARY),
            "variables": COMMON_VARIABLES,
            "created_by": admin_user_id,
            "created_at": current_time,
            "usage_count": 0
        })
        
        # Insert PDF template
        conn.execute(text("""
            INSERT INTO report_templates 
            (name, description, template_type, is_shared, structure, variables, created_by, created_at, usage_count)
            VALUES 
            (:name, :description, :template_type, :is_shared, :structure, :variables, :created_by, :created_at, :usage_count)
        """), {
            "name": "Campaign Report (PDF)",
            "description": "Comprehensive PDF template for detailed campaign analysis and KOL performance metrics",
            "template_type": "pdf",
            "is_shared": True,
            "structure": json.dumps(PDF_CAMPAIGN_REPORT),
            "variables": COMMON_VARIABLES,
            "created_by": admin_user_id,
            "created_at": current_time,
            "usage_count": 0
        })
        
        # Commit changes
        conn.commit()
        
        print("✅ Default report templates created successfully!")
        print("   - Campaign Summary (PowerPoint)")
        print("   - Campaign Report (PDF)")


if __name__ == "__main__":
    print("🌱 Seeding default report templates...")
    seed_default_templates()
    print("✨ Seeding completed!")