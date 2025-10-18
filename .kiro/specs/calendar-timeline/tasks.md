# Implementation Tasks - Calendar & Timeline Management (MVP)

## Overview

This task list covers the MVP implementation of campaign timeline visualization, KOL availability management, deadline tracking, and basic workload monitoring.

**Estimated Time: 5-6 days**

---

## Phase 1: Core Models

-   [x] 1. Create KOLAvailability model

    -   Define `app/models/kol_availability.py` with KOLAvailability table
    -   Fields: id, kol_id, start_date, end_date, is_available, reason, created_at
    -   Add reason enum (vacation, other_campaign, personal, blocked)
    -   Create database migration
    -   _Requirements: 2.1, 2.4_

-   [x] 2. Create Deadline model

    -   Define `app/models/deadline.py` with Deadline table
    -   Fields: id, campaign_id, title, description, due_date, priority, status, responsible_user_id, completed_at, created_at
    -   Add priority enum (low, medium, high, critical)
    -   Add status enum (upcoming, today, overdue, completed)
    -   Create database migration
    -   _Requirements: 3.1, 3.2_

-   [x] 3. Create RecurringEvent model

    -   Define `app/models/recurring_event.py`
    -   Fields: id, user_id, title, description, frequency, day_of_week, day_of_month, time, is_active, created_at
    -   Add frequency enum (daily, weekly, monthly)
    -   Create database migration
    -   _Requirements: 7.1, 7.2_

---

## Phase 2: Timeline Visualization Service

-   [ ] 4. Create TimelineService

    -   Create `app/services/timeline_service.py`
    -   Implement `get_campaign_timeline(campaign_id)` method
    -   Calculate campaign phases (brief creation, KOL selection, content creation, posting, reporting)
    -   Calculate progress percentage based on completed milestones
    -   Identify delayed phases and overdue items
    -   _Requirements: 1.1, 1.2, 1.3, 1.5_

-   [ ] 5. Implement timeline data structure

    -   Create Gantt chart data format
    -   Include campaign phases with start/end dates
    -   Include milestones and deadlines
    -   Include progress indicators and status
    -   Support hover details with responsible person and notes
    -   _Requirements: 1.1, 1.4, 1.6_

-   [ ] 6. Create timeline endpoints
    -   GET `/api/v1/campaigns/{id}/timeline` - Get campaign timeline data
    -   PUT `/api/v1/campaigns/{id}/timeline` - Update timeline (dates, milestones)
    -   GET `/api/v1/campaigns/{id}/timeline/conflicts` - Check for conflicts
    -   _Requirements: 1.1, 1.7_

---

## Phase 3: KOL Availability Management

-   [ ] 7. Create AvailabilityService

    -   Create `app/services/availability_service.py`
    -   Implement `get_kol_availability(kol_id, start_date, end_date)` method
    -   Implement `set_kol_unavailable(kol_id, start_date, end_date, reason)` method
    -   Implement `check_kol_conflicts(kol_id, campaign_id)` method
    -   Implement `calculate_kol_capacity(kol_id)` method
    -   _Requirements: 2.1, 2.2, 2.3, 2.5_

-   [ ] 8. Implement conflict detection

    -   Check for overlapping campaign assignments
    -   Check for blocked/unavailable dates
    -   Calculate capacity utilization (max 3 concurrent campaigns)
    -   Provide conflict warnings with details
    -   _Requirements: 2.2, 2.3, 2.6_

-   [ ] 9. Create availability endpoints
    -   GET `/api/v1/kols/{id}/availability` - Get availability calendar
    -   POST `/api/v1/kols/{id}/availability/block` - Block dates
    -   DELETE `/api/v1/kols/{id}/availability/{block_id}` - Remove block
    -   GET `/api/v1/kols/{id}/capacity` - Get capacity information
    -   _Requirements: 2.1, 2.4, 2.5_

---

## Phase 4: Deadline Management

-   [ ] 10. Create DeadlineService

    -   Create `app/services/deadline_service.py`
    -   Implement `create_deadline(campaign_id, deadline_data)` method
    -   Implement `get_upcoming_deadlines(user_id)` method
    -   Implement `check_overdue_deadlines()` method
    -   Implement `complete_deadline(deadline_id)` method
    -   _Requirements: 3.1, 3.2, 3.4_

-   [ ] 11. Implement deadline tracking and alerts

    -   Create Celery task to check deadlines daily
    -   Send reminders 3 days before due date
    -   Send urgent alerts for deadlines due today
    -   Escalate overdue deadlines to Campaign Manager
    -   _Requirements: 3.2, 3.3, 3.4_

-   [ ] 12. Create deadline endpoints
    -   POST `/api/v1/campaigns/{id}/deadlines` - Create deadline
    -   GET `/api/v1/deadlines` - Get all deadlines (filtered by user)
    -   GET `/api/v1/deadlines/upcoming` - Get upcoming deadlines
    -   PUT `/api/v1/deadlines/{id}` - Update deadline
    -   POST `/api/v1/deadlines/{id}/complete` - Mark as complete
    -   _Requirements: 3.1, 3.5, 3.6_

---

## Phase 5: Multi-Campaign Calendar View

-   [ ] 13. Create CalendarService

    -   Create `app/services/calendar_service.py`
    -   Implement `get_unified_calendar(user_id, start_date, end_date)` method
    -   Implement `get_team_calendar(start_date, end_date)` method
    -   Support month, week, and day views
    -   Include campaigns, deadlines, and milestones
    -   _Requirements: 4.1, 4.2, 4.5_

-   [ ] 14. Implement calendar filtering

    -   Filter by campaign status (active, completed, cancelled)
    -   Filter by team member assignments
    -   Filter by client or campaign type
    -   Color-code campaigns for visual distinction
    -   _Requirements: 4.4, 4.1_

-   [ ] 15. Create calendar endpoints
    -   GET `/api/v1/calendar` - Get unified calendar view
    -   GET `/api/v1/calendar/team` - Get team calendar
    -   GET `/api/v1/calendar/export` - Export as iCal format
    -   Support date range and filter parameters
    -   _Requirements: 4.1, 4.2, 4.6_

---

## Phase 6: Workload Management

-   [ ] 16. Create WorkloadService

    -   Create `app/services/workload_service.py`
    -   Implement `get_team_workload()` method
    -   Implement `get_user_workload(user_id)` method
    -   Implement `calculate_capacity_utilization(user_id)` method
    -   Implement `suggest_assignments(campaign_id)` method
    -   _Requirements: 6.1, 6.2, 6.6_

-   [ ] 17. Implement workload calculations

    -   Count active campaigns per user
    -   Count pending tasks and deadlines
    -   Calculate capacity utilization (assume 3 campaigns = 100%)
    -   Identify overloaded (>100%) and underutilized (<50%) users
    -   _Requirements: 6.2, 6.3, 6.4_

-   [ ] 18. Create workload endpoints
    -   GET `/api/v1/workload/team` - Get team workload overview
    -   GET `/api/v1/workload/user/{id}` - Get specific user workload
    -   GET `/api/v1/campaigns/{id}/suggest-assignments` - Suggest team members
    -   _Requirements: 6.1, 6.6_

---

## Phase 7: Recurring Events

-   [ ] 19. Create RecurringEventService

    -   Create `app/services/recurring_event_service.py`
    -   Implement `create_recurring_event(user_id, event_data)` method
    -   Implement `generate_event_instances(event_id, start_date, end_date)` method
    -   Implement `process_due_recurring_events()` Celery task
    -   _Requirements: 7.1, 7.2, 7.3_

-   [ ] 20. Create recurring event endpoints

    -   POST `/api/v1/recurring-events` - Create recurring event
    -   GET `/api/v1/recurring-events` - List user's recurring events
    -   PUT `/api/v1/recurring-events/{id}` - Update recurring event
    -   DELETE `/api/v1/recurring-events/{id}` - Delete recurring event
    -   _Requirements: 7.1, 7.5, 7.6_

-   [ ] 21. Implement recurring event processing
    -   Check for due recurring events daily
    -   Create task instances and send notifications
    -   Handle skipped occurrences with reasons
    -   Maintain recurring schedule after completion
    -   _Requirements: 7.2, 7.3, 7.4_

---

## Phase 8: Milestone Management (Basic)

-   [ ] 22. Extend existing Campaign model for milestones

    -   Add milestone support to existing campaign structure
    -   Use existing deliverable/deadline system for milestones
    -   Track milestone completion status
    -   _Requirements: 5.1, 5.2_

-   [ ] 23. Implement milestone tracking

    -   Mark milestones as complete with completion date
    -   Track delays and reasons for late completion
    -   Check milestone dependencies (basic)
    -   Suggest campaign status updates when all milestones complete
    -   _Requirements: 5.2, 5.3, 5.4, 5.7_

-   [ ] 24. Create milestone endpoints
    -   Use existing deadline endpoints for milestone management
    -   Add milestone-specific filtering and status
    -   Track milestone completion and delays
    -   _Requirements: 5.1, 5.5, 5.6_

---

## Phase 9: Background Tasks and Notifications

-   [ ] 25. Create calendar-related Celery tasks

    -   `@celery_app.task check_deadlines()` - Daily deadline checking
    -   `@celery_app.task send_deadline_reminders()` - Send reminder notifications
    -   `@celery_app.task process_recurring_events()` - Process due recurring events
    -   `@celery_app.task check_campaign_conflicts()` - Check for new conflicts
    -   _Requirements: 3.2, 3.3, 7.2_

-   [ ] 26. Set up Celery Beat schedule

    -   Daily deadline checking at 9 AM
    -   Recurring event processing at midnight
    -   Conflict checking every 6 hours
    -   Workload calculation refresh every hour
    -   _Requirements: 3.2, 7.2_

-   [ ] 27. Implement notification system integration
    -   Send deadline reminders via existing notification system
    -   Send escalation alerts to Campaign Managers
    -   Send recurring event reminders
    -   Include quick action links in notifications
    -   _Requirements: 3.2, 3.4, 7.2_

---

## Phase 10: Testing & Documentation

-   [ ]\* 28. Write unit tests

    -   Test conflict detection logic
    -   Test capacity calculation
    -   Test deadline reminder logic
    -   Test workload distribution calculations
    -   Test recurring event generation
    -   _Requirements: All_

-   [ ]\* 29. Write integration tests
    -   Test end-to-end timeline management
    -   Test deadline notification workflow
    -   Test team assignment suggestions
    -   Test calendar view generation
    -   _Requirements: All_

---

## Success Criteria

✅ Campaign timelines display with phases and progress  
✅ KOL availability conflicts are detected and warned  
✅ Deadlines send reminders and escalate when overdue  
✅ Multi-campaign calendar shows all team activities  
✅ Team workload is calculated and balanced  
✅ Recurring events are processed automatically  
✅ Milestones are tracked and completion recorded  
✅ Calendar can be exported to external systems  
✅ Notifications are sent for important events

---

## Notes

-   MVP focuses on core timeline and deadline functionality
-   Skip advanced calendar sync (Google, Outlook) for MVP (Phase 2)
-   Skip complex milestone dependencies for MVP (Phase 2)
-   Skip vacation/backup assignment for MVP (Phase 2)
-   Use simple capacity calculation (3 campaigns = 100%)
-   Advanced workload optimization can be added in Phase 2
-   Focus on essential calendar and deadline features
