"""
Calendar and Scheduling Background Tasks

Handles calendar-related background processing including:
- Content publication scheduling and automation
- Event reminders and notifications
- Calendar synchronization with external services
- Meeting coordination and follow-ups
- Recurring event generation
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.tasks.celery_app import celery_app
from app.core.database import get_session
from app.models.calendar import (
    CalendarEvent, ContentSchedule, Meeting, EventReminder,
    RecurringEventSeries, CalendarIntegration
)
from app.models.campaigns import CampaignContent
from app.services.communication.factory import communication_factory
from app.services.social_media.factory import social_media_factory

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def schedule_content_publication(self, content_schedule_id: int) -> Dict[str, Any]:
    """
    Execute scheduled content publication to social media platforms.

    Args:
        content_schedule_id: Content schedule identifier

    Returns:
        Dict with publication results
    """
    results = {
        "content_schedule_id": content_schedule_id,
        "success": False,
        "platform": None,
        "published_post_id": None,
        "error": None,
        "published_at": None
    }

    try:
        with get_session() as db:
            # Get content schedule
            schedule = db.query(ContentSchedule).filter_by(id=content_schedule_id).first()
            if not schedule:
                raise ValueError(f"Content schedule {content_schedule_id} not found")

            # Check if it's time to publish
            now = datetime.utcnow()
            if schedule.scheduled_time > now:
                # Reschedule for the correct time
                eta = schedule.scheduled_time
                schedule_content_publication.apply_async(
                    args=[content_schedule_id],
                    eta=eta
                )
                return {"message": "Rescheduled for correct time", "eta": eta.isoformat()}

            # Check approval status
            if schedule.approval_required and schedule.approval_status != "approved":
                schedule.status = "approval_pending"
                db.commit()
                return {
                    "content_schedule_id": content_schedule_id,
                    "status": "approval_pending",
                    "message": "Content requires approval before publishing"
                }

            # Publish content
            publication_result = asyncio.run(_publish_content_to_platform(schedule))

            if publication_result["success"]:
                # Update schedule with success
                schedule.status = "published"
                schedule.published_at = now
                schedule.published_post_id = publication_result.get("post_id")
                schedule.engagement_data = publication_result.get("initial_metrics", {})

                # Create campaign content record if linked to campaign
                if schedule.campaign_id:
                    campaign_content = CampaignContent(
                        campaign_id=schedule.campaign_id,
                        kol_id=schedule.kol_id,
                        platform=schedule.platform,
                        content_type=schedule.content_type,
                        title=schedule.title,
                        description=schedule.description,
                        content_url=publication_result.get("post_url"),
                        media_urls=schedule.media_urls,
                        hashtags=schedule.hashtags,
                        mentions=schedule.mentions,
                        published_date=now,
                        status="published"
                    )
                    db.add(campaign_content)

                results.update({
                    "success": True,
                    "platform": schedule.platform,
                    "published_post_id": publication_result.get("post_id"),
                    "published_at": now.isoformat()
                })

            else:
                # Update schedule with failure
                schedule.status = "failed"
                schedule.engagement_data = {"error": publication_result.get("error")}
                results["error"] = publication_result.get("error")

            db.commit()

            logger.info(f"Content publication completed for schedule {content_schedule_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Content publication failed for schedule {content_schedule_id}: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def send_calendar_reminders(self, event_id: int, reminder_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send calendar event reminders to attendees.

    Args:
        event_id: Calendar event identifier
        reminder_configs: List of reminder configurations

    Returns:
        Dict with reminder sending results
    """
    results = {
        "event_id": event_id,
        "reminders_scheduled": 0,
        "reminders_sent": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            # Get calendar event
            event = db.query(CalendarEvent).filter_by(id=event_id).first()
            if not event:
                raise ValueError(f"Calendar event {event_id} not found")

            # Process each reminder configuration
            for config in reminder_configs:
                try:
                    # Calculate reminder time
                    reminder_time = event.start_time - timedelta(minutes=config["timing_minutes"])

                    # Create reminder record
                    reminder = EventReminder(
                        event_id=event_id,
                        reminder_type=config["type"],
                        timing_minutes=config["timing_minutes"],
                        recipients=config.get("recipients", event.attendees),
                        subject=config.get("subject", f"Reminder: {event.title}"),
                        message_template=config.get("message_template"),
                        scheduled_at=reminder_time,
                        status="scheduled"
                    )

                    db.add(reminder)
                    results["reminders_scheduled"] += 1

                    # If reminder time is now or past, send immediately
                    if reminder_time <= datetime.utcnow():
                        send_result = asyncio.run(_send_reminder_notification(reminder, event))
                        if send_result["success"]:
                            reminder.status = "sent"
                            reminder.sent_at = datetime.utcnow()
                            results["reminders_sent"] += 1
                        else:
                            reminder.status = "failed"
                            reminder.last_error = send_result["error"]
                            results["errors"].append(send_result["error"])

                except Exception as e:
                    error_msg = f"Failed to process reminder config: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            db.commit()

            logger.info(f"Calendar reminders processed for event {event_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Calendar reminder processing failed for event {event_id}: {str(e)}")
        raise self.retry(countdown=180, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def sync_external_calendar(self, integration_id: int) -> Dict[str, Any]:
    """
    Synchronize with external calendar service.

    Args:
        integration_id: Calendar integration identifier

    Returns:
        Dict with sync results
    """
    results = {
        "integration_id": integration_id,
        "sync_type": None,
        "events_synced": 0,
        "events_updated": 0,
        "conflicts_detected": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            # Get calendar integration
            integration = db.query(CalendarIntegration).filter_by(id=integration_id).first()
            if not integration or not integration.is_active:
                raise ValueError(f"Calendar integration {integration_id} not found or inactive")

            results["sync_type"] = integration.sync_type

            # Perform sync based on type
            if integration.sync_type in ["import", "bidirectional"]:
                import_result = asyncio.run(_import_external_events(integration))
                results["events_synced"] += import_result.get("imported_count", 0)
                results["errors"].extend(import_result.get("errors", []))

            if integration.sync_type in ["export", "bidirectional"]:
                export_result = asyncio.run(_export_events_to_external(integration))
                results["events_updated"] += export_result.get("exported_count", 0)
                results["errors"].extend(export_result.get("errors", []))

            # Update integration status
            integration.last_sync_at = datetime.utcnow()
            integration.last_sync_status = "success" if not results["errors"] else "partial"
            integration.events_synced = integration.events_synced + results["events_synced"]

            if results["errors"]:
                integration.last_sync_error = "; ".join(results["errors"][:3])  # Store first 3 errors

            db.commit()

            logger.info(f"Calendar sync completed for integration {integration_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Calendar sync failed for integration {integration_id}: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def generate_recurring_events(self, series_id: int, months_ahead: int = 3) -> Dict[str, Any]:
    """
    Generate instances for recurring event series.

    Args:
        series_id: Recurring event series identifier
        months_ahead: How many months ahead to generate events

    Returns:
        Dict with generation results
    """
    results = {
        "series_id": series_id,
        "events_generated": 0,
        "events_updated": 0,
        "end_date": None,
        "errors": []
    }

    try:
        with get_session() as db:
            # Get recurring series
            series = db.query(RecurringEventSeries).filter_by(id=series_id).first()
            if not series or not series.is_active:
                raise ValueError(f"Recurring series {series_id} not found or inactive")

            # Calculate generation window
            start_from = series.last_generated or series.start_date
            end_date = datetime.utcnow() + timedelta(days=months_ahead * 30)

            if series.end_date and end_date > series.end_date:
                end_date = series.end_date

            results["end_date"] = end_date.isoformat()

            # Generate events based on pattern
            generation_result = _generate_event_instances(series, start_from, end_date)

            for event_data in generation_result["events"]:
                try:
                    # Create calendar event from template
                    event = CalendarEvent(
                        title=event_data["title"],
                        description=event_data["description"],
                        event_type=event_data["event_type"],
                        start_time=event_data["start_time"],
                        end_time=event_data["end_time"],
                        timezone=event_data["timezone"],
                        location=event_data.get("location"),
                        is_virtual=event_data.get("is_virtual", False),
                        meeting_link=event_data.get("meeting_link"),
                        attendees=event_data.get("attendees", []),
                        priority=event_data.get("priority", "medium"),
                        status="scheduled",
                        created_by=series.created_by
                    )

                    db.add(event)
                    results["events_generated"] += 1

                except Exception as e:
                    error_msg = f"Failed to create event instance: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Update series last generated timestamp
            series.last_generated = end_date

            db.commit()

            logger.info(f"Recurring events generated for series {series_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Recurring event generation failed for series {series_id}: {str(e)}")
        raise self.retry(countdown=240, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def send_meeting_follow_ups(self) -> Dict[str, Any]:
    """
    Send follow-up notifications for completed meetings.

    Returns:
        Dict with follow-up processing results
    """
    results = {
        "meetings_processed": 0,
        "follow_ups_sent": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            # Get meetings that need follow-ups
            follow_up_due = datetime.utcnow() - timedelta(hours=2)  # 2 hours after meeting

            meetings = db.query(Meeting).filter(
                and_(
                    Meeting.status == "completed",
                    Meeting.follow_up_required == True,
                    Meeting.end_time <= follow_up_due,
                    or_(
                        Meeting.follow_up_date.is_(None),
                        Meeting.follow_up_date <= datetime.utcnow()
                    )
                )
            ).all()

            for meeting in meetings:
                try:
                    # Send follow-up
                    follow_up_result = asyncio.run(_send_meeting_follow_up(meeting))

                    if follow_up_result["success"]:
                        meeting.follow_up_date = datetime.utcnow()
                        meeting.follow_up_notes = "Follow-up sent automatically"
                        results["follow_ups_sent"] += 1
                    else:
                        results["errors"].append(follow_up_result["error"])

                    results["meetings_processed"] += 1

                except Exception as e:
                    error_msg = f"Failed to send follow-up for meeting {meeting.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            db.commit()

            logger.info(f"Meeting follow-ups processed: {results}")
            return results

    except Exception as e:
        logger.error(f"Meeting follow-up processing failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task
def process_pending_reminders() -> Dict[str, Any]:
    """
    Process and send pending event reminders.

    Returns:
        Dict with reminder processing results
    """
    results = {
        "reminders_processed": 0,
        "reminders_sent": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            # Get reminders that should be sent now
            now = datetime.utcnow()

            reminders = db.query(EventReminder).filter(
                and_(
                    EventReminder.status == "scheduled",
                    EventReminder.scheduled_at <= now
                )
            ).all()

            for reminder in reminders:
                try:
                    # Get associated event
                    event = None
                    if reminder.event_id:
                        event = db.query(CalendarEvent).filter_by(id=reminder.event_id).first()
                    elif reminder.meeting_id:
                        event = db.query(Meeting).filter_by(id=reminder.meeting_id).first()

                    if event:
                        send_result = asyncio.run(_send_reminder_notification(reminder, event))

                        if send_result["success"]:
                            reminder.status = "sent"
                            reminder.sent_at = now
                            reminder.delivery_status = send_result.get("delivery_status", {})
                            results["reminders_sent"] += 1
                        else:
                            reminder.status = "failed"
                            reminder.last_error = send_result["error"]
                            reminder.delivery_attempts += 1

                    results["reminders_processed"] += 1

                except Exception as e:
                    error_msg = f"Failed to send reminder {reminder.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            db.commit()

            logger.info(f"Pending reminders processed: {results}")
            return results

    except Exception as e:
        logger.error(f"Reminder processing failed: {str(e)}")
        return {"error": str(e), "reminders_processed": 0, "reminders_sent": 0}


# Helper functions
async def _publish_content_to_platform(schedule: ContentSchedule) -> Dict[str, Any]:
    """
    Publish content to the specified social media platform.

    Args:
        schedule: Content schedule object

    Returns:
        Dict with publication results
    """
    try:
        # Get appropriate social media service
        service = social_media_factory.get_service(schedule.platform)

        # Prepare content data
        content_data = {
            "text": schedule.content_data.get("text", ""),
            "media_urls": schedule.media_urls,
            "hashtags": schedule.hashtags,
            "mentions": schedule.mentions
        }

        # Publish content
        async with service:
            result = await service.publish_content(
                content_type=schedule.content_type,
                content_data=content_data
            )

            return {
                "success": True,
                "post_id": result.get("post_id"),
                "post_url": result.get("post_url"),
                "initial_metrics": result.get("metrics", {})
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def _send_reminder_notification(reminder: EventReminder, event) -> Dict[str, Any]:
    """
    Send reminder notification to recipients.

    Args:
        reminder: Event reminder object
        event: Associated event object

    Returns:
        Dict with sending results
    """
    try:
        # Prepare notification message
        message = reminder.custom_message or reminder.message_template or f"Reminder: {event.title} is starting soon"

        # Send notifications based on type
        if reminder.reminder_type == "email":
            service = communication_factory.get_service("email")

            async with service:
                for recipient in reminder.recipients:
                    await service.send_message(
                        recipient=recipient,
                        subject=reminder.subject,
                        content=message
                    )

        return {"success": True, "delivery_status": {}}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _import_external_events(integration: CalendarIntegration) -> Dict[str, Any]:
    """
    Import events from external calendar service.

    Args:
        integration: Calendar integration object

    Returns:
        Dict with import results
    """
    # This would integrate with external calendar APIs
    # For now, return placeholder results
    return {
        "imported_count": 0,
        "errors": []
    }


async def _export_events_to_external(integration: CalendarIntegration) -> Dict[str, Any]:
    """
    Export events to external calendar service.

    Args:
        integration: Calendar integration object

    Returns:
        Dict with export results
    """
    # This would integrate with external calendar APIs
    # For now, return placeholder results
    return {
        "exported_count": 0,
        "errors": []
    }


def _generate_event_instances(series: RecurringEventSeries, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Generate event instances based on recurrence pattern.

    Args:
        series: Recurring event series
        start_date: Start of generation window
        end_date: End of generation window

    Returns:
        Dict with generated event data
    """
    events = []
    current_date = start_date

    # Simple daily pattern example
    if series.pattern_type == "daily":
        while current_date <= end_date:
            event_data = series.event_template.copy()
            event_data.update({
                "start_time": current_date,
                "end_time": current_date + timedelta(hours=1)  # Default 1 hour duration
            })
            events.append(event_data)
            current_date += timedelta(days=series.interval_value)

    return {"events": events}


async def _send_meeting_follow_up(meeting: Meeting) -> Dict[str, Any]:
    """
    Send meeting follow-up with notes and action items.

    Args:
        meeting: Meeting object

    Returns:
        Dict with follow-up results
    """
    try:
        # Prepare follow-up content
        follow_up_content = f"""
        Meeting Follow-up: {meeting.title}

        Meeting Notes:
        {meeting.meeting_notes or 'No notes recorded'}

        Action Items:
        {'; '.join([item.get('description', '') for item in meeting.action_items or []])}
        """

        # Send to attendees
        service = communication_factory.get_service("email")

        async with service:
            for attendee in meeting.attendees:
                await service.send_message(
                    recipient=attendee,
                    subject=f"Follow-up: {meeting.title}",
                    content=follow_up_content
                )

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}