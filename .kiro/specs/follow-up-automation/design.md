# Design Document - Follow-up Automation

## Overview

The Follow-up Automation system manages scheduled reminders and automated follow-ups with KOLs at configurable intervals with smart timing, escalation rules, and performance tracking.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Follow-up   │◀─────│   Follow-up  │◀─────│  Database   │
│  Dashboard   │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Celery Beat  │
                     │  (Scheduler) │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Communication│
                     │   Service    │
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class FollowUpService:
    async def schedule_follow_ups(message_id: int, intervals: List[int]) -> List[FollowUp]
    async def cancel_follow_ups(message_id: int) -> None
    async def send_follow_up(follow_up_id: int) -> None
    async def skip_follow_up(follow_up_id: int, reason: str) -> None
    async def reschedule_follow_up(follow_up_id: int, new_date: datetime) -> FollowUp

class EscalationService:
    async def check_escalation_rules(follow_up_id: int) -> bool
    async def escalate_to_manager(follow_up_id: int) -> None
    async def get_escalations(user_id: int) -> List[Escalation]

class FollowUpAnalyticsService:
    async def get_response_rates_by_interval() -> Dict[int, float]
    async def get_template_effectiveness() -> List[TemplateStats]
    async def get_user_performance(user_id: int) -> UserPerformance
```

## Data Models

### FollowUp Model

```python
class FollowUp(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    original_message_id: int = Field(foreign_key="message.id", index=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    campaign_id: Optional[int] = Field(foreign_key="campaign.id")
    follow_up_number: int  # 1, 2, 3
    scheduled_at: datetime = Field(index=True)
    status: str  # scheduled, sent, skipped, cancelled
    sent_at: Optional[datetime]
    skipped_reason: Optional[str]
    template_id: Optional[int] = Field(foreign_key="messagetemplate.id")
    assigned_to: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### FollowUpRule Model

```python
class FollowUpRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(foreign_key="campaign.id")  # Campaign-specific or global
    intervals: List[int] = Field(sa_column=Column(ARRAY(Integer)))  # [1, 3, 5] days
    max_follow_ups: int = Field(default=3)
    escalate_after: int = Field(default=3)  # Escalate after N follow-ups
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Escalation Model

```python
class Escalation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    follow_up_id: int = Field(foreign_key="followup.id")
    kol_id: int = Field(foreign_key="kol.id")
    campaign_id: int = Field(foreign_key="campaign.id")
    escalated_from: int = Field(foreign_key="user.id")
    escalated_to: int = Field(foreign_key="user.id")
    reason: str
    status: str  # pending, resolved, dismissed
    resolved_at: Optional[datetime]
    resolution_action: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
```

## API Endpoints

```python
# Follow-up Management
GET    /api/v1/follow-ups                            # Get all follow-ups (filtered)
GET    /api/v1/follow-ups/{id}                       # Get follow-up details
POST   /api/v1/follow-ups/{id}/send                  # Send follow-up immediately
POST   /api/v1/follow-ups/{id}/skip                  # Skip follow-up
PUT    /api/v1/follow-ups/{id}/reschedule            # Reschedule follow-up
DELETE /api/v1/follow-ups/{id}                       # Cancel follow-up

# Follow-up Rules
GET    /api/v1/follow-up-rules                       # Get rules
POST   /api/v1/follow-up-rules                       # Create rule
PUT    /api/v1/follow-up-rules/{id}                  # Update rule
GET    /api/v1/campaigns/{id}/follow-up-rules        # Get campaign-specific rules

# Escalations
GET    /api/v1/escalations                           # Get escalations
GET    /api/v1/escalations/{id}                      # Get escalation details
POST   /api/v1/escalations/{id}/resolve              # Resolve escalation
POST   /api/v1/escalations/{id}/dismiss              # Dismiss escalation

# Analytics
GET    /api/v1/follow-ups/analytics/response-rates   # Response rates by interval
GET    /api/v1/follow-ups/analytics/templates        # Template effectiveness
GET    /api/v1/follow-ups/analytics/user-performance # User performance
```

## Follow-up Scheduling

### Auto-schedule on Message Send

```python
async def schedule_follow_ups_on_send(message_id: int, kol_id: int, campaign_id: int):
    """Automatically schedule follow-ups when message is sent"""
    # Get follow-up rules
    rules = await get_follow_up_rules(campaign_id)
    if not rules:
        rules = await get_default_follow_up_rules()

    message = await get_message(message_id)

    for i, interval_days in enumerate(rules.intervals, start=1):
        scheduled_at = message.sent_at + timedelta(days=interval_days)

        follow_up = FollowUp(
            original_message_id=message_id,
            kol_id=kol_id,
            campaign_id=campaign_id,
            follow_up_number=i,
            scheduled_at=scheduled_at,
            status="scheduled",
            assigned_to=message.sent_by
        )

        await save_follow_up(follow_up)
```

### Cancel on Response

```python
async def cancel_follow_ups_on_response(message_id: int):
    """Cancel pending follow-ups when KOL responds"""
    follow_ups = await get_pending_follow_ups(message_id)

    for follow_up in follow_ups:
        follow_up.status = "cancelled"
        await save_follow_up(follow_up)
```

## Smart Timing

### Optimal Send Time

```python
async def calculate_optimal_send_time(kol_id: int, scheduled_at: datetime) -> datetime:
    """Calculate optimal send time based on KOL behavior"""
    # Get KOL's historical response patterns
    response_history = await get_kol_response_history(kol_id)

    if response_history:
        # Find most common response hour
        response_hours = [r.responded_at.hour for r in response_history]
        optimal_hour = max(set(response_hours), key=response_hours.count)
    else:
        optimal_hour = 10  # Default to 10 AM

    # Get KOL timezone
    kol = await get_kol(kol_id)
    prefs = await get_communication_preferences(kol_id)
    tz = pytz.timezone(prefs.timezone)

    # Adjust scheduled time to optimal hour in KOL's timezone
    optimal_time = scheduled_at.replace(hour=optimal_hour, minute=0, second=0)

    # Check if it's weekend, move to Monday
    if optimal_time.weekday() >= 5:  # Saturday or Sunday
        days_to_monday = 7 - optimal_time.weekday()
        optimal_time += timedelta(days=days_to_monday)

    # Check Do Not Disturb hours
    if prefs.do_not_disturb_hours:
        start_hour, end_hour = parse_dnd_hours(prefs.do_not_disturb_hours)
        if start_hour <= optimal_hour < end_hour:
            optimal_time = optimal_time.replace(hour=end_hour)

    return optimal_time
```

## Escalation Logic

### Check Escalation Rules

```python
async def check_and_escalate(follow_up: FollowUp):
    """Check if follow-up should be escalated"""
    rules = await get_follow_up_rules(follow_up.campaign_id)

    # Check if max follow-ups reached
    if follow_up.follow_up_number >= rules.escalate_after:
        # Check if KOL still hasn't responded
        original_message = await get_message(follow_up.original_message_id)
        if not original_message.responded_at:
            await escalate_to_manager(follow_up)

    # Check deadline proximity
    campaign = await get_campaign(follow_up.campaign_id)
    days_until_deadline = (campaign.end_date - datetime.now().date()).days

    if days_until_deadline <= 3 and not original_message.responded_at:
        await escalate_to_manager(follow_up, reason="Deadline approaching")
```

### Escalate to Manager

```python
async def escalate_to_manager(follow_up: FollowUp, reason: str = "No response after max follow-ups"):
    """Escalate follow-up to Campaign Manager"""
    campaign = await get_campaign(follow_up.campaign_id)
    manager = await get_campaign_manager(campaign.id)

    escalation = Escalation(
        follow_up_id=follow_up.id,
        kol_id=follow_up.kol_id,
        campaign_id=follow_up.campaign_id,
        escalated_from=follow_up.assigned_to,
        escalated_to=manager.id,
        reason=reason,
        status="pending"
    )

    await save_escalation(escalation)

    # Send notification to manager
    await send_escalation_notification(manager.id, escalation)
```

## Background Tasks

### Celery Tasks

```python
@celery_app.task
def process_due_follow_ups():
    """Process follow-ups that are due"""
    due_follow_ups = get_due_follow_ups()

    for follow_up in due_follow_ups:
        try:
            # Calculate optimal send time
            optimal_time = calculate_optimal_send_time(follow_up.kol_id, follow_up.scheduled_at)

            if datetime.now() >= optimal_time:
                send_follow_up_message(follow_up.id)
            else:
                # Reschedule to optimal time
                reschedule_follow_up(follow_up.id, optimal_time)
        except Exception as e:
            logger.error(f"Failed to process follow-up {follow_up.id}: {e}")

@celery_app.task
def check_escalations():
    """Check for follow-ups that need escalation"""
    follow_ups = get_follow_ups_for_escalation_check()

    for follow_up in follow_ups:
        check_and_escalate(follow_up)

@celery_app.task
def send_follow_up_reminders():
    """Send reminders to users about due follow-ups"""
    users = get_users_with_due_follow_ups()

    for user in users:
        follow_ups = get_user_due_follow_ups(user.id)
        send_follow_up_reminder_notification(user.id, follow_ups)
```

### Celery Beat Schedule

```python
beat_schedule = {
    'process-follow-ups': {
        'task': 'process_due_follow_ups',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'check-escalations': {
        'task': 'check_escalations',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'send-reminders': {
        'task': 'send_follow_up_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}
```

## Analytics

### Response Rate by Interval

```python
async def calculate_response_rates_by_interval() -> Dict[int, float]:
    """Calculate response rates for each follow-up interval"""
    follow_ups = await get_all_sent_follow_ups()

    rates = {}
    for interval in [1, 2, 3, 5, 7]:
        interval_follow_ups = [f for f in follow_ups if f.follow_up_number == interval]

        if interval_follow_ups:
            responded = len([f for f in interval_follow_ups if f.original_message.responded_at])
            rates[interval] = (responded / len(interval_follow_ups)) * 100
        else:
            rates[interval] = 0

    return rates
```

## Performance Considerations

### Database Indexes

```sql
CREATE INDEX idx_follow_up_scheduled ON followup(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_follow_up_kol ON followup(kol_id);
CREATE INDEX idx_escalation_status ON escalation(status, created_at DESC);
```

### Caching

-   Follow-up rules: Cache for 1 hour
-   User assignments: Cache for 5 minutes
-   Analytics: Cache for 15 minutes

## Testing Strategy

### Unit Tests

-   Follow-up scheduling logic
-   Optimal time calculation
-   Escalation rules
-   Response rate calculation

### Integration Tests

-   End-to-end follow-up flow
-   Auto-cancellation on response
-   Escalation workflow
-   Smart timing adjustments
