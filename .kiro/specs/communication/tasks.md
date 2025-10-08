# Implementation Tasks - Multi-Channel Communication (MVP - Email Only)

## Overview

This task list covers the MVP implementation of email communication with templates, message history, and basic delivery tracking.

**Estimated Time: 3-4 days**

---

## Phase 1: Core Models

-   [ ] 1. Create Message model

    -   Define `app/models/message.py`
    -   Fields: id, kol_id, campaign_id, channel, direction, subject, body, template_id, status, sent_by, sent_at, delivered_at, read_at, error_message
    -   Add channel enum (email, line, discord, instagram_dm, twitter_dm)
    -   Add direction enum (outbound, inbound)
    -   Add status enum (sending, sent, delivered, read, failed, bounced)
    -   Create database migration
    -   _Requirements: 1.1, 1.2_

-   [ ] 2. Create MessageTemplate model

    -   Define `app/models/message_template.py`
    -   Fields: id, name, category, channel, subject, body, variables (Array), usage_count, created_by, created_at
    -   Add category enum (brief, follow-up, reminder, thank_you)
    -   Create database migration
    -   _Requirements: 1.6_

-   [ ] 3. Create CommunicationPreference model
    -   Define `app/models/communication_preference.py`
    -   Fields: id, kol_id, primary_channel, secondary_channel, email, preferred_time, timezone, do_not_disturb_hours
    -   Create database migration
    -   _Requirements: 1.1_

---

## Phase 2: Email Service Implementation

-   [ ] 4. Configure SMTP settings

    -   Add SMTP configuration to `.env`
    -   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    -   Test SMTP connection
    -   _Requirements: 1.2_

-   [ ] 5. Create EmailService

    -   Create `app/services/email_service.py`
    -   Implement `send_email(to, subject, body, attachments)` method
    -   Use Python smtplib for sending
    -   Support HTML email format
    -   Handle SMTP errors gracefully
    -   _Requirements: 1.2_

-   [ ] 6. Add email tracking
    -   Add tracking pixel to HTML emails
    -   Implement `/api/v1/messages/{id}/track-open` webhook endpoint
    -   Record open timestamp when pixel is loaded
    -   Update message status to 'read'
    -   _Requirements: 1.2, 1.9_

---

## Phase 3: Communication Service & API

-   [ ] 7. Create CommunicationService

    -   Create `app/services/communication_service.py`
    -   Implement `send_message(kol_id, message_data)` method
    -   Get KOL communication preferences
    -   Create Message record
    -   Call appropriate channel service (EmailService for MVP)
    -   Update message status based on result
    -   _Requirements: 1.1, 1.2_

-   [ ] 8. Create messaging endpoints

    -   Create `app/api/v1/messages.py`
    -   POST `/api/v1/messages` - Send message to KOL
    -   GET `/api/v1/kols/{id}/messages` - Get KOL message history
    -   GET `/api/v1/campaigns/{id}/messages` - Get campaign messages
    -   GET `/api/v1/messages/{id}` - Get message details
    -   _Requirements: 1.1, 1.7_

-   [ ] 9. Implement message history
    -   Add `get_message_history(kol_id)` to CommunicationService
    -   Return messages in chronological order
    -   Include message preview (first 100 chars)
    -   Support pagination (50 messages per page)
    -   _Requirements: 1.7_

---

## Phase 4: Message Templates

-   [ ] 10. Create TemplateService

    -   Create `app/services/template_service.py`
    -   Implement `create_template(template_data)` method
    -   Implement `get_template(template_id)` method
    -   Implement `list_templates(category, channel)` method
    -   Implement `render_template(template_id, variables)` method
    -   _Requirements: 1.6_

-   [ ] 11. Implement template rendering

    -   Replace {{variable}} placeholders with actual values
    -   Support KOL variables (name, email, niche)
    -   Support campaign variables (name, dates, objectives)
    -   Validate all variables are provided
    -   _Requirements: 1.6_

-   [ ] 12. Create template endpoints

    -   POST `/api/v1/message-templates` - Create template
    -   GET `/api/v1/message-templates` - List templates
    -   GET `/api/v1/message-templates/{id}` - Get template
    -   PUT `/api/v1/message-templates/{id}` - Update template
    -   POST `/api/v1/message-templates/{id}/render` - Render with variables
    -   _Requirements: 1.6_

-   [ ] 13. Create default email templates
    -   Create "Brief Introduction" template
    -   Create "Follow-up Reminder" template
    -   Create "Thank You" template
    -   Seed templates in database
    -   _Requirements: 1.6_

---

## Phase 5: Communication Preferences

-   [ ] 14. Implement preference management

    -   Add `get_preferences(kol_id)` to CommunicationService
    -   Add `update_preferences(kol_id, preferences)` method
    -   Default to email if no preferences set
    -   _Requirements: 1.1_

-   [ ] 15. Create preference endpoints
    -   GET `/api/v1/kols/{id}/communication-preferences` - Get preferences
    -   PUT `/api/v1/kols/{id}/communication-preferences` - Update preferences
    -   _Requirements: 1.1_

---

## Phase 6: Delivery Status Tracking

-   [ ] 16. Implement delivery status tracking

    -   Update message status after sending
    -   Handle bounce notifications (if SMTP supports)
    -   Record delivery timestamp
    -   Record error messages on failure
    -   _Requirements: 1.9_

-   [ ] 17. Create delivery status endpoint
    -   GET `/api/v1/messages/{id}/delivery-status` - Get current status
    -   Return status, timestamps, and error details
    -   _Requirements: 1.9_

---

## Phase 7: Testing & Documentation

-   [ ]\* 18. Write unit tests

    -   Test email sending
    -   Test template rendering
    -   Test message history retrieval
    -   Test delivery tracking
    -   _Requirements: All_

-   [ ]\* 19. Write integration tests
    -   Test complete message sending flow
    -   Test template usage
    -   Test preference management
    -   _Requirements: All_

---

## Success Criteria

✅ Users can send emails to KOLs  
✅ Email templates can be created and used  
✅ Message history is tracked per KOL  
✅ Email open tracking works  
✅ Delivery status is recorded  
✅ Communication preferences can be set  
✅ Template variables are replaced correctly  
✅ Default templates are available

---

## Notes

-   MVP focuses on email only
-   Skip Line, Discord, social DMs for MVP (Phase 2)
-   Skip bulk messaging for MVP (Phase 2)
-   Skip advanced notifications for MVP (Phase 2)
-   Use simple SMTP for email (no SendGrid/SES yet)
-   Email tracking uses simple pixel method
-   Advanced features in Phase 2
