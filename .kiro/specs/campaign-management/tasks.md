# Implementation Tasks - Campaign Management (MVP)

## Overview

This task list covers the MVP implementation of basic campaign management with CRUD operations, client brief intake, and simple status workflow.

**Estimated Time: 4-5 days**

---

## Phase 1: Core Models

-   [x] 1. Create Campaign model

    -   Define `app/models/campaign.py` with Campaign table
    -   Fields: id, name, status, start_date, end_date, total_budget, currency, objectives, target_audience (JSON), created_by, created_at, updated_at
    -   Add CampaignStatus enum (draft, pending_approval, active, completed, cancelled)
    -   Create database migration
    -   _Requirements: 2.2_

-   [x] 2. Create ClientBrief model

    -   Define `app/models/client_brief.py`
    -   Fields: id, client_name, campaign_objective, target_audience (JSON), budget, brand_guidelines, content_requirements, status, created_by, created_at
    -   Add relationship to Campaign (one-to-many)
    -   Create database migration
    -   _Requirements: 2.1_

-   [x] 3. Create CampaignKPI model

    -   Define `app/models/campaign_kpi.py`
    -   Fields: id, campaign_id, kpi_type, target_value, actual_value, unit, created_at
    -   Add foreign key to Campaign
    -   Create database migration
    -   _Requirements: 2.2_

-   [x] 4. Create Deliverable model

    -   Define `app/models/deliverable.py`
    -   Fields: id, campaign_id, deliverable_type, quantity, deadline, status, created_at
    -   Add foreign key to Campaign
    -   Create database migration
    -   _Requirements: 2.2_

---

## Phase 2: Client Brief Service & API

-   [ ] 5. Create ClientBriefService

    -   Create `app/services/client_brief_service.py`
    -   Implement `create_brief(brief_data)` method
    -   Implement `get_brief(brief_id)` method
    -   Implement `update_brief(brief_id, brief_data)` method
    -   Implement `list_briefs(filters)` method with pagination
    -   _Requirements: 2.1_

-   [ ] 6. Create client brief endpoints
    -   Create `app/api/v1/client_briefs.py`
    -   POST `/api/v1/client-briefs` - Create client brief
    -   GET `/api/v1/client-briefs` - List briefs with filters
    -   GET `/api/v1/client-briefs/{id}` - Get brief details
    -   PUT `/api/v1/client-briefs/{id}` - Update brief
    -   Add pagination (50 items per page)
    -   _Requirements: 2.1_

---

## Phase 3: Campaign Service & API

-   [ ] 7. Create CampaignService

    -   Create `app/services/campaign_service.py`
    -   Implement `create_campaign(campaign_data, user_id)` method
    -   Implement `get_campaign(campaign_id)` method with relationships
    -   Implement `update_campaign(campaign_id, campaign_data)` method
    -   Implement `list_campaigns(filters)` method with pagination
    -   Implement `delete_campaign(campaign_id)` method (soft delete)
    -   _Requirements: 2.2, 2.5_

-   [ ] 8. Implement campaign status workflow

    -   Add `change_status(campaign_id, new_status, user_id)` to CampaignService
    -   Define allowed status transitions
    -   Validate transitions before applying
    -   Prevent deletion of active campaigns
    -   _Requirements: 2.5_

-   [ ] 9. Create campaign CRUD endpoints

    -   Create `app/api/v1/campaigns.py`
    -   POST `/api/v1/campaigns` - Create campaign
    -   GET `/api/v1/campaigns` - List campaigns with filters
    -   GET `/api/v1/campaigns/{id}` - Get campaign details
    -   PUT `/api/v1/campaigns/{id}` - Update campaign
    -   DELETE `/api/v1/campaigns/{id}` - Delete campaign
    -   _Requirements: 2.2, 2.5_

-   [ ] 10. Create campaign status endpoint
    -   PUT `/api/v1/campaigns/{id}/status` - Change campaign status
    -   Validate status transitions
    -   Return error for invalid transitions
    -   _Requirements: 2.5_

---

## Phase 4: KPI & Deliverables Management

-   [ ] 11. Add KPI management to CampaignService

    -   Implement `add_kpi(campaign_id, kpi_data)` method
    -   Implement `update_kpi(kpi_id, kpi_data)` method
    -   Implement `delete_kpi(kpi_id)` method
    -   _Requirements: 2.2_

-   [ ] 12. Create KPI endpoints

    -   POST `/api/v1/campaigns/{id}/kpis` - Add KPI to campaign
    -   PUT `/api/v1/campaigns/{id}/kpis/{kpi_id}` - Update KPI
    -   DELETE `/api/v1/campaigns/{id}/kpis/{kpi_id}` - Delete KPI
    -   _Requirements: 2.2_

-   [ ] 13. Add deliverable management to CampaignService

    -   Implement `add_deliverable(campaign_id, deliverable_data)` method
    -   Implement `update_deliverable(deliverable_id, deliverable_data)` method
    -   Implement `delete_deliverable(deliverable_id)` method
    -   _Requirements: 2.2_

-   [ ] 14. Create deliverable endpoints
    -   POST `/api/v1/campaigns/{id}/deliverables` - Add deliverable
    -   PUT `/api/v1/campaigns/{id}/deliverables/{deliverable_id}` - Update deliverable
    -   DELETE `/api/v1/campaigns/{id}/deliverables/{deliverable_id}` - Delete deliverable
    -   _Requirements: 2.2_

---

## Phase 5: Campaign Duplication (MVP - Basic)

-   [ ] 15. Implement campaign duplication
    -   Add `duplicate_campaign(campaign_id)` to CampaignService
    -   Copy campaign data (exclude dates and status)
    -   Copy KPIs and deliverables
    -   Set status to 'draft'
    -   POST `/api/v1/campaigns/{id}/duplicate` endpoint
    -   _Requirements: 2.7_

---

## Phase 6: Validation & Business Logic

-   [ ] 16. Add campaign validation

    -   Validate end_date is after start_date
    -   Validate budget is positive
    -   Validate required fields
    -   Add validation to create/update methods
    -   _Requirements: 2.2_

-   [ ] 17. Add permission checks
    -   Campaign Managers can create/update campaigns
    -   Only Admins can delete campaigns
    -   Account Executives can view campaigns
    -   Viewers have read-only access
    -   _Requirements: 2.5_

---

## Phase 7: Testing & Documentation

-   [ ]\* 18. Write unit tests

    -   Test campaign CRUD operations
    -   Test status transition validation
    -   Test KPI and deliverable management
    -   Test campaign duplication
    -   _Requirements: All_

-   [ ]\* 19. Write integration tests
    -   Test complete campaign creation flow
    -   Test campaign with KPIs and deliverables
    -   Test permission enforcement
    -   _Requirements: All_

---

## Success Criteria

✅ Users can create campaigns from client briefs  
✅ Campaigns have proper status workflow  
✅ KPIs and deliverables can be added to campaigns  
✅ Campaign list supports filtering and pagination  
✅ Campaign duplication works correctly  
✅ Date and budget validation works  
✅ Permissions are enforced correctly  
✅ Database migrations run successfully

---

## Notes

-   Skip timeline visualization for MVP (Phase 3)
-   Skip budget tracking for MVP (Phase 2)
-   Skip team assignment for MVP (Phase 2)
-   Skip milestone management for MVP (Phase 3)
-   Focus on basic CRUD and status workflow
-   Advanced features can be added in Phase 2
