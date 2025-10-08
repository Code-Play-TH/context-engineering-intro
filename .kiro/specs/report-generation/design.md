# Design Document - Report Generation & Templates

## Overview

The Report Generation system enables automated creation of campaign reports in PowerPoint and PDF formats with customizable templates, AI-powered template generation from samples, and dynamic data population.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Template    │◀─────│   Report     │◀─────│  Database   │
│  Builder     │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Celery    │
                     │  (Report     │
                     │  Generation) │
                     └──────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
         ┌──────────────┐      ┌──────────────┐
         │  python-pptx │      │  ReportLab/  │
         │  (PowerPoint)│      │  WeasyPrint  │
         └──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  OpenAI/     │
                     │  Anthropic   │
                     │  (Template   │
                     │  Analysis)   │
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class ReportTemplateService:
    async def create_template(template_data: TemplateCreate) -> ReportTemplate
    async def get_template(template_id: int) -> ReportTemplate
    async def list_templates(filters: TemplateFilters) -> List[ReportTemplate]
    async def update_template(template_id: int, template_data: TemplateUpdate) -> ReportTemplate
    async def delete_template(template_id: int) -> None
    async def duplicate_template(template_id: int) -> ReportTemplate

class AITemplateService:
    async def analyze_sample_file(file: UploadFile) -> TemplateAnalysis
    async def generate_template_from_sample(file: UploadFile) -> ReportTemplate
    async def suggest_variable_mappings(template_structure: dict) -> Dict[str, str]

class ReportGenerationService:
    async def generate_powerpoint(campaign_id: int, template_id: int) -> str
    async def generate_pdf(campaign_id: int, template_id: int) -> str
    async def get_generation_status(job_id: int) -> GenerationStatus
    async def schedule_report(campaign_id: int, template_id: int, schedule: ReportSchedule) -> None

class DataPopulationService:
    async def populate_template_variables(template: ReportTemplate, campaign_id: int) -> dict
    async def generate_chart_data(chart_config: dict, campaign_id: int) -> ChartData
    async def fetch_kol_images(kol_ids: List[int]) -> Dict[int, str]
```

## Data Models

### ReportTemplate Model

```python
class ReportTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str]
    template_type: str  # powerpoint, pdf
    is_shared: bool = Field(default=False)
    structure: dict = Field(sa_column=Column(JSON))  # Template layout definition
    variables: List[str] = Field(sa_column=Column(ARRAY(String)))  # {{campaign_name}}, etc.
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = Field(default=0)
```

### ReportGeneration Model

```python
class ReportGeneration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    template_id: int = Field(foreign_key="reporttemplate.id")
    report_type: str  # powerpoint, pdf
    status: str  # pending, processing, completed, failed
    file_path: Optional[str]
    download_url: Optional[str]
    error_message: Optional[str]
    generated_by: int = Field(foreign_key="user.id")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Download link expiry
```

### ReportSchedule Model

```python
class ReportSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    template_id: int = Field(foreign_key="reporttemplate.id")
    frequency: str  # daily, weekly, monthly, campaign_end
    recipients: List[str] = Field(sa_column=Column(ARRAY(String)))  # Email addresses
    is_active: bool = Field(default=True)
    last_generated_at: Optional[datetime]
    next_generation_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## API Endpoints

```python
# Template Management
POST   /api/v1/report-templates                     # Create template
GET    /api/v1/report-templates                     # List templates
GET    /api/v1/report-templates/{id}                # Get template
PUT    /api/v1/report-templates/{id}                # Update template
DELETE /api/v1/report-templates/{id}                # Delete template
POST   /api/v1/report-templates/{id}/duplicate      # Duplicate template

# AI Template Generation
POST   /api/v1/report-templates/analyze-sample      # Analyze sample file
POST   /api/v1/report-templates/generate-from-sample  # Generate template from sample

# Report Generation
POST   /api/v1/campaigns/{id}/reports/generate      # Generate report
GET    /api/v1/campaigns/{id}/reports                # List generated reports
GET    /api/v1/reports/{id}/download                # Download report
GET    /api/v1/reports/{id}/status                  # Get generation status

# Report Scheduling
POST   /api/v1/campaigns/{id}/reports/schedule      # Schedule report
GET    /api/v1/campaigns/{id}/reports/schedules     # List schedules
PUT    /api/v1/reports/schedules/{id}               # Update schedule
DELETE /api/v1/reports/schedules/{id}               # Delete schedule
```

## Template Structure Format

### PowerPoint Template Structure

```json
{
    "slides": [
        {
            "slide_number": 1,
            "layout": "title_slide",
            "elements": [
                {
                    "type": "text",
                    "content": "{{campaign_name}}",
                    "position": { "x": 1, "y": 2, "width": 8, "height": 1 },
                    "style": { "font": "Arial", "size": 44, "bold": true }
                },
                {
                    "type": "image",
                    "source": "{{client_logo}}",
                    "position": { "x": 0.5, "y": 0.5, "width": 2, "height": 1 }
                }
            ]
        },
        {
            "slide_number": 2,
            "layout": "content",
            "elements": [
                {
                    "type": "chart",
                    "chart_type": "bar",
                    "data_source": "kol_performance",
                    "position": { "x": 1, "y": 2, "width": 8, "height": 4 }
                },
                {
                    "type": "table",
                    "data_source": "campaign_kpis",
                    "position": { "x": 1, "y": 6, "width": 8, "height": 2 }
                }
            ]
        }
    ]
}
```

### Variable Mapping

```python
AVAILABLE_VARIABLES = {
    # Campaign variables
    '{{campaign_name}}': 'campaign.name',
    '{{campaign_start_date}}': 'campaign.start_date',
    '{{campaign_end_date}}': 'campaign.end_date',
    '{{campaign_budget}}': 'campaign.total_budget',

    # KOL variables
    '{{kol_count}}': 'count(campaign.kols)',
    '{{kol_list}}': 'campaign.kols.names',

    # Metrics variables
    '{{total_reach}}': 'sum(kol_metrics.follower_count)',
    '{{total_engagement}}': 'sum(post_metrics.likes + post_metrics.comments)',
    '{{engagement_rate}}': 'avg(kol_metrics.engagement_rate)',
    '{{total_posts}}': 'count(posts)',

    # KPI variables
    '{{kpi_reach_target}}': 'campaign_kpi.reach.target',
    '{{kpi_reach_actual}}': 'campaign_kpi.reach.actual',
    '{{kpi_achievement_rate}}': 'campaign_kpi.achievement_percentage'
}
```

## PowerPoint Generation

### Using python-pptx

```python
from pptx import Presentation
from pptx.util import Inches, Pt

async def generate_powerpoint(campaign_id: int, template: ReportTemplate) -> str:
    """Generate PowerPoint report from template"""
    prs = Presentation()

    # Populate template variables
    data = await populate_template_variables(template, campaign_id)

    for slide_config in template.structure['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[slide_config['layout_index']])

        for element in slide_config['elements']:
            if element['type'] == 'text':
                add_text_element(slide, element, data)
            elif element['type'] == 'chart':
                add_chart_element(slide, element, data)
            elif element['type'] == 'table':
                add_table_element(slide, element, data)
            elif element['type'] == 'image':
                add_image_element(slide, element, data)

    # Save to file
    file_path = f"uploads/reports/{campaign_id}_{template.id}_{datetime.now().timestamp()}.pptx"
    prs.save(file_path)

    return file_path

def add_chart_element(slide, element: dict, data: dict):
    """Add chart to slide"""
    chart_data = data[element['data_source']]

    # Create chart
    x, y, cx, cy = Inches(element['position']['x']), Inches(element['position']['y']), \
                   Inches(element['position']['width']), Inches(element['position']['height'])

    chart = slide.shapes.add_chart(
        element['chart_type'],
        x, y, cx, cy,
        chart_data
    ).chart

    # Customize chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
```

## PDF Generation

### Using ReportLab

```python
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet

async def generate_pdf(campaign_id: int, template: ReportTemplate) -> str:
    """Generate PDF report from template"""
    file_path = f"uploads/reports/{campaign_id}_{template.id}_{datetime.now().timestamp()}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Populate template variables
    data = await populate_template_variables(template, campaign_id)

    for page_config in template.structure['pages']:
        for element in page_config['elements']:
            if element['type'] == 'text':
                text = replace_variables(element['content'], data)
                story.append(Paragraph(text, styles[element['style']]))
                story.append(Spacer(1, 12))

            elif element['type'] == 'table':
                table_data = data[element['data_source']]
                table = Table(table_data)
                story.append(table)
                story.append(Spacer(1, 12))

            elif element['type'] == 'chart':
                chart_image = await generate_chart_image(element, data)
                story.append(Image(chart_image, width=400, height=300))
                story.append(Spacer(1, 12))

    doc.build(story)
    return file_path
```

## AI Template Analysis

### Sample File Analysis with LLM

```python
async def analyze_sample_file(file: UploadFile) -> TemplateAnalysis:
    """Analyze sample PowerPoint/PDF and extract structure"""

    # Extract text and layout from file
    if file.filename.endswith('.pptx'):
        structure = extract_pptx_structure(file)
    elif file.filename.endswith('.pdf'):
        structure = extract_pdf_structure(file)

    # Use LLM to identify data fields
    prompt = f"""
    Analyze this report structure and identify data fields that should be variables:

    {json.dumps(structure, indent=2)}

    For each text field, determine if it should be:
    1. Static text (keep as-is)
    2. Variable (replace with {{variable_name}})

    Suggest appropriate variable names for dynamic fields.
    Return as JSON with mappings.
    """

    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return parse_template_analysis(response.choices[0].message.content)
```

## Chart Generation

### Using matplotlib

```python
import matplotlib.pyplot as plt
import io

async def generate_chart_image(chart_config: dict, data: dict) -> bytes:
    """Generate chart image from data"""
    chart_data = data[chart_config['data_source']]

    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_config['chart_type'] == 'bar':
        ax.bar(chart_data['labels'], chart_data['values'])
    elif chart_config['chart_type'] == 'line':
        ax.plot(chart_data['labels'], chart_data['values'])
    elif chart_config['chart_type'] == 'pie':
        ax.pie(chart_data['values'], labels=chart_data['labels'], autopct='%1.1f%%')

    ax.set_title(chart_config.get('title', ''))
    ax.set_xlabel(chart_config.get('xlabel', ''))
    ax.set_ylabel(chart_config.get('ylabel', ''))

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)

    return buf.getvalue()
```

## Performance Considerations

### Background Processing

-   Generate reports as Celery tasks
-   Process in queue with priority (manual > scheduled)
-   Timeout: 5 minutes per report

### File Storage

-   Store generated reports for 90 days
-   Move to cold storage after 30 days
-   Clean up expired files daily

### Caching

-   Template structure: Cache indefinitely (invalidate on update)
-   Campaign data: No cache (always fresh)
-   Chart images: Cache for 1 hour

## Testing Strategy

### Unit Tests

-   Variable replacement logic
-   Chart generation
-   Table formatting
-   Template validation

### Integration Tests

-   End-to-end PowerPoint generation
-   End-to-end PDF generation
-   AI template analysis
-   Scheduled report generation

### Visual Tests

-   Compare generated reports with expected output
-   Verify chart rendering
-   Check layout consistency
