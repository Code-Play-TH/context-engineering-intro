# Implementation Tasks - Report Generation & Templates (MVP)

## Overview

This task list covers the MVP implementation of report template creation, PowerPoint/PDF generation, and basic AI-powered template analysis.

**Estimated Time: 6-7 days**

---

## Phase 1: Core Models

-   [x] 1. Create ReportTemplate model

    -   Define `app/models/report_template.py` with ReportTemplate table
    -   Fields: id, name, description, template_type, is_shared, structure (JSON), variables (Array), created_by, created_at, usage_count
    -   Add template_type enum (powerpoint, pdf)
    -   Create database migration
    -   _Requirements: 1.1, 5.1_

-   [x] 2. Create ReportGeneration model

    -   Define `app/models/report_generation.py`
    -   Fields: id, campaign_id, template_id, report_type, status, file_path, download_url, error_message, generated_by, generated_at, expires_at
    -   Add status enum (pending, processing, completed, failed)
    -   Create database migration
    -   _Requirements: 3.1, 4.1_

-   [x] 3. Create ReportSchedule model

    -   Define `app/models/report_schedule.py`
    -   Fields: id, campaign_id, template_id, frequency, recipients (Array), is_active, last_generated_at, next_generation_at, created_at
    -   Add frequency enum (daily, weekly, monthly, campaign_end)
    -   Create database migration
    -   _Requirements: 8.1, 8.2_

---

## Phase 2: Template Management Service

-   [x] 4. Create ReportTemplateService

    -   Create `app/services/report_template_service.py`
    -   Implement `create_template(template_data)` method
    -   Implement `get_template(template_id)` method
    -   Implement `list_templates(filters)` method with search and filtering
    -   Implement `update_template(template_id, template_data)` method
    -   Implement `duplicate_template(template_id)` method
    -   _Requirements: 1.1, 5.2, 5.3_

-   [x] 5. Create template management endpoints

    -   Create `app/api/v1/report_templates.py`
    -   POST `/api/v1/report-templates` - Create template
    -   GET `/api/v1/report-templates` - List templates with search/filter
    -   GET `/api/v1/report-templates/{id}` - Get template details
    -   PUT `/api/v1/report-templates/{id}` - Update template
    -   DELETE `/api/v1/report-templates/{id}` - Delete template
    -   POST `/api/v1/report-templates/{id}/duplicate` - Duplicate template
    -   _Requirements: 1.1, 5.1, 5.2_

-   [x] 6. Create default report templates

    -   Define standard PowerPoint template structure (JSON)
    -   Create basic PDF template layout
    -   Include common variables ({{campaign_name}}, {{kol_count}}, {{total_reach}}, etc.)
    -   Seed default templates in database
    -   _Requirements: 1.1, 6.1_

---

## Phase 3: Data Population Service

-   [x] 7. Create DataPopulationService

    -   Create `app/services/data_population_service.py`
    -   Implement `populate_template_variables(template, campaign_id)` method
    -   Implement `fetch_campaign_metrics(campaign_id)` method
    -   Implement `calculate_aggregated_metrics(campaign_id)` method
    -   Handle missing data with "N/A" placeholders
    -   _Requirements: 6.1, 6.2, 6.6_

-   [x] 8. Define variable mapping system

    -   Create comprehensive variable mapping dictionary
    -   Map template variables to database queries
    -   Support campaign, KOL, and metrics variables
    -   Add number formatting (commas, decimals, currency)
    -   _Requirements: 6.1, 6.3, 6.4, 6.5_

-   [x] 9. Implement chart data generation

    -   Create `generate_chart_data(chart_config, campaign_id)` method
    -   Support bar, line, pie, and donut charts
    -   Fetch KOL performance data for charts
    -   Generate time-series data for trend charts
    -   _Requirements: 7.1, 7.2, 7.4_

---

## Phase 4: PowerPoint Generation

-   [x] 10. Install and configure python-pptx

    -   Add python-pptx dependency to requirements
    -   Create PowerPoint generation utilities
    -   Set up slide layouts and styling
    -   _Requirements: 3.1_

-   [x] 11. Create PowerPointGenerationService

    -   Create `app/services/powerpoint_generation_service.py`
    -   Implement `generate_powerpoint(campaign_id, template_id)` method
    -   Add text elements with variable replacement
    -   Add chart elements with dynamic data
    -   Add table elements with campaign metrics
    -   Add image elements (KOL profile pictures, logos)
    -   _Requirements: 3.1, 3.2, 3.3, 3.4_

-   [x] 12. Implement chart generation for PowerPoint

    -   Create native PowerPoint charts (not images)
    -   Support multiple chart types
    -   Apply template styling (colors, fonts)
    -   Handle chart data formatting
    -   _Requirements: 3.2, 7.1, 7.6, 7.7_

---

## Phase 5: PDF Generation

-   [x] 13. Install and configure ReportLab

    -   Add ReportLab dependency to requirements
    -   Set up PDF document templates
    -   Configure page layouts and styling
    -   _Requirements: 4.1_

-   [x] 14. Create PDFGenerationService

    -   Create `app/services/pdf_generation_service.py`
    -   Implement `generate_pdf(campaign_id, template_id)` method
    -   Add text paragraphs with styling
    -   Add tables with campaign data
    -   Add chart images (generated with matplotlib)
    -   Add images and logos
    -   _Requirements: 4.1, 4.2, 4.3, 4.4_

-   [x] 15. Implement chart image generation

    -   Use matplotlib to generate chart images
    -   Support various chart types
    -   Apply consistent styling
    -   Save as high-quality PNG for PDF embedding
    -   _Requirements: 4.3, 7.1_

---

## Phase 6: Report Generation Service

-   [x] 16. Create ReportGenerationService

    -   Create `app/services/report_generation_service.py`
    -   Implement `generate_report(campaign_id, template_id, report_type)` method
    -   Process as background Celery task
    -   Update generation status and progress
    -   Handle errors and provide detailed error messages
    -   _Requirements: 3.7, 4.7_

-   [x] 17. Create report generation endpoints

    -   POST `/api/v1/campaigns/{id}/reports/generate` - Generate report
    -   GET `/api/v1/campaigns/{id}/reports` - List generated reports
    -   GET `/api/v1/reports/{id}/download` - Download report file
    -   GET `/api/v1/reports/{id}/status` - Get generation status
    -   _Requirements: 3.1, 4.1, 9.1_

-   [x] 18. Implement file storage and cleanup

    -   Store generated reports in `uploads/reports/` directory
    -   Generate secure download URLs with expiration (24 hours)
    -   Clean up expired files daily
    -   Archive old reports to cold storage after 90 days
    -   _Requirements: 9.1, 9.4, 10.1_

---

## Phase 7: AI Template Analysis (Basic)

-   [ ] 19. Create AITemplateService

    -   Create `app/services/ai_template_service.py`
    -   Implement `analyze_sample_file(file)` method for PowerPoint files
    -   Extract text content and layout structure
    -   Use OpenAI API to identify variable placeholders
    -   Generate template structure JSON
    -   _Requirements: 2.1, 2.2, 2.3_

-   [ ] 20. Create AI template analysis endpoints

    -   POST `/api/v1/report-templates/analyze-sample` - Upload and analyze sample
    -   POST `/api/v1/report-templates/generate-from-sample` - Generate template from analysis
    -   Return suggested variable mappings for user review
    -   _Requirements: 2.1, 2.5, 2.6_

-   [ ] 21. Implement sample file processing
    -   Support PowerPoint (.pptx) file upload (up to 50MB)
    -   Extract slide content and layout information
    -   Identify potential variable locations
    -   Preserve styling information (fonts, colors)
    -   _Requirements: 2.1, 2.4, 2.7_

---

## Phase 8: Report Scheduling (Basic)

-   [ ] 22. Create ReportSchedulingService

    -   Create `app/services/report_scheduling_service.py`
    -   Implement `schedule_report(campaign_id, template_id, schedule_data)` method
    -   Implement `process_scheduled_reports()` Celery task
    -   Send email notifications with download links
    -   _Requirements: 8.1, 8.3_

-   [ ] 23. Create scheduling endpoints

    -   POST `/api/v1/campaigns/{id}/reports/schedule` - Schedule report
    -   GET `/api/v1/campaigns/{id}/reports/schedules` - List schedules
    -   PUT `/api/v1/reports/schedules/{id}` - Update schedule
    -   DELETE `/api/v1/reports/schedules/{id}` - Cancel schedule
    -   _Requirements: 8.1, 8.6, 8.7_

-   [ ] 24. Set up scheduled report processing
    -   Configure Celery Beat for daily report generation check
    -   Process due scheduled reports
    -   Handle generation failures with retry logic
    -   _Requirements: 8.4, 8.5_

---

## Phase 9: Report History and Sharing

-   [ ] 25. Implement report history

    -   Store all generated reports with metadata
    -   Display report history in campaign view
    -   Allow downloading previous reports
    -   Show generation date and template used
    -   _Requirements: 9.1, 9.2, 9.6_

-   [ ] 26. Create sharing functionality

    -   Generate shareable links valid for 7 days
    -   Allow email sharing with custom message
    -   Support multiple recipients
    -   No login required for shared links
    -   _Requirements: 10.2, 10.3, 10.4, 10.5_

-   [ ] 27. Add export options
    -   Provide CSV export of raw campaign data
    -   Optimize report layout for printing
    -   Handle page breaks and margins properly
    -   _Requirements: 10.6, 10.7_

---

## Phase 10: Testing & Documentation

-   [ ]\* 28. Write unit tests

    -   Test variable replacement logic
    -   Test chart data generation
    -   Test PowerPoint generation
    -   Test PDF generation
    -   Test template validation
    -   _Requirements: All_

-   [ ]\* 29. Write integration tests
    -   Test end-to-end PowerPoint generation
    -   Test end-to-end PDF generation
    -   Test AI template analysis
    -   Test scheduled report generation
    -   _Requirements: All_

---

## Success Criteria

✅ Users can create and manage report templates  
✅ PowerPoint reports are generated with dynamic data  
✅ PDF reports are generated with charts and tables  
✅ AI can analyze sample files and suggest templates  
✅ Reports can be scheduled for automatic generation  
✅ Report history is maintained with download links  
✅ Templates can be shared across the organization  
✅ Charts are generated with campaign data  
✅ Variable replacement works correctly  
✅ File storage and cleanup works properly

---

## Notes

-   MVP focuses on basic PowerPoint and PDF generation
-   Skip advanced template builder UI for MVP (Phase 2)
-   Skip complex chart customization for MVP (Phase 2)
-   Skip advanced AI analysis for MVP (Phase 2)
-   Use simple scheduling (daily, weekly, monthly)
-   Advanced sharing features can be added in Phase 2
-   Focus on core functionality and reliability
