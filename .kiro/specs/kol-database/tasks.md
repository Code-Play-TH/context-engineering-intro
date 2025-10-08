# Implementation Tasks - KOL Database Management (MVP)

## Overview

This task list covers the MVP implementation of KOL database with manual entry, CSV import, and basic search functionality.

**Estimated Time: 5-6 days**

---

## Phase 1: Core Models

-   [ ] 1. Create KOL model

    -   Define `app/models/kol.py` with KOL table
    -   Fields: id, name, email, phone, location, niche (Array), tier, tags (Array), notes, status, created_at, updated_at
    -   Add tier enum (nano, micro, mid, macro, mega)
    -   Create database migration
    -   _Requirements: 1.1_

-   [ ] 2. Create SocialHandle model

    -   Define `app/models/social_handle.py`
    -   Fields: id, kol_id, platform, handle, url, follower_count, is_verified, is_active, last_enriched_at, created_at
    -   Add platform enum (instagram, tiktok, youtube, twitter, facebook)
    -   Add foreign key to KOL
    -   Create database migration
    -   _Requirements: 1.1_

-   [ ] 3. Create ImportJob model
    -   Define `app/models/import_job.py`
    -   Fields: id, filename, file_path, status, total_rows, processed_rows, success_count, error_count, errors (JSON), created_by, created_at, completed_at
    -   Add status enum (pending, validating, processing, completed, failed)
    -   Create database migration
    -   _Requirements: 1.3_

---

## Phase 2: KOL Service & Basic CRUD

-   [ ] 4. Create KOLService

    -   Create `app/services/kol_service.py`
    -   Implement `create_kol(kol_data)` method
    -   Implement `get_kol(kol_id)` method with social handles
    -   Implement `update_kol(kol_id, kol_data)` method
    -   Implement `soft_delete_kol(kol_id)` method
    -   Implement `list_kols(filters)` method with pagination
    -   _Requirements: 1.1_

-   [ ] 5. Create KOL CRUD endpoints

    -   Create `app/api/v1/kols.py`
    -   POST `/api/v1/kols` - Create KOL
    -   GET `/api/v1/kols` - List KOLs with filters
    -   GET `/api/v1/kols/{id}` - Get KOL details
    -   PUT `/api/v1/kols/{id}` - Update KOL
    -   DELETE `/api/v1/kols/{id}` - Soft delete KOL
    -   _Requirements: 1.1_

-   [ ] 6. Add social handle management
    -   Implement `add_social_handle(kol_id, handle_data)` in KOLService
    -   Implement `update_social_handle(handle_id, handle_data)` method
    -   Implement `delete_social_handle(handle_id)` method
    -   POST `/api/v1/kols/{id}/social-handles` endpoint
    -   PUT `/api/v1/kols/{id}/social-handles/{handle_id}` endpoint
    -   DELETE `/api/v1/kols/{id}/social-handles/{handle_id}` endpoint
    -   _Requirements: 1.1_

---

## Phase 3: Search & Filtering

-   [ ] 7. Implement basic search functionality

    -   Add `search_kols(query, filters)` to KOLService
    -   Support search by name (case-insensitive)
    -   Support search by email
    -   Support search by social handle
    -   Use PostgreSQL ILIKE for fuzzy matching
    -   _Requirements: 1.2_

-   [ ] 8. Implement filtering

    -   Add filter by niche (array contains)
    -   Add filter by location
    -   Add filter by tier
    -   Add filter by status (active/inactive)
    -   Add filter by tags
    -   Support multiple filters with AND logic
    -   _Requirements: 1.2_

-   [ ] 9. Add sorting and pagination
    -   Support sort by name, created_at, updated_at
    -   Default pagination: 50 items per page
    -   Add cursor-based pagination for large datasets
    -   Return total count in response
    -   _Requirements: 1.2_

---

## Phase 4: CSV Import

-   [ ] 10. Create ImportService

    -   Create `app/services/import_service.py`
    -   Implement `upload_import_file(file)` method
    -   Save file to `uploads/imports/pending/`
    -   Create ImportJob record
    -   Return job_id for tracking
    -   _Requirements: 1.3_

-   [ ] 11. Implement import validation

    -   Implement `validate_import_data(job_id)` method
    -   Check required fields (name, at least one social handle)
    -   Validate email format
    -   Validate URL format for social handles
    -   Check for duplicates (name similarity >85%)
    -   Store validation errors in ImportJob
    -   _Requirements: 1.3_

-   [ ] 12. Implement import processing

    -   Implement `process_import(job_id)` method
    -   Process rows in batches of 100
    -   Create KOL records
    -   Create SocialHandle records
    -   Update ImportJob progress
    -   Move file to processed/ or failed/ folder
    -   _Requirements: 1.3_

-   [ ] 13. Create import endpoints
    -   POST `/api/v1/kols/import` - Upload CSV file
    -   GET `/api/v1/kols/import/{job_id}` - Get import status
    -   POST `/api/v1/kols/import/{job_id}/validate` - Validate import
    -   POST `/api/v1/kols/import/{job_id}/process` - Process import
    -   _Requirements: 1.3_

---

## Phase 5: Tier Calculation & Tagging

-   [ ] 14. Implement tier calculation

    -   Add `calculate_tier(kol_id)` to KOLService
    -   Get max follower count across all platforms
    -   Assign tier based on follower count
    -   Auto-update tier when follower count changes
    -   _Requirements: 1.8_

-   [ ] 15. Implement tagging system
    -   Add `add_tag(kol_id, tag)` to KOLService
    -   Add `remove_tag(kol_id, tag)` method
    -   Suggest existing similar tags (prevent duplicates)
    -   POST `/api/v1/kols/{id}/tags` endpoint
    -   DELETE `/api/v1/kols/{id}/tags/{tag}` endpoint
    -   _Requirements: 1.8_

---

## Phase 6: Validation & Business Logic

-   [ ] 16. Add KOL validation

    -   Validate at least one social handle required
    -   Validate email format if provided
    -   Validate phone format if provided
    -   Prevent deletion if KOL has active campaigns
    -   _Requirements: 1.1_

-   [ ] 17. Add duplicate detection (basic)
    -   Check for exact email match
    -   Check for exact social handle match
    -   Warn user if potential duplicate found
    -   Allow user to proceed or cancel
    -   _Requirements: 1.6_

---

## Phase 7: Testing & Documentation

-   [ ]\* 18. Write unit tests

    -   Test KOL CRUD operations
    -   Test search and filtering
    -   Test CSV import validation
    -   Test tier calculation
    -   _Requirements: All_

-   [ ]\* 19. Write integration tests
    -   Test complete KOL creation flow
    -   Test CSV import end-to-end
    -   Test duplicate detection
    -   _Requirements: All_

---

## Success Criteria

✅ Users can manually create KOL profiles  
✅ Social handles can be added to KOLs  
✅ KOL search works with filters  
✅ CSV import validates and processes correctly  
✅ Tier is calculated automatically  
✅ Tags can be added and managed  
✅ Duplicate detection warns users  
✅ Pagination works for large datasets

---

## Notes

-   Skip API-based discovery for MVP (Phase 2)
-   Skip third-party integration for MVP (Phase 2)
-   Skip advanced duplicate detection for MVP (Phase 2)
-   Skip profile enrichment for MVP (Phase 2)
-   Skip Elasticsearch for MVP (use PostgreSQL full-text search)
-   Focus on manual entry and CSV import
-   Advanced features in Phase 2
