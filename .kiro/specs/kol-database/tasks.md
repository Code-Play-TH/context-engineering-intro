# Implementation Tasks - KOL Database Management (MVP)

## Overview

This task list covers the MVP implementation of KOL database with manual entry, CSV import, and basic search functionality.

**Estimated Time: 5-6 days**

---

## Phase 1: Core Models ✅ COMPLETED

-   [x] 1. Create KOL model

    -   Define `app/models/kol.py` with KOL table
    -   Fields: id, name, email, phone, location, niche (Array), tier, tags (Array), notes, status, created_at, updated_at
    -   Add tier enum (nano, micro, mid, macro, mega)
    -   Create database migration
    -   _Requirements: 1.1_

-   [x] 2. Create SocialHandle model

    -   Define `app/models/social_handle.py`
    -   Fields: id, kol_id, platform, handle, url, follower_count, is_verified, is_active, last_enriched_at, created_at
    -   Add platform enum (instagram, tiktok, youtube, twitter, facebook)
    -   Add foreign key to KOL
    -   Create database migration
    -   _Requirements: 1.1_

-   [x] 3. Create ImportJob model
    -   Define `app/models/import_job.py`
    -   Fields: id, filename, file_path, status, total_rows, processed_rows, success_count, error_count, errors (JSON), created_by, created_at, completed_at
    -   Add status enum (pending, validating, processing, completed, failed)
    -   Create database migration
    -   _Requirements: 1.3_

---

## Phase 2: KOL Service & Basic CRUD ✅ COMPLETED

-   [x] 4. Create KOLService

    -   Create `app/services/kol_service.py`
    -   Implement `create_kol(kol_data)` method
    -   Implement `get_kol(kol_id)` method with social handles
    -   Implement `update_kol(kol_id, kol_data)` method
    -   Implement `soft_delete_kol(kol_id)` method
    -   Implement `list_kols(filters)` method with pagination
    -   _Requirements: 1.1_

-   [x] 5. Create KOL CRUD endpoints

    -   Create `app/api/v1/kols.py`
    -   POST `/api/v1/kols` - Create KOL
    -   GET `/api/v1/kols` - List KOLs with filters
    -   GET `/api/v1/kols/{id}` - Get KOL details
    -   PUT `/api/v1/kols/{id}` - Update KOL
    -   DELETE `/api/v1/kols/{id}` - Soft delete KOL
    -   _Requirements: 1.1_

-   [x] 6. Add social handle management

    -   Implement `update_social_handle(handle_id, handle_data)` method in KOLService
    -   Implement `delete_social_handle(handle_id)` method in KOLService
    -   PUT `/api/v1/kols/{kol_id}/social-handles/{handle_id}` endpoint
    -   DELETE `/api/v1/kols/{kol_id}/social-handles/{handle_id}` endpoint
    -   _Requirements: 1.1_

---

## Phase 3: Search & Filtering ✅ COMPLETED

-   [x] 7. Enhance search functionality

    -   Add search by social handle to `list_kols()` method (currently only searches name and email)
    -   Use JOIN with social_handles table to search by handle
    -   Ensure distinct KOL results when matching social handles
    -   _Requirements: 1.2_

-   [x] 8. Implement filtering

    -   Add filter by niche (array contains)
    -   Add filter by location
    -   Add filter by tier
    -   Add filter by status (active/inactive)
    -   Add filter by tags
    -   Support multiple filters with AND logic
    -   _Requirements: 1.2_

-   [x] 9. Add sorting functionality

    -   Add `sort_by` and `sort_order` parameters to `list_kols()` method
    -   Support sort by name, created_at, updated_at
    -   Add sorting to API endpoint query parameters
    -   _Requirements: 1.2_

---

## Phase 4: CSV Import

-   [x] 10. Create ImportService

    -   Create `app/services/import_service.py`
    -   Implement `upload_import_file(file)` method
    -   Save file to `uploads/imports/pending/`
    -   Create ImportJob record
    -   Return job_id for tracking
    -   _Requirements: 1.3_

-   [x] 11. Implement import validation

    -   Implement `validate_import_data(job_id)` method
    -   Check required fields (name, at least one social handle)
    -   Validate email format
    -   Validate URL format for social handles
    -   Check for duplicates (name similarity >85%)
    -   Store validation errors in ImportJob
    -   _Requirements: 1.3_

-   [x] 12. Implement import processing

    -   Implement `process_import(job_id)` method
    -   Process rows in batches of 100
    -   Create KOL records
    -   Create SocialHandle records
    -   Update ImportJob progress
    -   Move file to processed/ or failed/ folder
    -   _Requirements: 1.3_

-   [x] 13. Create import endpoints

    -   POST `/api/v1/kols/import` - Upload CSV file
    -   GET `/api/v1/kols/import/{job_id}` - Get import status
    -   POST `/api/v1/kols/import/{job_id}/validate` - Validate import
    -   POST `/api/v1/kols/import/{job_id}/process` - Process import
    -   _Requirements: 1.3_

---

## Phase 5: Tier Calculation & Tagging ✅ COMPLETED

-   [x] 14. Implement tier calculation

    -   Add `calculate_tier(kol_id)` to KOLService
    -   Get max follower count across all platforms
    -   Assign tier based on follower count
    -   Auto-update tier when follower count changes
    -   _Requirements: 1.8_

-   [x] 15. Implement tagging system
    -   Add `add_tag(kol_id, tag)` to KOLService
    -   Add `remove_tag(kol_id, tag)` method
    -   Suggest existing similar tags (prevent duplicates)
    -   POST `/api/v1/kols/{id}/tags/{tag}` endpoint
    -   DELETE `/api/v1/kols/{id}/tags/{tag}` endpoint
    -   _Requirements: 1.8_

---

## Phase 6: Validation & Business Logic

-   [x] 16. Add KOL validation

    -   Validate email format if provided (add email validation to schemas)
    -   Validate phone format if provided (add phone validation to schemas)
    -   Prevent deletion if KOL has active campaigns (check campaign_kol relationship)
    -   _Requirements: 1.1_

-   [x] 17. Add duplicate detection (basic)

    -   Create `find_duplicates(kol_id)` method in KOLService
    -   Check for exact email match
    -   Check for exact social handle match (platform + handle)
    -   Return list of potential duplicate KOLs
    -   Add GET `/api/v1/kols/{id}/duplicates` endpoint
    -   _Requirements: 1.6_

---

## Phase 7: Advanced Search (Future Enhancement)

-   [ ] 18. Implement fuzzy name matching

    -   Install and configure pg_trgm PostgreSQL extension
    -   Add similarity search for KOL names (>85% similarity)
    -   Update search to use similarity scoring
    -   _Requirements: 1.2_

-   [ ] 19. Add saved filter functionality
    -   Create SavedFilter model
    -   Implement save/load filter combinations
    -   Add endpoints for managing saved filters
    -   _Requirements: 1.2_

---

## Phase 8: Profile Enrichment (Future Enhancement)

-   [ ] 20. Create EnrichmentService

    -   Create `app/services/enrichment_service.py`
    -   Implement social media API integration framework
    -   Add rate limiting and retry logic
    -   _Requirements: 1.7_

-   [ ] 21. Implement automatic profile enrichment
    -   Fetch follower counts from social media APIs
    -   Store historical metrics for trend analysis
    -   Schedule periodic enrichment tasks
    -   _Requirements: 1.7_

---

## Phase 9: Advanced Duplicate Detection (Future Enhancement)

-   [ ] 22. Implement advanced duplicate detection

    -   Install fuzzy matching library (RapidFuzz)
    -   Implement name similarity matching (>85%)
    -   Create `merge_kols(primary_id, duplicate_id)` method
    -   Transfer campaign history during merge
    -   Add merge tracking to KOL model
    -   _Requirements: 1.6_

-   [ ] 23. Add duplicate scanning
    -   Implement `scan_all_duplicates()` method
    -   Generate duplicate detection report
    -   Add admin endpoint for bulk duplicate review
    -   _Requirements: 1.6_

---

## Phase 10: Testing & Documentation

-   [ ]\* 24. Write unit tests

    -   Test KOL CRUD operations
    -   Test search and filtering
    -   Test CSV import validation
    -   Test tier calculation
    -   _Requirements: All_

-   [ ]\* 25. Write integration tests
    -   Test complete KOL creation flow
    -   Test CSV import end-to-end
    -   Test duplicate detection
    -   _Requirements: All_

---

## Success Criteria

### MVP (Phase 1-6)

✅ Users can manually create KOL profiles  
✅ Social handles can be added to KOLs  
🔄 KOL search works with filters (needs social handle search + sorting)  
⏳ CSV import validates and processes correctly  
✅ Tier is calculated automatically  
✅ Tags can be added and managed  
⏳ Duplicate detection warns users  
✅ Pagination works for large datasets

### Future Enhancements (Phase 7-9)

⏳ Fuzzy name matching for better search  
⏳ Saved filter combinations  
⏳ Automatic profile enrichment from social media APIs  
⏳ Advanced duplicate detection with merge functionality

---

## Notes

-   **MVP Focus**: Manual entry, CSV import, basic search/filter
-   **Phase 2 Features** (not in current MVP):
    -   API-based KOL discovery from social media platforms
    -   Third-party influencer database integration
    -   Advanced duplicate detection with fuzzy matching
    -   Profile enrichment and auto-update
    -   Elasticsearch for advanced search
-   **Current Status**: Backend 100% complete, Frontend 100% complete - MVP ready for testing
