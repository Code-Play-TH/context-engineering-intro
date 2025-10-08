# Design Document - Campaign Management

## Overview

The Campaign Management system enables end-to-end campaign lifecycle management from client brief intake through execution. It handles campaign structure, timeline planning, budget tracking, team assignment, and workflow status management.

## Architecture

### High-Level Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Campaign    │◀─────│   Campaign   │◀─────│  Database   │
│  Dashboard   │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Celery    │
                     │  (Timeline   │
                     │  Reminders)  │
                     └──────────────┘
```

### Campaign Lifecycle

```
Draft → Pending Approval → Active → Completed
  │                                      │
  └──────────────▶ Cancelled ◀──────────┘
```

## Components and Interfaces

### Backend Services

#### 1. Campaign Service (`app/services/campaign_service.py`)

```python
class CampaignService:
    async def create_campaign(campaign_data: CampaignCreate, user_id: int) -> Campaign
    async def get_campaign(campaign_id: int) -> Campaign
    async def update_campaign(campaign_id: int, campaign_data: CampaignUpdate) -> Campaign
    async def list_campaigns(filters: CampaignFilters) -> List[Campaign]
    async def change_status(campaign_id: int, new_status: CampaignStatus) -> Campaign
    async def duplicate_campaign(campaign_id: int) -> Campaign
    async def delete_campaign(campaign_id: int) -> None
```

#### 2. Client Brief Service (`app/services/client_brief_service.py`)

```python
class ClientBriefService:
    async def create_brief(brief_data: ClientBriefCreate) -> ClientBrief
    async def get_brief(brief_id: int) -> ClientBrief
    async def update_brief(brief_id: int, brief_data: ClientBriefUpdate) -> ClientBrief
    async def upload_assets(brief_id: int, files: List[UploadFile]) -> List[str]
```

#### 3. Budget Service (`app/services/budget_service.py`)

```python
class BudgetService:
    async def allocate_budget(campaign_id: int, allocations: List[BudgetAllocation]) -> None
    async def record_expense(campaign_id: int, expense: ExpenseCreate) -> Expense
    async def get_budget_summary(campaign_id: int) -> BudgetSummary
    async def check_budget_threshold(campaign_id: int) -> BudgetAlert
```

#### 4. Timeline Service (`app/services/timeline_service.py`)

```python
class TimelineService:
    async def create_milestone(campaign_id: int, milestone: MilestoneCreate) -> Milestone
    async def update_milestone(milestone_id: int, milestone: MilestoneUpdate) -> Milestone
    async def get_timeline(campaign_id: int) -> Timeline
    async def check_overdue_milestones() -> List[Milestone]
```

### API Endpoints

#### Campaign Endpoints (`app/api/v1/campaigns.py`)

```python
POST   /api/v1/campaigns                    # Create campaign
GET    /api/v1/campaigns                    # List campaigns
GET    /api/v1/campaigns/{id}               # Get campaign details
PUT    /api/v1/campaigns/{id}               # Update campaign
DELETE /api/v1/campaigns/{id}               # Delete campaign
POST   /api/v1/campaigns/{id}/duplicate     # Duplicate campaign
PUT    /api/v1/campaigns/{id}/status        # Change status
GET    /api/v1/campaigns/{id}/budget        # Get budget summary
POST   /api/v1/campaigns/{id}/expenses      # Record expense
GET    /api/v1/campaigns/{id}/timeline      # Get timeline
POST   /api/v1/campaigns/{id}/milestones    # Create milestone
PUT    /api/v1/campaigns/{id}/team          # Assign team members
```

#### Client Brief Endpoints (`app/api/v1/client-briefs.py`)

```python
POST   /api/v1/client-briefs                # Create client brief
GET    /api/v1/client-briefs                # List briefs
GET    /api/v1/client-briefs/{id}           # Get brief details
PUT    /api/v1/client-briefs/{id}           # Update brief
POST   /api/v1/client-briefs/{id}/assets    # Upload brand assets
```

## Data Models

### Campaign Model (`app/models/campaign.py`)

```python
class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    client_brief_id: Optional[int] = Field(foreign_key="clientbrief.id")
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT)
    start_date: date
    end_date: date
    total_budget: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str = Field(default="USD")
    objectives: str  # Campaign objectives
    target_audience: dict = Field(sa_column=Column(JSON))
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    client_brief: Optional["ClientBrief"] = Relationship(back_populates="campaigns")
    kpis: List["CampaignKPI"] = Relationship(back_populates="campaign")
    deliverables: List["Deliverable"] = Relationship(back_populates="campaign")
    team_members: List["CampaignTeamMember"] = Relationship(back_populates="campaign")
```

### ClientBrief Model (`app/models/client_brief.py`)

```python
class ClientBrief(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str
    campaign_objective: str
    target_audience: dict = Field(sa_column=Column(JSON))
    budget: Decimal = Field(max_digits=12, decimal_places=2)
    brand_guidelines: Optional[str]
    content_requirements: Optional[str]
    special_instructions: Optional[str]
    status: str = Field(default="draft")  # draft, approved, in-progress, completed
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    campaigns: List["Campaign"] = Relationship(back_populates="client_brief")
    assets: List["BriefAsset"] = Relationship(back_populates="brief")
```

### CampaignKPI Model (`app/models/campaign_kpi.py`)

```python
class CampaignKPI(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    kpi_type: str  # reach, engagement, conversions, impressions, etc.
    target_value: Decimal
    actual_value: Optional[Decimal] = None
    unit: str  # count, percentage, currency
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="kpis")
```

### Deliverable Model (`app/models/deliverable.py`)

```python
class Deliverable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    deliverable_type: str  # post, story, video, reel, etc.
    quantity: int
    deadline: date
    status: str = Field(default="pending")  # pending, in-progress, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="deliverables")
```

### BudgetAllocation Model (`app/models/budget_allocation.py`)

```python
class BudgetAllocation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    category: str  # kol_fees, production, ads, misc
    allocated_amount: Decimal = Field(max_digits=12, decimal_places=2)
    spent_amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Milestone Model (`app/models/milestone.py`)

```python
class Milestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    name: str
    due_date: date
    responsible_user_id: int = Field(foreign_key="user.id")
    status: str = Field(default="not_started")  # not_started, in_progress, completed, overdue
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### CampaignTeamMember Model (`app/models/campaign_team_member.py`)

```python
class CampaignTeamMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    user_id: int = Field(foreign_key="user.id")
    role: str  # lead, account_executive, coordinator
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="team_members")
    user: "User" = Relationship()
```

## Business Logic

### Campaign Status Transitions

```python
ALLOWED_TRANSITIONS = {
    CampaignStatus.DRAFT: [CampaignStatus.PENDING_APPROVAL, CampaignStatus.CANCELLED],
    CampaignStatus.PENDING_APPROVAL: [CampaignStatus.ACTIVE, CampaignStatus.DRAFT, CampaignStatus.CANCELLED],
    CampaignStatus.ACTIVE: [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED],
    CampaignStatus.COMPLETED: [],
    CampaignStatus.CANCELLED: []
}
```

### Budget Alert Thresholds

```python
def check_budget_alerts(campaign_id: int) -> List[BudgetAlert]:
    budget_summary = get_budget_summary(campaign_id)
    utilization = budget_summary.spent / budget_summary.total

    if utilization >= 1.0:
        return BudgetAlert(level="critical", message="Budget exceeded")
    elif utilization >= 0.8:
        return BudgetAlert(level="warning", message="80% budget used")
    return None
```

## Error Handling

### Campaign Errors

```python
400 Bad Request: Invalid date range, budget allocation exceeds total
403 Forbidden: Cannot delete active campaign
404 Not Found: Campaign not found
409 Conflict: Invalid status transition
```

## Testing Strategy

### Unit Tests

-   Campaign CRUD operations
-   Status transition validation
-   Budget calculation logic
-   Timeline milestone tracking

### Integration Tests

-   Campaign creation from client brief
-   Team member assignment
-   Budget allocation and tracking
-   Milestone notifications

## Performance Considerations

### Database Indexes

```sql
CREATE INDEX idx_campaign_status ON campaign(status);
CREATE INDEX idx_campaign_dates ON campaign(start_date, end_date);
CREATE INDEX idx_campaign_created_by ON campaign(created_by);
CREATE INDEX idx_milestone_due_date ON milestone(due_date);
CREATE INDEX idx_milestone_status ON milestone(status);
```

### Caching Strategy

-   Campaign details: Cache for 5 minutes
-   Budget summary: Cache for 1 minute
-   Timeline: Cache for 5 minutes

## Background Tasks

### Celery Tasks (`app/tasks/campaign_tasks.py`)

```python
@celery_app.task
def check_approaching_deadlines():
    """Check for campaigns ending in 7 days and send reminders"""

@celery_app.task
def check_overdue_milestones():
    """Check for overdue milestones and send notifications"""

@celery_app.task
def update_campaign_progress():
    """Calculate and update campaign completion percentage"""
```

### Task Schedule

```python
# Celery Beat schedule
beat_schedule = {
    'check-deadlines': {
        'task': 'check_approaching_deadlines',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'check-milestones': {
        'task': 'check_overdue_milestones',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}
```
