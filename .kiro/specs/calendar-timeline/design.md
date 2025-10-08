# Design Document - Calendar & Timeline Management

## Overview

The Calendar & Timeline Management system provides project visualization, KOL availability scheduling, deadline tracking, milestone management, and team workload balancing across campaigns.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Calendar    │◀─────│   Calendar   │◀─────│  Database   │
│  View        │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Celery Beat  │
                     │  (Deadline   │
                     │  Reminders)  │
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class TimelineService:
    async def get_campaign_timeline(campaign_id: int) -> Timeline
    async def update_timeline(campaign_id: int, timeline_data: TimelineUpdate) -> Timeline
    async def check_timeline_conflicts(campaign_id: int) -> List[Conflict]

class AvailabilityService:
    async def get_kol_availability(kol_id: int, start_date: date, end_date: date) -> List[AvailabilitySlot]
    async def set_kol_unavailable(kol_id: int, start_date: date, end_date: date, reason: str) -> None
    async def check_kol_conflicts(kol_id: int, campaign_id: int) -> List[Conflict]
    async def get_kol_capacity(kol_id: int) -> CapacityInfo

class DeadlineService:
    async def create_deadline(campaign_id: int, deadline_data: DeadlineCreate) -> Deadline
    async def get_upcoming_deadlines(user_id: int) -> List[Deadline]
    async def check_overdue_deadlines() -> List[Deadline]
    async def send_deadline_reminders() -> None

class WorkloadService:
    async def get_team_workload() -> List[UserWorkload]
    async def get_user_workload(user_id: int) -> UserWorkload
    async def calculate_capacity_utilization(user_id: int) -> float
    async def suggest_assignments(campaign_id: int) -> List[UserSuggestion]

class CalendarSyncService:
    async def sync_to_google_calendar(user_id: int, campaign_id: int) -> None
    async def sync_to_outlook(user_id: int, campaign_id: int) -> None
    async def disconnect_calendar_sync(user_id: int) -> None
```

## Data Models

### Timeline Model (extends Campaign)

```python
# Timeline is represented through Campaign dates and Milestones
# No separate table needed, uses existing Campaign and Milestone models
```

### KOLAvailability Model

```python
class KOLAvailability(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    start_date: date
    end_date: date
    is_available: bool = Field(default=True)
    reason: Optional[str]  # vacation, other_campaign, personal
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Deadline Model

```python
class Deadline(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    title: str
    description: Optional[str]
    due_date: date = Field(index=True)
    priority: str  # low, medium, high, critical
    status: str  # upcoming, today, overdue, completed
    responsible_user_id: int = Field(foreign_key="user.id")
    completed_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### RecurringEvent Model

```python
class RecurringEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    description: Optional[str]
    frequency: str  # daily, weekly, monthly
    day_of_week: Optional[int]  # 0-6 for weekly
    day_of_month: Optional[int]  # 1-31 for monthly
    time: time
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### CalendarSync Model

```python
class CalendarSync(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    provider: str  # google, outlook, apple
    access_token: str  # Encrypted
    refresh_token: str  # Encrypted
    calendar_id: str
    is_active: bool = Field(default=True)
    last_synced_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## API Endpoints

```python
# Timeline
GET    /api/v1/campaigns/{id}/timeline                # Get campaign timeline
PUT    /api/v1/campaigns/{id}/timeline                # Update timeline
GET    /api/v1/campaigns/{id}/timeline/conflicts      # Check conflicts

# KOL Availability
GET    /api/v1/kols/{id}/availability                 # Get availability
POST   /api/v1/kols/{id}/availability/block           # Block dates
DELETE /api/v1/kols/{id}/availability/{block_id}      # Remove block
GET    /api/v1/kols/{id}/capacity                     # Get capacity info

# Deadlines
POST   /api/v1/campaigns/{id}/deadlines               # Create deadline
GET    /api/v1/deadlines                              # Get all deadlines (filtered)
GET    /api/v1/deadlines/upcoming                     # Get upcoming deadlines
PUT    /api/v1/deadlines/{id}                         # Update deadline
POST   /api/v1/deadlines/{id}/complete                # Mark as complete

# Calendar View
GET    /api/v1/calendar                               # Get unified calendar
GET    /api/v1/calendar/team                          # Get team calendar
GET    /api/v1/calendar/export                        # Export as iCal

# Workload
GET    /api/v1/workload/team                          # Get team workload
GET    /api/v1/workload/user/{id}                     # Get user workload
GET    /api/v1/campaigns/{id}/suggest-assignments     # Suggest team members

# Recurring Events
POST   /api/v1/recurring-events                       # Create recurring event
GET    /api/v1/recurring-events                       # List recurring events
PUT    /api/v1/recurring-events/{id}                  # Update recurring event
DELETE /api/v1/recurring-events/{id}                  # Delete recurring event

# Calendar Sync
POST   /api/v1/calendar-sync/google                   # Connect Google Calendar
POST   /api/v1/calendar-sync/outlook                  # Connect Outlook
DELETE /api/v1/calendar-sync                          # Disconnect sync
GET    /api/v1/calendar-sync/status                   # Get sync status
```

## Timeline Visualization

### Gantt Chart Data Structure

```python
def get_campaign_timeline_data(campaign_id: int) -> dict:
    """Get timeline data for Gantt chart"""
    campaign = get_campaign(campaign_id)
    milestones = get_campaign_milestones(campaign_id)

    return {
        'campaign': {
            'id': campaign.id,
            'name': campaign.name,
            'start_date': campaign.start_date,
            'end_date': campaign.end_date,
            'progress': calculate_campaign_progress(campaign_id)
        },
        'phases': [
            {
                'name': 'Brief Creation',
                'start': campaign.start_date,
                'end': campaign.start_date + timedelta(days=7),
                'status': 'completed'
            },
            {
                'name': 'KOL Selection',
                'start': campaign.start_date + timedelta(days=7),
                'end': campaign.start_date + timedelta(days=14),
                'status': 'in_progress'
            },
            # ... more phases
        ],
        'milestones': [
            {
                'id': m.id,
                'name': m.name,
                'date': m.due_date,
                'status': m.status,
                'responsible': m.responsible_user.full_name
            }
            for m in milestones
        ]
    }
```

## Availability Management

### Check KOL Conflicts

```python
async def check_kol_conflicts(kol_id: int, start_date: date, end_date: date) -> List[Conflict]:
    """Check if KOL has conflicts in date range"""
    conflicts = []

    # Check existing campaigns
    existing_campaigns = await get_kol_campaigns(kol_id, start_date, end_date)
    for campaign in existing_campaigns:
        if campaign.status == 'active':
            conflicts.append(Conflict(
                type='campaign',
                campaign_id=campaign.id,
                campaign_name=campaign.name,
                start_date=campaign.start_date,
                end_date=campaign.end_date
            ))

    # Check blocked dates
    blocked_dates = await get_kol_blocked_dates(kol_id, start_date, end_date)
    for block in blocked_dates:
        conflicts.append(Conflict(
            type='unavailable',
            reason=block.reason,
            start_date=block.start_date,
            end_date=block.end_date
        ))

    return conflicts
```

### Calculate Capacity

```python
async def calculate_kol_capacity(kol_id: int) -> CapacityInfo:
    """Calculate KOL's current capacity"""
    max_concurrent_campaigns = 3  # Configurable per KOL

    active_campaigns = await get_active_campaigns_count(kol_id)
    utilization = (active_campaigns / max_concurrent_campaigns) * 100

    return CapacityInfo(
        max_campaigns=max_concurrent_campaigns,
        active_campaigns=active_campaigns,
        available_slots=max_concurrent_campaigns - active_campaigns,
        utilization_percentage=utilization,
        status='available' if active_campaigns < max_concurrent_campaigns else 'full'
    )
```

## Deadline Management

### Deadline Reminders

```python
@celery_app.task
def send_deadline_reminders():
    """Send reminders for upcoming deadlines"""
    # 3 days before
    deadlines_3days = get_deadlines_in_days(3)
    for deadline in deadlines_3days:
        send_notification(
            user_id=deadline.responsible_user_id,
            message=f"Reminder: {deadline.title} is due in 3 days",
            priority='normal'
        )

    # Today
    deadlines_today = get_deadlines_today()
    for deadline in deadlines_today:
        send_notification(
            user_id=deadline.responsible_user_id,
            message=f"Urgent: {deadline.title} is due today!",
            priority='high'
        )

    # Overdue
    overdue_deadlines = get_overdue_deadlines()
    for deadline in overdue_deadlines:
        # Escalate to manager
        campaign = get_campaign(deadline.campaign_id)
        manager = get_campaign_manager(campaign.id)

        send_notification(
            user_id=manager.id,
            message=f"Overdue: {deadline.title} was due on {deadline.due_date}",
            priority='critical'
        )
```

## Workload Management

### Calculate Team Workload

```python
async def calculate_team_workload() -> List[UserWorkload]:
    """Calculate workload for all team members"""
    users = await get_all_users()
    workloads = []

    for user in users:
        active_campaigns = await get_user_active_campaigns(user.id)
        pending_tasks = await get_user_pending_tasks(user.id)

        # Calculate capacity (assume 3 campaigns = 100% capacity)
        capacity_utilization = (len(active_campaigns) / 3) * 100

        workloads.append(UserWorkload(
            user_id=user.id,
            user_name=user.full_name,
            active_campaigns=len(active_campaigns),
            pending_tasks=len(pending_tasks),
            capacity_utilization=capacity_utilization,
            status='overloaded' if capacity_utilization > 100 else
                   'optimal' if 50 <= capacity_utilization <= 100 else
                   'underutilized'
        ))

    return workloads
```

### Suggest Assignments

```python
async def suggest_team_assignments(campaign_id: int) -> List[UserSuggestion]:
    """Suggest team members for campaign assignment"""
    workloads = await calculate_team_workload()
    campaign = await get_campaign(campaign_id)

    # Filter users with capacity
    available_users = [w for w in workloads if w.capacity_utilization < 100]

    # Sort by utilization (prefer balanced distribution)
    available_users.sort(key=lambda w: w.capacity_utilization)

    suggestions = []
    for workload in available_users[:5]:  # Top 5 suggestions
        user = await get_user(workload.user_id)

        suggestions.append(UserSuggestion(
            user_id=user.id,
            user_name=user.full_name,
            role=user.role,
            current_utilization=workload.capacity_utilization,
            reason=f"Available capacity: {100 - workload.capacity_utilization:.0f}%"
        ))

    return suggestions
```

## Calendar Sync

### Google Calendar Integration

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

async def sync_to_google_calendar(user_id: int, campaign_id: int):
    """Sync campaign events to Google Calendar"""
    sync_config = await get_calendar_sync(user_id)

    credentials = Credentials(
        token=decrypt(sync_config.access_token),
        refresh_token=decrypt(sync_config.refresh_token)
    )

    service = build('calendar', 'v3', credentials=credentials)

    campaign = await get_campaign(campaign_id)
    milestones = await get_campaign_milestones(campaign_id)

    # Create campaign event
    event = {
        'summary': f"Campaign: {campaign.name}",
        'description': campaign.objectives,
        'start': {'date': campaign.start_date.isoformat()},
        'end': {'date': campaign.end_date.isoformat()},
        'colorId': '9'  # Blue
    }

    service.events().insert(calendarId=sync_config.calendar_id, body=event).execute()

    # Create milestone events
    for milestone in milestones:
        event = {
            'summary': f"Milestone: {milestone.name}",
            'start': {'date': milestone.due_date.isoformat()},
            'end': {'date': milestone.due_date.isoformat()},
            'colorId': '11'  # Red
        }

        service.events().insert(calendarId=sync_config.calendar_id, body=event).execute()

    sync_config.last_synced_at = datetime.now()
    await save_calendar_sync(sync_config)
```

## Performance Considerations

### Database Indexes

```sql
CREATE INDEX idx_kol_availability_kol_dates ON kolavailability(kol_id, start_date, end_date);
CREATE INDEX idx_deadline_due_date ON deadline(due_date) WHERE status != 'completed';
CREATE INDEX idx_deadline_user ON deadline(responsible_user_id, status);
```

### Caching

-   Timeline data: Cache for 5 minutes
-   Workload calculations: Cache for 10 minutes
-   Availability: Cache for 1 hour

## Testing Strategy

### Unit Tests

-   Conflict detection logic
-   Capacity calculation
-   Workload distribution
-   Deadline reminder logic

### Integration Tests

-   End-to-end timeline management
-   Calendar sync workflow
-   Deadline notifications
-   Team assignment suggestions
