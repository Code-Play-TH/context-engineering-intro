# Implementation Tasks - Brief Management (MVP)

## Overview

This task list covers the MVP implementation of basic brief management with templates, campaign-based generation, and email distribution.

**Estimated Time: 3-4 days**

---

## Phase 1: Core Models

-   [ ] 1. Create BriefTemplate model

    -   Define `app/models/brief_template.py`
    -   Fields: id, name, description, sections (JSON), variables (Array), is_default, usage_count, created_by, created_at
    -   Create database migration
    -   _Requirements: 1.1_

-   [ ] 2. Create Brief model

    -   Define `app/models/brief.py`
    -   Fields: id, campaign_id, kol_id, template_id, version, status, content (JSON), customizations (JSON), created_by, created_at, sent_at, viewed_at, responded_at
    -   Add status enum (draft, sent, accepted, declined, negotiating)
    -   Add foreign keys to Campaign, KOL, BriefTemplate
    -   Create database migration
    -   _Requirements: 1.2, 1.3_

-   [ ] 3. Create BriefResponse model
    -   Define `app/models/brief_response.py`
    -   Fields: id, brief_id, response_type, decline_reason, negotiation_notes, responded_at
    -   Add response_type enum (accepted, declined, negotiating)
    -   Create database migration
    -   _Requirements: 1.7_

---

## Phase 2: Brief Template Service

-   [ ] 4. Create BriefTemplateService

    -   Create `app/services/brief_template_service.py`
    -   Implement `create_template(template_data)` method
    -   Implement `get_template(template_id)` method
    -   Implement `list_templates()` method
    -   Implement `update_template(template_id, template_data)` method
    -   _Requirements: 1.1_

-   [ ] 5. Create brief template endpoints

    -   Create `app/api/v1/brief_templates.py`
    -   POST `/api/v1/brief-templates` - Create template
    -   GET `/api/v1/brief-templates` - List templates
    -   GET `/api/v1/brief-templates/{id}` - Get template
    -   PUT `/api/v1/brief-templates/{id}` - Update template
    -   _Requirements: 1.1_

-   [ ] 6. Create default brief template
    -   Define standard template structure (JSON)
    -   Sections: campaign_overview, objectives, deliverables, compensation, guidelines
    -   Add template variables ({{campaign_name}}, {{kol_name}}, etc.)
    -   Seed default template in database
    -   _Requirements: 1.1_

---

## Phase 3: Brief Generation & Management

-   [ ] 7. Create BriefService

    -   Create `app/services/brief_service.py`
    -   Implement `generate_brief_from_campaign(campaign_id, kol_id, template_id)` method
    -   Auto-populate campaign data (name, dates, objectives, deliverables)
    -   Auto-populate KOL data (name, niche, social handles)
    -   Return Brief object with populated content
    -   _Requirements: 1.2_

-   [ ] 8. Implement brief customization

    -   Implement `update_brief(brief_id, brief_data)` method
    -   Allow editing any section of the brief
    -   Store customizations separately from template
    -   Preserve template structure
    -   _Requirements: 1.3_

-   [ ] 9. Create brief management endpoints
    -   POST `/api/v1/campaigns/{id}/briefs` - Generate brief for KOL
    -   GET `/api/v1/campaigns/{id}/briefs` - List campaign briefs
    -   GET `/api/v1/briefs/{id}` - Get brief details
    -   PUT `/api/v1/briefs/{id}` - Update brief
    -   DELETE `/api/v1/briefs/{id}` - Delete brief
    -   _Requirements: 1.2, 1.3_

---

## Phase 4: Brief Distribution

-   [ ] 10. Implement brief sending

    -   Add `send_brief(brief_id)` to BriefService
    -   Get KOL communication preferences
    -   Render brief content with all variables
    -   Call CommunicationService to send via email
    -   Update brief status to 'sent'
    -   Record sent_at timestamp
    -   _Requirements: 1.6_

-   [ ] 11. Create brief sending endpoint
    -   POST `/api/v1/briefs/{id}/send` - Send brief to KOL
    -   Validate brief is in 'draft' status
    -   Check KOL has valid email
    -   Return success/error response
    -   _Requirements: 1.6_

---

## Phase 5: Response Tracking

-   [ ] 12. Implement response recording

    -   Add `record_response(brief_id, response_type, notes)` to BriefService
    -   Create BriefResponse record
    -   Update brief status based on response type
    -   Record responded_at timestamp
    -   _Requirements: 1.7_

-   [ ] 13. Create response endpoints
    -   POST `/api/v1/briefs/{id}/response` - Record KOL response
    -   GET `/api/v1/briefs/{id}/response` - Get response details
    -   Support response types: accepted, declined, negotiating
    -   _Requirements: 1.7_

---

## Phase 6: Template Variable Rendering

-   [ ] 14. Implement variable replacement

    -   Create `render_brief_template(template, variables)` utility
    -   Replace all {{variable}} placeholders with actual values
    -   Support campaign variables (name, dates, budget, objectives)
    -   Support KOL variables (name, niche, social handles)
    -   Support deliverable variables (type, quantity, deadline)
    -   _Requirements: 1.2_

-   [ ] 15. Add variable validation
    -   Check all required variables are provided
    -   Warn if variables are missing
    -   Provide default values for optional variables
    -   _Requirements: 1.2_

---

## Phase 7: Testing & Documentation

-   [ ]\* 16. Write unit tests

    -   Test brief generation from campaign
    -   Test variable replacement
    -   Test brief customization
    -   Test response recording
    -   _Requirements: All_

-   [ ]\* 17. Write integration tests
    -   Test complete brief creation and sending flow
    -   Test brief with multiple KOLs
    -   Test response tracking
    -   _Requirements: All_

---

## Success Criteria

✅ Brief templates can be created and managed  
✅ Briefs are generated from campaign data  
✅ Briefs can be customized per KOL  
✅ Briefs can be sent via email  
✅ KOL responses are tracked  
✅ Template variables are replaced correctly  
✅ Default template is available

---

## Notes

-   Skip versioning for MVP (Phase 2)
-   Skip approval workflow for MVP (Phase 2)
-   Skip analytics for MVP (Phase 2)
-   Focus on basic brief generation and sending
-   Email is the only distribution channel in MVP
-   Advanced features in Phase 2
