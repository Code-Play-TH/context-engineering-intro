# Requirements Document - KOL Brief Management

## Introduction

This document outlines the requirements for the KOL Brief Management system, which enables creation, customization, versioning, and approval of briefs sent to individual KOLs. The system supports template-based brief creation that pulls from campaign parameters and allows Account Executives to customize for each influencer.

## Requirements

### Requirement 1: Brief Template Creation

**User Story:** As a Campaign Manager, I want to create brief templates with standard sections, so that I can quickly generate consistent briefs for KOLs.

#### Acceptance Criteria

1. WHEN a Campaign Manager creates a brief template THEN the system SHALL provide sections for campaign overview, objectives, deliverables, timeline, compensation, and guidelines
2. WHEN creating a template THEN the system SHALL allow inserting dynamic variables ({{kol_name}}, {{campaign_name}}, {{deadline}}, etc.)
3. WHEN creating a template THEN the system SHALL support rich text formatting (bold, italic, lists, links)
4. WHEN saving a template THEN the system SHALL require template name and optional description
5. WHEN a template is saved THEN the system SHALL make it available for selection when creating briefs
6. WHEN a user views template library THEN the system SHALL display all templates with preview and usage count
7. WHEN a template is marked as default THEN the system SHALL auto-select it when creating new briefs

### Requirement 2: Campaign-Based Brief Generation

**User Story:** As an Account Executive, I want to generate briefs from campaign parameters, so that I don't have to manually enter campaign details for each KOL.

#### Acceptance Criteria

1. WHEN an Account Executive generates a brief THEN the system SHALL auto-populate campaign name, objectives, timeline, and budget from campaign data
2. WHEN generating a brief THEN the system SHALL auto-populate KOL name, social handles, and contact information
3. WHEN deliverables are defined in campaign THEN the system SHALL list them in the brief with quantities and deadlines
4. WHEN brand guidelines are attached to campaign THEN the system SHALL include links or attachments in the brief
5. WHEN compensation is set for KOL THEN the system SHALL include payment terms in the brief
6. WHEN brief is generated THEN the system SHALL allow Account Executive to review and customize before sending
7. WHEN multiple KOLs are selected THEN the system SHALL generate individual briefs for each with personalized content

### Requirement 3: Brief Customization and Personalization

**User Story:** As an Account Executive, I want to customize briefs for individual KOLs, so that I can address their specific strengths and requirements.

#### Acceptance Criteria

1. WHEN an Account Executive edits a brief THEN the system SHALL allow modifying any section while preserving template structure
2. WHEN customizing a brief THEN the system SHALL allow adding KOL-specific notes or special instructions
3. WHEN customizing deliverables THEN the system SHALL allow adjusting quantities, formats, or deadlines per KOL
4. WHEN customizing compensation THEN the system SHALL allow setting KOL-specific rates or bonuses
5. WHEN adding attachments THEN the system SHALL accept images, PDFs, and documents up to 50MB total
6. WHEN saving customizations THEN the system SHALL preserve original template for future use
7. WHEN reverting changes THEN the system SHALL allow resetting to template defaults

### Requirement 4: Brief Versioning and History

**User Story:** As an Account Executive, I want to track brief versions and changes, so that I can see what was communicated to KOLs over time.

#### Acceptance Criteria

1. WHEN a brief is created THEN the system SHALL assign version 1.0
2. WHEN a brief is edited after sending THEN the system SHALL create new version (1.1, 1.2, etc.)
3. WHEN a brief is significantly revised THEN the system SHALL allow marking as major version (2.0, 3.0)
4. WHEN viewing brief history THEN the system SHALL display all versions with timestamps and who made changes
5. WHEN comparing versions THEN the system SHALL highlight differences between selected versions
6. WHEN a new version is created THEN the system SHALL optionally notify KOL of updates
7. WHEN viewing a brief THEN the system SHALL clearly indicate if it's the latest version or outdated

### Requirement 5: Brief Approval Workflow

**User Story:** As a Campaign Manager, I want to approve briefs before they're sent to KOLs, so that I can ensure quality and consistency.

#### Acceptance Criteria

1. WHEN an Account Executive submits brief for approval THEN the system SHALL change status to "pending approval"
2. WHEN a brief is pending approval THEN the system SHALL notify assigned Campaign Manager
3. WHEN a Campaign Manager reviews brief THEN the system SHALL allow approving, requesting changes, or rejecting
4. WHEN requesting changes THEN the system SHALL require comments explaining what needs to be modified
5. WHEN a brief is approved THEN the system SHALL change status to "approved" and allow sending
6. WHEN a brief is rejected THEN the system SHALL return to Account Executive with rejection reason
7. WHEN approval is required THEN the system SHALL prevent sending brief until approved

### Requirement 6: Brief Distribution and Sending

**User Story:** As an Account Executive, I want to send briefs to KOLs via their preferred communication channel, so that they receive and review the information.

#### Acceptance Criteria

1. WHEN sending a brief THEN the system SHALL check KOL's preferred communication channel (Email, Line, Discord, DM)
2. WHEN sending via email THEN the system SHALL format brief as HTML email with attachments
3. WHEN sending via messaging app THEN the system SHALL send brief as formatted message with attachment links
4. WHEN brief is sent THEN the system SHALL record send timestamp and channel used
5. WHEN brief is sent THEN the system SHALL change status to "sent" and start tracking response
6. WHEN send fails THEN the system SHALL log error and notify Account Executive
7. WHEN sending to multiple KOLs THEN the system SHALL process as background task with progress indicator

### Requirement 7: Brief Response Tracking

**User Story:** As an Account Executive, I want to track KOL responses to briefs, so that I know who has accepted, declined, or needs follow-up.

#### Acceptance Criteria

1. WHEN a brief is sent THEN the system SHALL set response status to "awaiting response"
2. WHEN a KOL views brief (email opened) THEN the system SHALL record view timestamp
3. WHEN a KOL responds THEN the system SHALL allow Account Executive to mark as "accepted", "declined", or "negotiating"
4. WHEN a KOL accepts THEN the system SHALL automatically create campaign assignment
5. WHEN a KOL declines THEN the system SHALL require recording decline reason
6. WHEN a KOL is negotiating THEN the system SHALL allow tracking negotiation notes and revised terms
7. WHEN no response after 3 days THEN the system SHALL flag for follow-up

### Requirement 8: Brief Analytics and Reporting

**User Story:** As a Campaign Manager, I want to see brief acceptance rates and response times, so that I can optimize our approach.

#### Acceptance Criteria

1. WHEN viewing brief analytics THEN the system SHALL display acceptance rate, decline rate, and no-response rate
2. WHEN viewing response times THEN the system SHALL show average time to first response and time to acceptance
3. WHEN analyzing by KOL tier THEN the system SHALL break down metrics by Nano, Micro, Mid, Macro, Mega
4. WHEN analyzing by campaign type THEN the system SHALL compare metrics across different campaign categories
5. WHEN viewing decline reasons THEN the system SHALL aggregate and display most common reasons
6. WHEN exporting analytics THEN the system SHALL provide CSV with all brief data and outcomes
7. WHEN comparing templates THEN the system SHALL show which templates have highest acceptance rates
