# Implementation Tasks - Follow-up Automation (MVP)

## Overview

This task list covers the MVP implementation of automated follow-up scheduling, reminder notifications, template management, and basic escalation rules.

**Estimated Time: 4-5 days**

---

## Phase 1: Core Models

-   [x] 1. Create FollowUp model

    -   Define `app/models/follow_up.py` with FollowUp table
    -   Fields: id, original_message_id, kol_id, campaign_id, follow_up_number, scheduled_at, status, sent_at, skipped_reason, template_id, assigned_to, created_at
    -   Add status enum (scheduled, sent, skipped, cancelled)
    -   Create database migration
    -   _Requirements: 1.1, 1.2_

-   [x] 2. Create FollowUpRule model

    -   Define `app/models/follow_up_rule.py`
    -   Fields: id, campaign_id, intervals (Array), max_follow_ups, escalate_after, is_active, created_at
    -   Default intervals: [1, 3, 5] days
    -   Create database migration
    -   _Requirements: 1.1, 7.1_

-   [x] 3. Create Escalation model

    -   Define `app/models/escalation.py`
    -   Fields: id, follow_up_id, kol_id, campaign_id, escalated_from, escalated_to, reason, status, resolved_at, resolution_action, created_at
    -   Add status enum (pending, resolved, dismissed)
    -   Create database migration
    -   _Requirements: 5.1, 5.2_

---

## Phase 2: Follow-up Scheduling Service

-   [ ] 4. Create FollowUpService

    -   Create `app/services/follow_up_service.py`
    -   Implement `schedule_follow_ups(message_id, kol_id, campaign_id)` method
    -   Implement `cancel_follow_ups(message_id)` method for when KOL responds
    -   Implement `send_follow_up(follow_up_id)` method
    -   Implement `skip_follow_up(follow_up_id, reason)` method
    -   _Requirements: 1.1, 1.4, 4.1_

-   [ ] 5. Implement auto-scheduling on message send

    -   Hook into message sending to automatically schedule follow-ups
    -   Get follow-up rules for campaign (or use defaults)
    -   Create FollowUp records for each interval
    -   Schedule Celery tasks for each follow-up
    -   _Requirements: 1.1, 1.2_

-   [ ] 6. Implement auto-cancellation on response
    -   Hook into message response handling
    -   Cancel all pending follow-ups for the original message
    -   Update follow-up status to 'cancelled'
    -   Cancel scheduled Celery tasks
    -   _Requirements: 1.4_

---

## Phase 3: Follow-up Templates

-   [ ] 7. Extend MessageTemplate model for follow-ups

    -   Add follow_up_number field to existing MessageTemplate
    -   Add category enum value for 'follow_up'
    -   Create default follow-up templates (1st, 2nd, 3rd)
    -   Seed templates in database
    -   _Requirements: 3.1, 3.2_

-   [ ] 8. Implement template suggestion logic

    -   Add `suggest_template(follow_up_number, category)` to TemplateService
    -   Return appropriate template based on follow-up sequence
    -   Allow Account Executive to select different template
    -   _Requirements: 3.3, 3.4_

-   [ ] 9. Create follow-up template endpoints
    -   GET `/api/v1/follow-ups/{id}/suggested-template` - Get suggested template
    -   POST `/api/v1/follow-ups/{id}/send-with-template` - Send with specific template
    -   Track template usage and effectiveness
    -   _Requirements: 3.3, 3.6_

---

## Phase 4: Background Task Processing

-   [ ] 10. Create Celery tasks for follow-up processing

    -   Create `@celery_app.task process_due_follow_ups()` task
    -   Check for follow-ups that are due to be sent
    -   Send follow-up messages using CommunicationService
    -   Update follow-up status and sent_at timestamp
    -   _Requirements: 1.5, 2.1_

-   [ ] 11. Implement smart timing logic

    -   Add `calculate_optimal_send_time(kol_id, scheduled_at)` function
    -   Consider KOL timezone and response patterns
    -   Avoid weekends and late night hours
    -   Respect Do Not Disturb preferences
    -   _Requirements: 10.1, 10.2, 10.3_

-   [ ] 12. Set up Celery Beat schedule
    -   Configure periodic task to process due follow-ups (every 15 minutes)
    -   Configure daily task to send follow-up reminders to users
    -   Configure task to check for escalations (every 6 hours)
    -   _Requirements: 2.1, 2.2_

---

## Phase 5: Follow-up Management API

-   [ ] 13. Create follow-up management endpoints

    -   Create `app/api/v1/follow_ups.py`
    -   GET `/api/v1/follow-ups` - List follow-ups with filters
    -   GET `/api/v1/follow-ups/{id}` - Get follow-up details
    -   POST `/api/v1/follow-ups/{id}/send` - Send immediately
    -   POST `/api/v1/follow-ups/{id}/skip` - Skip with reason
    -   PUT `/api/v1/follow-ups/{id}/reschedule` - Reschedule to new date
    -   _Requirements: 2.1, 4.1, 4.2_

-   [ ] 14. Create follow-up rules endpoints

    -   GET `/api/v1/follow-up-rules` - Get default rules
    -   POST `/api/v1/follow-up-rules` - Create custom rule
    -   GET `/api/v1/campaigns/{id}/follow-up-rules` - Get campaign-specific rules
    -   PUT `/api/v1/campaigns/{id}/follow-up-rules` - Update campaign rules
    -   _Requirements: 7.1, 7.2, 7.3_

-   [ ] 15. Add follow-up history endpoints
    -   GET `/api/v1/kols/{id}/follow-up-history` - Get KOL follow-up history
    -   GET `/api/v1/campaigns/{id}/follow-up-history` - Get campaign follow-up history
    -   Include status, dates, and response information
    -   _Requirements: 8.1, 8.2, 8.3_

---

## Phase 6: Escalation System

-   [ ] 16. Create EscalationService

    -   Create `app/services/escalation_service.py`
    -   Implement `check_escalation_rules(follow_up_id)` method
    -   Implement `escalate_to_manager(follow_up_id, reason)` method
    -   Implement `resolve_escalation(escalation_id, action)` method
    -   _Requirements: 5.1, 5.2, 5.5_

-   [ ] 17. Implement escalation logic

    -   Check if max follow-ups reached without response
    -   Check if campaign deadline is approaching (within 3 days)
    -   Escalate to Campaign Manager automatically
    -   Send escalation notifications
    -   _Requirements: 5.1, 5.2, 5.4_

-   [ ] 18. Create escalation endpoints
    -   GET `/api/v1/escalations` - Get escalations for current user
    -   GET `/api/v1/escalations/{id}` - Get escalation details
    -   POST `/api/v1/escalations/{id}/resolve` - Resolve escalation
    -   POST `/api/v1/escalations/{id}/dismiss` - Dismiss escalation
    -   _Requirements: 5.2, 5.5_

---

## Phase 7: Notifications and Reminders

-   [ ] 19. Implement follow-up reminder notifications

    -   Create task to send daily reminders to Account Executives
    -   List due follow-ups in notification
    -   Include quick action links (send, skip, reschedule)
    -   Send email reminders based on user preferences
    -   _Requirements: 2.1, 2.2, 2.3_

-   [ ] 20. Add overdue follow-up alerts

    -   Check for follow-ups overdue by more than 24 hours
    -   Send escalation notifications to Campaign Manager
    -   Include follow-up history and KOL details
    -   _Requirements: 2.4, 5.1_

-   [ ] 21. Create notification preferences
    -   Allow users to configure reminder frequency
    -   Allow users to set quiet hours for notifications
    -   Allow users to choose notification channels (in-app, email)
    -   _Requirements: 2.2, 10.6_

---

## Phase 8: Analytics and Performance Tracking

-   [ ] 22. Implement follow-up analytics

    -   Create `app/services/follow_up_analytics_service.py`
    -   Calculate response rates by follow-up number (1st, 2nd, 3rd)
    -   Calculate response rates by interval (1, 3, 5 days)
    -   Track template effectiveness
    -   _Requirements: 6.1, 6.2, 6.3_

-   [ ] 23. Create analytics endpoints

    -   GET `/api/v1/follow-ups/analytics/response-rates` - Response rates by interval
    -   GET `/api/v1/follow-ups/analytics/templates` - Template effectiveness
    -   GET `/api/v1/follow-ups/analytics/user-performance` - User performance metrics
    -   _Requirements: 6.1, 6.2, 6.5_

-   [ ] 24. Add performance tracking
    -   Track follow-up completion rates by user
    -   Track average response times
    -   Identify best practices and successful patterns
    -   _Requirements: 6.5, 6.7_

---

## Phase 9: Testing & Documentation

-   [ ]\* 25. Write unit tests

    -   Test follow-up scheduling logic
    -   Test escalation rules
    -   Test smart timing calculations
    -   Test response rate calculations
    -   _Requirements: All_

-   [ ]\* 26. Write integration tests
    -   Test complete follow-up workflow
    -   Test auto-cancellation on response
    -   Test escalation process
    -   Test notification delivery
    -   _Requirements: All_

---

## Success Criteria

✅ Follow-ups are automatically scheduled when messages are sent  
✅ Follow-ups are cancelled when KOLs respond  
✅ Account Executives receive reminders for due follow-ups  
✅ Follow-ups can be sent, skipped, or rescheduled manually  
✅ Escalation occurs after max follow-ups without response  
✅ Templates are suggested based on follow-up sequence  
✅ Smart timing considers KOL preferences and timezone  
✅ Analytics show response rates and template effectiveness

---

## Notes

-   MVP focuses on basic 1, 3, 5 day intervals
-   Skip multi-channel strategy for MVP (Phase 2)
-   Skip advanced timing optimization for MVP (Phase 2)
-   Skip vacation/backup assignment for MVP (Phase 2)
-   Use simple escalation rules (max follow-ups reached)
-   Advanced analytics can be added in Phase 2
