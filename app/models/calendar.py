"""
Calendar and Scheduling Database Models

SQLAlchemy models for calendar, scheduling, and event management functionality.
Supports event management, content scheduling, meetings, and calendar integrations.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CalendarEvent(Base):
    """
    Calendar event model for managing various types of events and deadlines.
    """
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False, index=True)  # meeting, deadline, reminder, etc.

    # Timing information
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), nullable=False, default="UTC")

    # Location and meeting details
    location = Column(String(500), nullable=True)
    is_virtual = Column(Boolean, default=False)
    meeting_link = Column(String(500), nullable=True)

    # Attendees and participants
    attendees = Column(JSON, default=list)  # List of user/KOL IDs

    # Relationships
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    kol_id = Column(Integer, ForeignKey("kols.id"), nullable=True, index=True)

    # Priority and status
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(20), default="scheduled", index=True)  # scheduled, confirmed, completed, cancelled

    # Recurrence and reminders
    recurrence = Column(JSON, nullable=True)  # Recurrence pattern configuration
    reminders = Column(JSON, default=list)   # Reminder configurations

    # Metadata and tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="calendar_events")
    kol = relationship("KOL", back_populates="calendar_events")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', type='{self.event_type}')>"


class ContentSchedule(Base):
    """
    Content scheduling model for managing when content should be published.
    """
    __tablename__ = "content_schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Content details
    content_type = Column(String(50), nullable=False)  # post, story, video, reel, etc.
    platform = Column(String(50), nullable=False, index=True)  # instagram, youtube, tiktok, etc.

    # Scheduling information
    scheduled_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), nullable=False, default="UTC")

    # Relationships
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    kol_id = Column(Integer, ForeignKey("kols.id"), nullable=True, index=True)

    # Content data
    content_data = Column(JSON, default=dict)  # Content text, captions, etc.
    media_urls = Column(JSON, default=list)    # URLs to media files
    hashtags = Column(JSON, default=list)      # List of hashtags
    mentions = Column(JSON, default=list)      # List of mentions

    # Publishing configuration
    approval_required = Column(Boolean, default=True)
    auto_publish = Column(Boolean, default=False)

    # Status tracking
    status = Column(String(20), default="scheduled", index=True)  # scheduled, approved, published, failed
    published_at = Column(DateTime, nullable=True)

    # Approval workflow
    approval_status = Column(String(20), nullable=True)  # pending, approved, rejected
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Publishing results
    published_post_id = Column(String(100), nullable=True)  # ID from social platform
    engagement_data = Column(JSON, nullable=True)          # Engagement metrics after publishing

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="content_schedules")
    kol = relationship("KOL", back_populates="content_schedules")

    def __repr__(self):
        return f"<ContentSchedule(id={self.id}, title='{self.title}', platform='{self.platform}')>"


class Meeting(Base):
    """
    Meeting model for managing meetings, calls, and collaborative sessions.
    """
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    meeting_type = Column(String(50), nullable=False)  # kickoff, review, planning, sync, etc.

    # Timing information
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), nullable=False, default="UTC")

    # Location and meeting details
    location = Column(String(500), nullable=True)
    is_virtual = Column(Boolean, default=True)
    meeting_link = Column(String(500), nullable=True)
    meeting_password = Column(String(100), nullable=True)

    # Participants
    attendees = Column(JSON, default=list)  # List of user/KOL IDs

    # Campaign relationship
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)

    # Meeting content
    agenda = Column(JSON, default=list)           # Meeting agenda items
    preparation_notes = Column(Text, nullable=True)

    # Status and results
    status = Column(String(20), default="scheduled", index=True)  # scheduled, in_progress, completed, cancelled
    meeting_notes = Column(Text, nullable=True)   # Post-meeting notes
    action_items = Column(JSON, default=list)     # Action items from meeting

    # Attendee management
    attendee_responses = Column(JSON, default=dict)  # Attendee RSVP responses
    actual_attendees = Column(JSON, default=list)    # Who actually attended

    # Recording and resources
    recording_url = Column(String(500), nullable=True)
    shared_resources = Column(JSON, default=list)  # Shared files, links, etc.

    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="meetings")

    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', type='{self.meeting_type}')>"


class CalendarIntegration(Base):
    """
    Calendar integration model for managing external calendar synchronization.
    """
    __tablename__ = "calendar_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # User who owns the integration

    # Integration details
    provider = Column(String(50), nullable=False)  # google, outlook, apple, notion
    provider_calendar_id = Column(String(200), nullable=False)
    calendar_name = Column(String(200), nullable=True)

    # Sync configuration
    sync_type = Column(String(20), default="import")  # import, export, bidirectional
    sync_events = Column(Boolean, default=True)
    sync_meetings = Column(Boolean, default=True)
    sync_content_schedules = Column(Boolean, default=False)

    # Authentication
    access_token = Column(Text, nullable=True)      # Encrypted access token
    refresh_token = Column(Text, nullable=True)     # Encrypted refresh token
    token_expires_at = Column(DateTime, nullable=True)

    # Sync status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(20), nullable=True)  # success, failed, partial
    last_sync_error = Column(Text, nullable=True)
    sync_frequency = Column(String(20), default="daily")  # hourly, daily, weekly

    # Filtering and mapping
    sync_filters = Column(JSON, default=dict)      # Filters for what to sync
    field_mappings = Column(JSON, default=dict)    # How to map fields between systems

    # Statistics
    events_synced = Column(Integer, default=0)
    sync_conflicts = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CalendarIntegration(id={self.id}, provider='{self.provider}', user_id={self.user_id})>"


class EventReminder(Base):
    """
    Event reminder model for managing automated reminders and notifications.
    """
    __tablename__ = "event_reminders"

    id = Column(Integer, primary_key=True, index=True)

    # Event relationship
    event_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=True)
    content_schedule_id = Column(Integer, ForeignKey("content_schedules.id"), nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)

    # Reminder configuration
    reminder_type = Column(String(20), nullable=False)  # email, sms, push, webhook
    timing_minutes = Column(Integer, nullable=False)    # Minutes before event
    recipients = Column(JSON, default=list)             # Who to remind

    # Message configuration
    subject = Column(String(200), nullable=True)
    message_template = Column(Text, nullable=True)
    custom_message = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(20), default="scheduled")  # scheduled, sent, failed, cancelled
    scheduled_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)

    # Delivery tracking
    delivery_status = Column(JSON, default=dict)    # Status per recipient
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    event = relationship("CalendarEvent", backref="reminders")
    content_schedule = relationship("ContentSchedule", backref="reminders")
    meeting = relationship("Meeting", backref="reminders")

    def __repr__(self):
        return f"<EventReminder(id={self.id}, type='{self.reminder_type}', timing={self.timing_minutes}min)>"


class RecurringEventSeries(Base):
    """
    Recurring event series model for managing recurring events and their instances.
    """
    __tablename__ = "recurring_event_series"

    id = Column(Integer, primary_key=True, index=True)

    # Series configuration
    series_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Pattern configuration
    pattern_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly, custom
    interval_value = Column(Integer, default=1)        # Every N intervals
    days_of_week = Column(JSON, nullable=True)         # For weekly patterns [0-6]
    day_of_month = Column(Integer, nullable=True)      # For monthly patterns
    month_of_year = Column(Integer, nullable=True)     # For yearly patterns

    # Series limits
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    max_occurrences = Column(Integer, nullable=True)

    # Template for instances
    event_template = Column(JSON, nullable=False)      # Template for creating instances

    # Status
    is_active = Column(Boolean, default=True)
    last_generated = Column(DateTime, nullable=True)   # Last time instances were generated

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<RecurringEventSeries(id={self.id}, name='{self.series_name}', pattern='{self.pattern_type}')>"


class EventException(Base):
    """
    Event exception model for managing exceptions to recurring events.
    """
    __tablename__ = "event_exceptions"

    id = Column(Integer, primary_key=True, index=True)

    # Series relationship
    series_id = Column(Integer, ForeignKey("recurring_event_series.id"), nullable=False)

    # Exception details
    exception_date = Column(DateTime, nullable=False)  # Date of the exception
    exception_type = Column(String(20), nullable=False)  # cancelled, modified, moved

    # Modified event data (if exception_type is 'modified')
    modified_event_data = Column(JSON, nullable=True)

    # New date (if exception_type is 'moved')
    new_date = Column(DateTime, nullable=True)

    # Reason for exception
    reason = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)

    # Relationships
    series = relationship("RecurringEventSeries", backref="exceptions")

    def __repr__(self):
        return f"<EventException(id={self.id}, series_id={self.series_id}, type='{self.exception_type}')>"


class CalendarPermission(Base):
    """
    Calendar permission model for managing access control to calendar items.
    """
    __tablename__ = "calendar_permissions"

    id = Column(Integer, primary_key=True, index=True)

    # Resource identification
    resource_type = Column(String(50), nullable=False)  # event, meeting, schedule
    resource_id = Column(Integer, nullable=False)

    # Permission target
    user_id = Column(Integer, nullable=True)    # Specific user
    role = Column(String(50), nullable=True)    # Or role-based

    # Permission levels
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_manage_attendees = Column(Boolean, default=False)

    # Conditions
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<CalendarPermission(id={self.id}, resource={self.resource_type}:{self.resource_id})>"