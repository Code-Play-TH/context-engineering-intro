# Requirements Document - Follow-up Automation

## Introduction

This document outlines the requirements for the Follow-up Automation system, which manages scheduled reminders and automated follow-ups with KOLs at configurable intervals (1, 3, and 5 days). The system tracks communication history, allows manual overrides, and ensures timely engagement throughout the campaign lifecycle.

## Requirements

### Requirement 1: Automated Follow-up Scheduling

**User Story:** As an Account Executive, I want to automatically schedule follow-ups when I send briefs or messages, so that I don't forget to check in with KOLs.

#### Acceptance Criteria

1. WHEN a brief is sent THEN the system SHALL automatically schedule follow-ups at 1, 3, and 5 days if no response
2. WHEN a message is sent THEN the system SHALL allow Account Executive to enable/disable auto follow-up
3. WHEN scheduling follow-ups THEN the system SHALL allow customizing intervals (e.g., 2, 4, 7 days instead of defaults)
4. WHEN a KOL responds THEN the system SHALL automatically cancel pending follow-ups
5. WHEN a follow-up is scheduled THEN the system SHALL display in Account Executive's task list with due date
6. WHEN multiple follow-ups are pending THEN the system SHALL prioritize by urgency and campaign deadline
7. WHEN campaign is cancelled THEN the system SHALL cancel all pending follow-ups for that campaign

### Requirement 2: Follow-up Reminder Notifications

**User Story:** As an Account Executive, I want to receive reminders when follow-ups are due, so that I can reach out to KOLs at the right time.

#### Acceptance Criteria

1. WHEN a follow-up is due THEN the system SHALL send in-app notification to Account Executive
2. WHEN a follow-up is due THEN the system SHALL optionally send email reminder based on user preferences
3. WHEN notification is clicked THEN the system SHALL open the KOL conversation with draft follow-up message
4. WHEN follow-up is overdue (not completed within 24 hours) THEN the system SHALL send escalation notification
5. WHEN multiple follow-ups are due THEN the system SHALL group notifications by campaign
6. WHEN Account Executive is on vacation THEN the system SHALL reassign follow-ups to backup team member
7. WHEN follow-up is completed THEN the system SHALL mark as done and remove from task list

### Requirement 3: Follow-up Message Templates

**User Story:** As an Account Executive, I want to use pre-written follow-up templates, so that I can quickly send consistent reminders.

#### Acceptance Criteria

1. WHEN creating follow-up template THEN the system SHALL allow different templates for 1st, 2nd, and 3rd follow-up
2. WHEN creating template THEN the system SHALL support variables ({{kol_name}}, {{days_since_sent}}, {{deadline}}, etc.)
3. WHEN follow-up is due THEN the system SHALL suggest appropriate template based on follow-up number
4. WHEN using template THEN the system SHALL allow editing before sending
5. WHEN template references previous message THEN the system SHALL include quote or summary
6. WHEN saving template THEN the system SHALL categorize by purpose (brief follow-up, deliverable reminder, payment follow-up)
7. WHEN template has high response rate THEN the system SHALL mark as "Effective" in template library

### Requirement 4: Manual Follow-up Override

**User Story:** As an Account Executive, I want to manually trigger or skip follow-ups, so that I have control over communication timing.

#### Acceptance Criteria

1. WHEN viewing scheduled follow-ups THEN the system SHALL allow sending immediately instead of waiting
2. WHEN sending early THEN the system SHALL cancel the scheduled follow-up and reschedule next one
3. WHEN skipping a follow-up THEN the system SHALL require reason (e.g., "Spoke on phone", "KOL on vacation")
4. WHEN skipping a follow-up THEN the system SHALL optionally reschedule for later date
5. WHEN rescheduling THEN the system SHALL allow selecting new date and time
6. WHEN manual follow-up is sent THEN the system SHALL reset the follow-up sequence
7. WHEN Account Executive marks "Do not follow up" THEN the system SHALL cancel all pending follow-ups for that KOL

### Requirement 5: Follow-up Escalation Rules

**User Story:** As a Campaign Manager, I want follow-ups to escalate when KOLs don't respond, so that important communications don't fall through the cracks.

#### Acceptance Criteria

1. WHEN 3rd follow-up receives no response THEN the system SHALL escalate to Campaign Manager
2. WHEN escalation occurs THEN the system SHALL send notification with full communication history
3. WHEN Campaign Manager reviews escalation THEN the system SHALL allow assigning to different Account Executive
4. WHEN deadline is approaching (within 3 days) and no response THEN the system SHALL escalate immediately
5. WHEN escalation is resolved THEN the system SHALL record resolution action and outcome
6. WHEN configuring escalation rules THEN the system SHALL allow setting custom thresholds per campaign type
7. WHEN VIP KOL doesn't respond THEN the system SHALL escalate after 2nd follow-up instead of 3rd

### Requirement 6: Follow-up Performance Tracking

**User Story:** As a Campaign Manager, I want to track follow-up effectiveness, so that I can optimize our communication strategy.

#### Acceptance Criteria

1. WHEN viewing follow-up analytics THEN the system SHALL display response rate by follow-up number (1st, 2nd, 3rd)
2. WHEN analyzing timing THEN the system SHALL show which intervals (1, 3, 5 days) have highest response rates
3. WHEN comparing templates THEN the system SHALL show response rates for each template
4. WHEN analyzing by KOL tier THEN the system SHALL break down metrics by Nano, Micro, Mid, Macro, Mega
5. WHEN viewing Account Executive performance THEN the system SHALL show follow-up completion rate and average response time
6. WHEN exporting analytics THEN the system SHALL provide CSV with all follow-up data and outcomes
7. WHEN identifying trends THEN the system SHALL highlight best practices (e.g., "2-day interval has 15% higher response rate")

### Requirement 7: Campaign-Specific Follow-up Rules

**User Story:** As a Campaign Manager, I want to set custom follow-up rules per campaign, so that I can adjust strategy based on campaign urgency and type.

#### Acceptance Criteria

1. WHEN creating a campaign THEN the system SHALL allow setting custom follow-up intervals
2. WHEN campaign is urgent THEN the system SHALL allow setting shorter intervals (e.g., 12 hours, 1 day, 2 days)
3. WHEN campaign is long-term THEN the system SHALL allow setting longer intervals (e.g., 3 days, 7 days, 14 days)
4. WHEN setting campaign rules THEN the system SHALL allow specifying maximum number of follow-ups before escalation
5. WHEN campaign has specific communication preferences THEN the system SHALL enforce preferred channels for follow-ups
6. WHEN campaign rules are set THEN the system SHALL apply to all KOLs in that campaign
7. WHEN KOL has individual preferences THEN the system SHALL allow overriding campaign rules per KOL

### Requirement 8: Follow-up History and Audit Trail

**User Story:** As an Account Executive, I want to see complete follow-up history, so that I know what communications have been sent and when.

#### Acceptance Criteria

1. WHEN viewing KOL profile THEN the system SHALL display all follow-ups with status (scheduled, sent, skipped, responded)
2. WHEN viewing follow-up details THEN the system SHALL show scheduled date, actual send date, and response date
3. WHEN follow-up was skipped THEN the system SHALL display reason and who skipped it
4. WHEN follow-up was rescheduled THEN the system SHALL show original and new dates
5. WHEN viewing campaign follow-ups THEN the system SHALL show aggregate statistics (total sent, response rate, average response time)
6. WHEN exporting history THEN the system SHALL provide CSV with all follow-up events
7. WHEN auditing follow-ups THEN the system SHALL show which follow-ups were automated vs manual

### Requirement 9: Multi-Channel Follow-up Strategy

**User Story:** As an Account Executive, I want to use different channels for follow-ups, so that I can reach KOLs through their preferred or most responsive channel.

#### Acceptance Criteria

1. WHEN 1st follow-up is sent THEN the system SHALL use same channel as original message
2. WHEN 2nd follow-up is sent THEN the system SHALL optionally try secondary channel if no response
3. WHEN 3rd follow-up is sent THEN the system SHALL allow trying all available channels
4. WHEN configuring follow-up strategy THEN the system SHALL allow setting channel sequence (e.g., Email → Line → Discord)
5. WHEN a channel consistently fails THEN the system SHALL skip it in future follow-ups
6. WHEN KOL responds on different channel THEN the system SHALL update preferred channel
7. WHEN using multiple channels THEN the system SHALL avoid duplicate messages within 24 hours

### Requirement 10: Smart Follow-up Timing

**User Story:** As a system, I want to send follow-ups at optimal times based on KOL behavior, so that messages are more likely to be seen and answered.

#### Acceptance Criteria

1. WHEN the system has historical data THEN the system SHALL identify when KOL typically responds (time of day, day of week)
2. WHEN scheduling follow-up THEN the system SHALL suggest optimal send time based on KOL patterns
3. WHEN KOL is in different timezone THEN the system SHALL adjust send time to their local business hours
4. WHEN sending on weekend THEN the system SHALL warn and suggest rescheduling to weekday
5. WHEN sending late at night THEN the system SHALL queue for next morning (8-10 AM local time)
6. WHEN KOL has "Do Not Disturb" hours set THEN the system SHALL respect those hours
7. WHEN optimal time conflicts with urgency THEN the system SHALL prioritize urgency but log the decision
