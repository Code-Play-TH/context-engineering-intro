"""
Calendar and Scheduling Pydantic Schemas

Provides validation schemas for calendar and scheduling operations including:
- Event management and scheduling
- Content publication scheduling
- Meeting management and coordination
- Calendar synchronization and integrations
- Analytics and reporting
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class EventType(str, Enum):
    """Event type enumeration."""
    MEETING = "meeting"
    DEADLINE = "deadline"
    REMINDER = "reminder"
    CONTENT_REVIEW = "content_review"
    CAMPAIGN_LAUNCH = "campaign_launch"
    KOL_CALL = "kol_call"
    APPROVAL_DUE = "approval_due"
    CONTENT_PUBLISH = "content_publish"
    PERFORMANCE_REVIEW = "performance_review"


class EventStatus(str, Enum):
    """Event status enumeration."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"


class ContentType(str, Enum):
    """Content type enumeration."""
    POST = "post"
    STORY = "story"
    VIDEO = "video"
    REEL = "reel"
    LIVE = "live"
    ARTICLE = "article"
    PODCAST = "podcast"


class SocialPlatform(str, Enum):
    """Social media platform enumeration."""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITCH = "twitch"


class Priority(str, Enum):
    """Priority level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MeetingType(str, Enum):
    """Meeting type enumeration."""
    KICKOFF = "kickoff"
    REVIEW = "review"
    PLANNING = "planning"
    SYNC = "sync"
    PRESENTATION = "presentation"
    TRAINING = "training"
    ONE_ON_ONE = "one_on_one"


# Core Calendar Event Schemas
class CalendarEventBase(BaseModel):
    """Base schema for calendar events."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: EventType
    start_time: datetime
    end_time: datetime
    timezone: str = Field(default="UTC")
    location: Optional[str] = Field(None, max_length=500)
    is_virtual: bool = False
    meeting_link: Optional[str] = Field(None, max_length=500)
    attendees: List[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating calendar events."""
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    reminders: List[Dict[str, Any]] = Field(default_factory=list)
    recurrence: Optional[Dict[str, Any]] = None
    ignore_conflicts: bool = False


class CalendarEventUpdate(BaseModel):
    """Schema for updating calendar events."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: Optional[EventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    is_virtual: Optional[bool] = None
    meeting_link: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[str]] = None
    priority: Optional[Priority] = None
    status: Optional[EventStatus] = None
    reminders: Optional[List[Dict[str, Any]]] = None
    recurrence: Optional[Dict[str, Any]] = None
    ignore_conflicts: bool = False


class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event responses."""
    id: int
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    status: EventStatus
    reminders: List[Dict[str, Any]]
    recurrence: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Content Scheduling Schemas
class ContentScheduleBase(BaseModel):
    """Base schema for content scheduling."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    content_type: ContentType
    platform: SocialPlatform
    scheduled_time: datetime
    timezone: str = Field(default="UTC")


class ContentScheduleCreate(ContentScheduleBase):
    """Schema for creating content schedules."""
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    content_data: Dict[str, Any] = Field(default_factory=dict)
    media_urls: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    approval_required: bool = True
    auto_publish: bool = False


class ContentScheduleUpdate(BaseModel):
    """Schema for updating content schedules."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    scheduled_time: Optional[datetime] = None
    timezone: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None
    media_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    approval_required: Optional[bool] = None
    auto_publish: Optional[bool] = None
    status: Optional[str] = None


class ContentScheduleResponse(ContentScheduleBase):
    """Schema for content schedule responses."""
    id: int
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    content_data: Dict[str, Any]
    media_urls: List[str]
    hashtags: List[str]
    mentions: List[str]
    approval_required: bool
    auto_publish: bool
    status: str
    published_at: Optional[datetime] = None
    approval_status: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Meeting Management Schemas
class MeetingBase(BaseModel):
    """Base schema for meetings."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    meeting_type: MeetingType
    start_time: datetime
    end_time: datetime
    timezone: str = Field(default="UTC")
    location: Optional[str] = Field(None, max_length=500)
    is_virtual: bool = False
    meeting_link: Optional[str] = Field(None, max_length=500)
    attendees: List[str] = Field(default_factory=list)


class MeetingCreate(MeetingBase):
    """Schema for creating meetings."""
    campaign_id: Optional[int] = None
    agenda: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    preparation_notes: Optional[str] = Field(None, max_length=2000)
    ignore_conflicts: bool = False


class MeetingUpdate(BaseModel):
    """Schema for updating meetings."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    meeting_type: Optional[MeetingType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    is_virtual: Optional[bool] = None
    meeting_link: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[str]] = None
    agenda: Optional[List[Dict[str, Any]]] = None
    preparation_notes: Optional[str] = Field(None, max_length=2000)
    status: Optional[EventStatus] = None
    meeting_notes: Optional[str] = Field(None, max_length=5000)
    action_items: Optional[List[Dict[str, Any]]] = None


class MeetingResponse(MeetingBase):
    """Schema for meeting responses."""
    id: int
    campaign_id: Optional[int] = None
    agenda: List[Dict[str, Any]]
    preparation_notes: Optional[str] = None
    status: EventStatus
    meeting_notes: Optional[str] = None
    action_items: List[Dict[str, Any]]
    attendee_responses: Dict[str, str] = Field(default_factory=dict)
    recording_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Filter and Search Schemas
class CalendarFilters(BaseModel):
    """Schema for calendar filtering and search."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[EventType]] = None
    statuses: Optional[List[EventStatus]] = None
    priorities: Optional[List[Priority]] = None
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    attendee_id: Optional[str] = None
    location: Optional[str] = None
    is_virtual: Optional[bool] = None
    search_term: Optional[str] = None


# Analytics Schemas
class CalendarAnalytics(BaseModel):
    """Schema for calendar analytics."""
    date_range_start: datetime
    date_range_end: datetime
    total_events: int
    completed_events: int
    cancelled_events: int
    total_content_schedules: int
    published_content: int
    failed_content: int
    total_meetings: int
    completed_meetings: int
    utilization_rate: float = Field(ge=0, le=100)
    conflicts_detected: int
    generated_at: datetime


class SchedulingConflict(BaseModel):
    """Schema for scheduling conflicts."""
    event_id: int
    event_title: str
    start_time: datetime
    end_time: datetime
    conflicting_attendees: List[str]
    conflict_type: str


class CalendarInsights(BaseModel):
    """Schema for calendar insights and recommendations."""
    busiest_days: List[str]
    peak_hours: List[int]
    meeting_efficiency: float
    content_publishing_patterns: Dict[str, Any]
    recommendations: List[str]
    trends: Dict[str, Any]


# External Integration Schemas
class CalendarSyncRequest(BaseModel):
    """Schema for calendar synchronization requests."""
    provider: str = Field(..., pattern="^(google|outlook|apple|notion)$")
    sync_type: str = Field(..., pattern="^(import|export|bidirectional)$")
    calendar_ids: List[str] = Field(default_factory=list)
    sync_events: bool = True
    sync_meetings: bool = True
    sync_content_schedules: bool = False
    date_range: Optional[Dict[str, datetime]] = None
    auto_sync: bool = False
    sync_frequency: Optional[str] = Field(None, pattern="^(hourly|daily|weekly)$")


class CalendarSyncResponse(BaseModel):
    """Schema for calendar sync response."""
    sync_id: str
    status: str
    provider: str
    sync_type: str
    events_synced: int
    errors_count: int
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    sync_log: List[Dict[str, Any]] = Field(default_factory=list)


class CalendarExportRequest(BaseModel):
    """Schema for calendar export requests."""
    format: str = Field(..., pattern="^(ical|csv|json|pdf)$")
    date_range: Dict[str, datetime]
    include_events: bool = True
    include_meetings: bool = True
    include_content_schedules: bool = True
    filters: Optional[CalendarFilters] = None
    timezone: str = Field(default="UTC")


class CalendarExportResponse(BaseModel):
    """Schema for calendar export response."""
    export_id: str
    format: str
    status: str
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


# Notification and Reminder Schemas
class ReminderConfig(BaseModel):
    """Schema for reminder configuration."""
    type: str = Field(..., pattern="^(email|sms|push|webhook)$")
    timing: int = Field(..., description="Minutes before event")
    recipients: List[str] = Field(default_factory=list)
    message_template: Optional[str] = None
    is_active: bool = True


class NotificationPreferences(BaseModel):
    """Schema for notification preferences."""
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    webhook_enabled: bool = False
    reminder_timings: List[int] = Field(default_factory=lambda: [60, 15])  # minutes
    quiet_hours: Optional[Dict[str, str]] = None
    timezone: str = Field(default="UTC")


# Bulk Operations Schemas
class BulkEventAction(BaseModel):
    """Schema for bulk event actions."""
    event_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(update|cancel|reschedule|delete)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BulkEventResponse(BaseModel):
    """Schema for bulk event operation response."""
    success_count: int
    failed_count: int
    failed_events: List[Dict[str, Any]] = Field(default_factory=list)
    processed_events: List[int] = Field(default_factory=list)


# Recurrence and Pattern Schemas
class RecurrencePattern(BaseModel):
    """Schema for event recurrence patterns."""
    pattern_type: str = Field(..., pattern="^(daily|weekly|monthly|yearly|custom)$")
    interval: int = Field(default=1, ge=1)
    days_of_week: Optional[List[int]] = Field(None, description="0=Monday, 6=Sunday")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    month_of_year: Optional[int] = Field(None, ge=1, le=12)
    end_date: Optional[datetime] = None
    occurrence_count: Optional[int] = Field(None, ge=1)
    exceptions: List[datetime] = Field(default_factory=list)


class RecurrenceInstance(BaseModel):
    """Schema for individual recurrence instances."""
    parent_event_id: int
    instance_date: datetime
    is_modified: bool = False
    is_cancelled: bool = False
    modifications: Dict[str, Any] = Field(default_factory=dict)


# Calendar View and Display Schemas
class CalendarView(BaseModel):
    """Schema for calendar view configurations."""
    view_type: str = Field(..., pattern="^(day|week|month|year|agenda)$")
    start_date: datetime
    end_date: datetime
    timezone: str = Field(default="UTC")
    filters: Optional[CalendarFilters] = None
    group_by: Optional[str] = Field(None, pattern="^(campaign|kol|priority|type)$")


class CalendarViewResponse(BaseModel):
    """Schema for calendar view response."""
    view_type: str
    date_range: Dict[str, datetime]
    events: List[CalendarEventResponse]
    content_schedules: List[ContentScheduleResponse]
    meetings: List[MeetingResponse]
    summary: Dict[str, Any]
    conflicts: List[SchedulingConflict] = Field(default_factory=list)


# Time Zone and Availability Schemas
class TimeZoneInfo(BaseModel):
    """Schema for timezone information."""
    timezone: str
    offset: str
    display_name: str
    is_dst: bool


class AvailabilitySlot(BaseModel):
    """Schema for availability slots."""
    start_time: datetime
    end_time: datetime
    is_available: bool
    conflict_reason: Optional[str] = None
    suggested_alternatives: List[datetime] = Field(default_factory=list)


class AvailabilityRequest(BaseModel):
    """Schema for availability checking."""
    attendees: List[str]
    duration_minutes: int = Field(ge=15, le=480)
    preferred_times: List[datetime] = Field(default_factory=list)
    date_range: Dict[str, datetime]
    timezone: str = Field(default="UTC")
    working_hours_only: bool = True


class AvailabilityResponse(BaseModel):
    """Schema for availability response."""
    available_slots: List[AvailabilitySlot]
    suggested_times: List[datetime]
    conflicts: List[SchedulingConflict]
    attendee_availability: Dict[str, List[AvailabilitySlot]]