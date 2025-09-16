"""
Calendar and Scheduling API Endpoints

Provides comprehensive calendar and scheduling functionality:
- Event management and scheduling
- Content publishing schedules
- Meeting and deadline tracking
- Campaign timeline management
- Calendar synchronization and integrations
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.calendar import CalendarEvent, ContentSchedule, Meeting
from app.models.campaigns import Campaign, CampaignContent
from app.models.kols import KOL
from app.schemas.calendar import (
    CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse,
    ContentScheduleCreate, ContentScheduleUpdate, ContentScheduleResponse,
    MeetingCreate, MeetingUpdate, MeetingResponse,
    CalendarFilters, CalendarAnalytics, SchedulingConflict,
    CalendarSyncRequest, CalendarExportRequest
)
from app.tasks.calendar import schedule_content_publication, send_calendar_reminders
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["Calendar & Scheduling"])


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: CalendarEventCreate,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CalendarEventResponse:
    """
    Create a new calendar event.

    Args:
        event_data: Event creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created event details
    """
    try:
        # Check for scheduling conflicts
        conflicts = await _check_scheduling_conflicts(
            db, event_data.start_time, event_data.end_time,
            event_data.attendees, exclude_event_id=None
        )

        if conflicts and not event_data.ignore_conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Scheduling conflicts detected",
                    "conflicts": conflicts
                }
            )

        # Create event
        event = CalendarEvent(
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            timezone=event_data.timezone,
            location=event_data.location,
            is_virtual=event_data.is_virtual,
            meeting_link=event_data.meeting_link,
            attendees=event_data.attendees,
            campaign_id=event_data.campaign_id,
            kol_id=event_data.kol_id,
            priority=event_data.priority,
            reminders=event_data.reminders,
            recurrence=event_data.recurrence,
            status="scheduled",
            created_by=current_user.id
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)

        # Schedule reminders if configured
        if event_data.reminders:
            send_calendar_reminders.delay(event.id, event_data.reminders)

        logger.info(f"Calendar event created: {event.id}")
        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create calendar event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create calendar event"
        )


@router.get("/events", response_model=List[CalendarEventResponse])
async def list_events(
    start_date: Optional[datetime] = Query(None, description="Filter events from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events until this date"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    campaign_id: Optional[int] = Query(None, description="Filter by campaign"),
    kol_id: Optional[int] = Query(None, description="Filter by KOL"),
    status: Optional[str] = Query(None, description="Filter by status"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[CalendarEventResponse]:
    """
    List calendar events with filtering options.

    Args:
        start_date: Filter events from this date
        end_date: Filter events until this date
        event_type: Filter by event type
        campaign_id: Filter by campaign
        kol_id: Filter by KOL
        status: Filter by status
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of calendar events
    """
    try:
        # Build query with filters
        query = select(CalendarEvent)

        if start_date:
            query = query.where(CalendarEvent.start_time >= start_date)

        if end_date:
            query = query.where(CalendarEvent.end_time <= end_date)

        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)

        if campaign_id:
            query = query.where(CalendarEvent.campaign_id == campaign_id)

        if kol_id:
            query = query.where(CalendarEvent.kol_id == kol_id)

        if status:
            query = query.where(CalendarEvent.status == status)

        # Order by start time
        query = query.order_by(CalendarEvent.start_time.asc())

        # Execute paginated query
        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return [CalendarEventResponse.model_validate(event) for event in result.items]

    except Exception as e:
        logger.error(f"Failed to list calendar events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar events"
        )


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    event_id: int = Path(..., description="Event ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CalendarEventResponse:
    """
    Get specific calendar event by ID.

    Args:
        event_id: Event identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Event details
    """
    try:
        query = select(CalendarEvent).where(CalendarEvent.id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get calendar event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar event"
        )


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: int = Path(..., description="Event ID"),
    event_data: CalendarEventUpdate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CalendarEventResponse:
    """
    Update calendar event.

    Args:
        event_id: Event identifier
        event_data: Updated event data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated event details
    """
    try:
        query = select(CalendarEvent).where(CalendarEvent.id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check for conflicts if time is being updated
        update_data = event_data.model_dump(exclude_unset=True)
        if "start_time" in update_data or "end_time" in update_data:
            new_start = update_data.get("start_time", event.start_time)
            new_end = update_data.get("end_time", event.end_time)
            new_attendees = update_data.get("attendees", event.attendees)

            conflicts = await _check_scheduling_conflicts(
                db, new_start, new_end, new_attendees, exclude_event_id=event_id
            )

            if conflicts and not update_data.get("ignore_conflicts", False):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "Scheduling conflicts detected",
                        "conflicts": conflicts
                    }
                )

        # Update event fields
        for field, value in update_data.items():
            if field != "ignore_conflicts":
                setattr(event, field, value)

        event.updated_at = datetime.utcnow()
        event.updated_by = current_user.id

        await db.commit()
        await db.refresh(event)

        logger.info(f"Calendar event updated: {event.id}")
        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update calendar event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update calendar event"
        )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int = Path(..., description="Event ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Delete calendar event.

    Args:
        event_id: Event identifier
        db: Database session
        current_user: Current authenticated user
    """
    try:
        query = select(CalendarEvent).where(CalendarEvent.id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Update status to cancelled instead of hard delete
        event.status = "cancelled"
        event.updated_at = datetime.utcnow()
        event.updated_by = current_user.id

        await db.commit()

        logger.info(f"Calendar event cancelled: {event.id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete calendar event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete calendar event"
        )


@router.post("/content-schedule", response_model=ContentScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_content_schedule(
    schedule_data: ContentScheduleCreate,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> ContentScheduleResponse:
    """
    Schedule content for publication.

    Args:
        schedule_data: Content scheduling data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created schedule details
    """
    try:
        # Verify campaign exists if specified
        if schedule_data.campaign_id:
            campaign_query = select(Campaign).where(Campaign.id == schedule_data.campaign_id)
            campaign_result = await db.execute(campaign_query)
            campaign = campaign_result.scalar_one_or_none()

            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign not found"
                )

        # Create content schedule
        schedule = ContentSchedule(
            title=schedule_data.title,
            description=schedule_data.description,
            content_type=schedule_data.content_type,
            platform=schedule_data.platform,
            scheduled_time=schedule_data.scheduled_time,
            timezone=schedule_data.timezone,
            campaign_id=schedule_data.campaign_id,
            kol_id=schedule_data.kol_id,
            content_data=schedule_data.content_data,
            media_urls=schedule_data.media_urls,
            hashtags=schedule_data.hashtags,
            mentions=schedule_data.mentions,
            approval_required=schedule_data.approval_required,
            auto_publish=schedule_data.auto_publish,
            status="scheduled",
            created_by=current_user.id
        )

        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        # Schedule background task for publication
        if schedule_data.auto_publish:
            schedule_content_publication.apply_async(
                args=[schedule.id],
                eta=schedule_data.scheduled_time
            )

        logger.info(f"Content schedule created: {schedule.id}")
        return ContentScheduleResponse.model_validate(schedule)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create content schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create content schedule"
        )


@router.get("/content-schedule", response_model=List[ContentScheduleResponse])
async def list_content_schedules(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    campaign_id: Optional[int] = Query(None, description="Filter by campaign"),
    kol_id: Optional[int] = Query(None, description="Filter by KOL"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[ContentScheduleResponse]:
    """
    List content schedules with filtering.

    Args:
        platform: Filter by platform
        campaign_id: Filter by campaign
        kol_id: Filter by KOL
        status: Filter by status
        start_date: Filter from date
        end_date: Filter to date
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of content schedules
    """
    try:
        query = select(ContentSchedule)

        if platform:
            query = query.where(ContentSchedule.platform == platform)

        if campaign_id:
            query = query.where(ContentSchedule.campaign_id == campaign_id)

        if kol_id:
            query = query.where(ContentSchedule.kol_id == kol_id)

        if status:
            query = query.where(ContentSchedule.status == status)

        if start_date:
            query = query.where(ContentSchedule.scheduled_time >= start_date)

        if end_date:
            query = query.where(ContentSchedule.scheduled_time <= end_date)

        query = query.order_by(ContentSchedule.scheduled_time.asc())

        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return [ContentScheduleResponse.model_validate(schedule) for schedule in result.items]

    except Exception as e:
        logger.error(f"Failed to list content schedules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content schedules"
        )


@router.post("/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> MeetingResponse:
    """
    Create a new meeting.

    Args:
        meeting_data: Meeting creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created meeting details
    """
    try:
        # Check for scheduling conflicts
        conflicts = await _check_scheduling_conflicts(
            db, meeting_data.start_time, meeting_data.end_time,
            meeting_data.attendees, exclude_event_id=None
        )

        if conflicts and not meeting_data.ignore_conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Scheduling conflicts detected",
                    "conflicts": conflicts
                }
            )

        # Create meeting
        meeting = Meeting(
            title=meeting_data.title,
            description=meeting_data.description,
            meeting_type=meeting_data.meeting_type,
            start_time=meeting_data.start_time,
            end_time=meeting_data.end_time,
            timezone=meeting_data.timezone,
            location=meeting_data.location,
            is_virtual=meeting_data.is_virtual,
            meeting_link=meeting_data.meeting_link,
            attendees=meeting_data.attendees,
            campaign_id=meeting_data.campaign_id,
            agenda=meeting_data.agenda,
            preparation_notes=meeting_data.preparation_notes,
            status="scheduled",
            created_by=current_user.id
        )

        db.add(meeting)
        await db.commit()
        await db.refresh(meeting)

        logger.info(f"Meeting created: {meeting.id}")
        return MeetingResponse.model_validate(meeting)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create meeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create meeting"
        )


@router.get("/analytics", response_model=CalendarAnalytics)
async def get_calendar_analytics(
    start_date: Optional[datetime] = Query(None, description="Analytics start date"),
    end_date: Optional[datetime] = Query(None, description="Analytics end date"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CalendarAnalytics:
    """
    Get calendar analytics and insights.

    Args:
        start_date: Analytics start date
        end_date: Analytics end date
        db: Database session
        current_user: Current authenticated user

    Returns:
        Calendar analytics data
    """
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Get event statistics
        event_query = select(
            func.count(CalendarEvent.id).label('total_events'),
            func.count(func.nullif(CalendarEvent.status == 'completed', False)).label('completed_events'),
            func.count(func.nullif(CalendarEvent.status == 'cancelled', False)).label('cancelled_events')
        ).where(
            and_(
                CalendarEvent.start_time >= start_date,
                CalendarEvent.start_time <= end_date
            )
        )
        event_result = await db.execute(event_query)
        event_stats = event_result.first()

        # Get content schedule statistics
        schedule_query = select(
            func.count(ContentSchedule.id).label('total_schedules'),
            func.count(func.nullif(ContentSchedule.status == 'published', False)).label('published_schedules'),
            func.count(func.nullif(ContentSchedule.status == 'failed', False)).label('failed_schedules')
        ).where(
            and_(
                ContentSchedule.scheduled_time >= start_date,
                ContentSchedule.scheduled_time <= end_date
            )
        )
        schedule_result = await db.execute(schedule_query)
        schedule_stats = schedule_result.first()

        # Get meeting statistics
        meeting_query = select(
            func.count(Meeting.id).label('total_meetings'),
            func.count(func.nullif(Meeting.status == 'completed', False)).label('completed_meetings')
        ).where(
            and_(
                Meeting.start_time >= start_date,
                Meeting.start_time <= end_date
            )
        )
        meeting_result = await db.execute(meeting_query)
        meeting_stats = meeting_result.first()

        return CalendarAnalytics(
            date_range_start=start_date,
            date_range_end=end_date,
            total_events=event_stats.total_events or 0,
            completed_events=event_stats.completed_events or 0,
            cancelled_events=event_stats.cancelled_events or 0,
            total_content_schedules=schedule_stats.total_schedules or 0,
            published_content=schedule_stats.published_schedules or 0,
            failed_content=schedule_stats.failed_schedules or 0,
            total_meetings=meeting_stats.total_meetings or 0,
            completed_meetings=meeting_stats.completed_meetings or 0,
            utilization_rate=85.0,  # Would calculate from actual data
            conflicts_detected=2,   # Would calculate from actual conflicts
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to get calendar analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar analytics"
        )


@router.post("/sync", response_model=Dict[str, Any])
async def sync_external_calendar(
    sync_request: CalendarSyncRequest,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sync with external calendar services.

    Args:
        sync_request: Calendar sync configuration
        db: Database session
        current_user: Current authenticated user

    Returns:
        Sync operation results
    """
    try:
        # This would integrate with external calendar APIs
        # For now, return a placeholder response

        sync_id = f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return {
            "sync_id": sync_id,
            "status": "scheduled",
            "provider": sync_request.provider,
            "sync_type": sync_request.sync_type,
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
            "events_to_sync": 0,  # Would calculate from actual data
            "last_sync": None
        }

    except Exception as e:
        logger.error(f"Failed to sync external calendar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync external calendar"
        )


# Helper functions
async def _check_scheduling_conflicts(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    attendees: List[str],
    exclude_event_id: Optional[int] = None
) -> List[SchedulingConflict]:
    """
    Check for scheduling conflicts with existing events.

    Args:
        db: Database session
        start_time: Event start time
        end_time: Event end time
        attendees: List of attendee IDs
        exclude_event_id: Event ID to exclude from conflict check

    Returns:
        List of scheduling conflicts
    """
    conflicts = []

    try:
        # Check for overlapping events with same attendees
        query = select(CalendarEvent).where(
            and_(
                or_(
                    and_(
                        CalendarEvent.start_time <= start_time,
                        CalendarEvent.end_time > start_time
                    ),
                    and_(
                        CalendarEvent.start_time < end_time,
                        CalendarEvent.end_time >= end_time
                    ),
                    and_(
                        CalendarEvent.start_time >= start_time,
                        CalendarEvent.end_time <= end_time
                    )
                ),
                CalendarEvent.status.in_(["scheduled", "confirmed"])
            )
        )

        if exclude_event_id:
            query = query.where(CalendarEvent.id != exclude_event_id)

        result = await db.execute(query)
        overlapping_events = result.scalars().all()

        for event in overlapping_events:
            # Check if any attendees overlap
            if event.attendees and attendees:
                common_attendees = set(event.attendees) & set(attendees)
                if common_attendees:
                    conflicts.append(SchedulingConflict(
                        event_id=event.id,
                        event_title=event.title,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        conflicting_attendees=list(common_attendees),
                        conflict_type="attendee_overlap"
                    ))

        return conflicts

    except Exception as e:
        logger.error(f"Failed to check scheduling conflicts: {str(e)}")
        return []