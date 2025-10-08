# Design Document - KOL Brief Management

## Overview

The KOL Brief Management system enables template-based brief creation, customization, versioning, approval workflows, and distribution to individual KOLs with response tracking.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Brief       │◀─────│   Brief      │◀─────│  Database   │
│  Builder     │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Communication│
                     │   Service    │
                     │  (Send Brief)│
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class BriefService:
    async def create_brief(campaign_id: int, kol_id: int, template_id: int) -> Brief
    async def get_brief(brief_id: int) -> Brief
    async def update_brief(brief_id: int, brief_data: BriefUpdate) -> Brief
    async def send_brief(brief_id: int) -> None
    async def get_brief_versions(brief_id: int) -> List[BriefVersion]

class BriefTemplateService:
    async def create_template(template_data: BriefTemplateCreate) -> BriefTemplate
    async def get_template(template_id: int) -> BriefTemplate
    async def list_templates() -> List[BriefTemplate]

class BriefApprovalService:
    async def submit_for_approval(brief_id: int) -> None
    async def approve_brief(brief_id: int, approver_id: int) -> None
    async def request_changes(brief_id: int, approver_id: int, comments: str) -> None
    async def reject_brief(brief_id: int, approver_id: int, reason: str) -> None

class BriefResponseService:
    async def record_response(brief_id: int, response_type: str, notes: str) -> None
    async def get_response_analytics(campaign_id: int) -> ResponseAnalytics
```

## Data Models

### Brief Model

```python
class Brief(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    template_id: int = Field(foreign_key="brieftemplate.id")
    version: Decimal = Field(default=1.0, max_digits=3, decimal_places=1)
    status: str  # draft, pending_approval, approved, sent, accepted, declined, negotiating
    content: dict = Field(sa_column=Column(JSON))  # Brief sections and content
    customizations: dict = Field(default={}, sa_column=Column(JSON))
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    responded_at: Optional[datetime]
```

### BriefTemplate Model

```python
class BriefTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str]
    sections: List[dict] = Field(sa_column=Column(JSON))  # Template sections
    variables: List[str] = Field(sa_column=Column(ARRAY(String)))
    is_default: bool = Field(default=False)
    usage_count: int = Field(default=0)
    acceptance_rate: Optional[Decimal] = Field(max_digits=5, decimal_places=2)
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### BriefVersion Model

```python
class BriefVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brief_id: int = Field(foreign_key="brief.id", index=True)
    version: Decimal = Field(max_digits=3, decimal_places=1)
    content: dict = Field(sa_column=Column(JSON))
    changes_summary: Optional[str]
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### BriefApproval Model

```python
class BriefApproval(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brief_id: int = Field(foreign_key="brief.id")
    approver_id: int = Field(foreign_key="user.id")
    action: str  # approved, requested_changes, rejected
    comments: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### BriefResponse Model

```python
class BriefResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brief_id: int = Field(foreign_key="brief.id", unique=True)
    response_type: str  # accepted, declined, negotiating
    decline_reason: Optional[str]
    negotiation_notes: Optional[str]
    revised_terms: Optional[dict] = Field(sa_column=Column(JSON))
    responded_at: datetime = Field(default_factory=datetime.utcnow)
```

## API Endpoints

```python
# Brief Management
POST   /api/v1/campaigns/{id}/briefs                 # Create brief
GET    /api/v1/campaigns/{id}/briefs                 # List campaign briefs
GET    /api/v1/briefs/{id}                           # Get brief details
PUT    /api/v1/briefs/{id}                           # Update brief
DELETE /api/v1/briefs/{id}                           # Delete brief
GET    /api/v1/briefs/{id}/versions                  # Get brief versions
POST   /api/v1/briefs/{id}/send                      # Send brief to KOL

# Brief Templates
POST   /api/v1/brief-templates                       # Create template
GET    /api/v1/brief-templates                       # List templates
GET    /api/v1/brief-templates/{id}                  # Get template
PUT    /api/v1/brief-templates/{id}                  # Update template
DELETE /api/v1/brief-templates/{id}                  # Delete template

# Approval Workflow
POST   /api/v1/briefs/{id}/submit-for-approval       # Submit for approval
POST   /api/v1/briefs/{id}/approve                   # Approve brief
POST   /api/v1/briefs/{id}/request-changes           # Request changes
POST   /api/v1/briefs/{id}/reject                    # Reject brief

# Response Tracking
POST   /api/v1/briefs/{id}/response                  # Record KOL response
GET    /api/v1/briefs/{id}/response                  # Get response details
GET    /api/v1/campaigns/{id}/brief-analytics        # Get response analytics
```

## Brief Template Structure

### Template Sections

```json
{
    "sections": [
        {
            "id": "campaign_overview",
            "title": "Campaign Overview",
            "content": "{{campaign_name}} is a {{campaign_duration}} campaign...",
            "editable": true
        },
        {
            "id": "objectives",
            "title": "Campaign Objectives",
            "content": "{{campaign_objectives}}",
            "editable": true
        },
        {
            "id": "deliverables",
            "title": "Deliverables",
            "content": [
                {
                    "type": "{{deliverable_type}}",
                    "quantity": "{{deliverable_quantity}}",
                    "deadline": "{{deliverable_deadline}}"
                }
            ],
            "editable": true
        },
        {
            "id": "compensation",
            "title": "Compensation",
            "content": "{{compensation_amount}} {{currency}}",
            "editable": true
        },
        {
            "id": "guidelines",
            "title": "Brand Guidelines",
            "content": "{{brand_guidelines}}",
            "editable": false
        }
    ]
}
```

## Brief Generation

### Auto-populate from Campaign

```python
async def generate_brief_from_campaign(campaign_id: int, kol_id: int, template_id: int) -> Brief:
    """Generate brief with campaign data"""
    campaign = await get_campaign(campaign_id)
    kol = await get_kol(kol_id)
    template = await get_brief_template(template_id)

    # Get template variables
    variables = {
        'campaign_name': campaign.name,
        'campaign_duration': f"{(campaign.end_date - campaign.start_date).days} days",
        'campaign_objectives': campaign.objectives,
        'campaign_start_date': campaign.start_date.strftime('%B %d, %Y'),
        'campaign_end_date': campaign.end_date.strftime('%B %d, %Y'),
        'kol_name': kol.name,
        'kol_niche': ', '.join(kol.niche),
        'brand_guidelines': campaign.client_brief.brand_guidelines if campaign.client_brief else '',
    }

    # Populate deliverables
    deliverables = []
    for deliverable in campaign.deliverables:
        deliverables.append({
            'type': deliverable.deliverable_type,
            'quantity': deliverable.quantity,
            'deadline': deliverable.deadline.strftime('%B %d, %Y')
        })
    variables['deliverables'] = deliverables

    # Get KOL-specific compensation
    campaign_kol = await get_campaign_kol(campaign_id, kol_id)
    variables['compensation_amount'] = f"{campaign_kol.fee:,.2f}" if campaign_kol.fee else "TBD"
    variables['currency'] = campaign.currency

    # Render template
    content = render_brief_template(template, variables)

    return Brief(
        campaign_id=campaign_id,
        kol_id=kol_id,
        template_id=template_id,
        content=content,
        status="draft"
    )
```

## Approval Workflow

### Status Transitions

```python
ALLOWED_TRANSITIONS = {
    'draft': ['pending_approval'],
    'pending_approval': ['approved', 'draft'],  # Can request changes back to draft
    'approved': ['sent'],
    'sent': ['accepted', 'declined', 'negotiating'],
    'negotiating': ['accepted', 'declined'],
    'accepted': [],
    'declined': []
}

async def change_brief_status(brief_id: int, new_status: str, user_id: int) -> Brief:
    """Change brief status with validation"""
    brief = await get_brief(brief_id)

    if new_status not in ALLOWED_TRANSITIONS[brief.status]:
        raise ValueError(f"Cannot transition from {brief.status} to {new_status}")

    brief.status = new_status

    # Record approval action
    if new_status in ['approved', 'draft']:
        await record_approval_action(brief_id, user_id, new_status)

    return await save_brief(brief)
```

## Versioning

### Create New Version

```python
async def create_brief_version(brief_id: int, changes_summary: str) -> Brief:
    """Create new version when brief is edited after sending"""
    brief = await get_brief(brief_id)

    # Save current version
    await save_brief_version(
        brief_id=brief_id,
        version=brief.version,
        content=brief.content
    )

    # Increment version
    if changes_summary and "major" in changes_summary.lower():
        brief.version = float(int(brief.version) + 1)  # 1.0 -> 2.0
    else:
        brief.version = brief.version + 0.1  # 1.0 -> 1.1

    return await save_brief(brief)
```

## Response Analytics

### Calculate Acceptance Rate

```python
async def calculate_acceptance_rate(campaign_id: int) -> Dict[str, float]:
    """Calculate brief acceptance rates"""
    briefs = await get_campaign_briefs(campaign_id)

    total = len(briefs)
    accepted = len([b for b in briefs if b.status == 'accepted'])
    declined = len([b for b in briefs if b.status == 'declined'])
    no_response = len([b for b in briefs if b.status == 'sent' and not b.responded_at])

    return {
        'acceptance_rate': (accepted / total * 100) if total > 0 else 0,
        'decline_rate': (declined / total * 100) if total > 0 else 0,
        'no_response_rate': (no_response / total * 100) if total > 0 else 0,
        'avg_response_time_hours': calculate_avg_response_time(briefs)
    }
```

## Performance Considerations

### Database Indexes

```sql
CREATE INDEX idx_brief_campaign_kol ON brief(campaign_id, kol_id);
CREATE INDEX idx_brief_status ON brief(status);
CREATE INDEX idx_brief_version_brief ON briefversion(brief_id, version DESC);
```

### Caching

-   Templates: Cache indefinitely
-   Brief content: No cache (always fresh)
-   Analytics: Cache for 5 minutes

## Testing Strategy

### Unit Tests

-   Brief generation from campaign
-   Template rendering
-   Version increment logic
-   Status transition validation

### Integration Tests

-   End-to-end brief creation
-   Approval workflow
-   Brief sending
-   Response tracking
