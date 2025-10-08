# Requirements Document - Performance Tracking & Social Media Scraping

## Introduction

This document outlines the requirements for the Performance Tracking system, which automatically scrapes and monitors KOL social media metrics across multiple platforms (Facebook, Instagram, TikTok, YouTube, Twitter/X) with configurable scheduling and historical data tracking.

## Requirements

### Requirement 1: Manual Performance Refresh

**User Story:** As an Account Executive, I want to manually refresh KOL performance metrics, so that I can get immediate updates when needed.

#### Acceptance Criteria

1. WHEN a user clicks refresh button on KOL profile THEN the system SHALL fetch latest metrics from all connected social platforms
2. WHEN manual refresh is triggered THEN the system SHALL display loading indicator with estimated time
3. WHEN refresh completes THEN the system SHALL display updated metrics with timestamp
4. WHEN refresh fails for a platform THEN the system SHALL display error for that platform but show data from successful platforms
5. WHEN multiple users trigger refresh for same KOL within 5 minutes THEN the system SHALL return cached results to avoid API rate limits
6. WHEN refresh is in progress THEN the system SHALL disable refresh button to prevent duplicate requests
7. WHEN refresh completes THEN the system SHALL store metrics in history for trend analysis

### Requirement 2: Scheduled Automatic Scraping

**User Story:** As a Campaign Manager, I want to schedule automatic daily scraping of KOL metrics, so that I have up-to-date data without manual effort.

#### Acceptance Criteria

1. WHEN a user configures scraping schedule THEN the system SHALL allow setting time of day (e.g., "Daily at 2:00 AM")
2. WHEN scheduled scraping runs THEN the system SHALL process all active KOLs (in active campaigns) first, then inactive KOLs
3. WHEN scraping 100K+ KOLs THEN the system SHALL distribute requests across 24 hours to respect API rate limits (~70 KOLs per minute)
4. WHEN scheduled scraping completes THEN the system SHALL generate summary report with success/failure counts
5. WHEN scraping fails for a KOL THEN the system SHALL retry up to 3 times with exponential backoff
6. WHEN a KOL fails repeatedly (5 consecutive days) THEN the system SHALL flag for manual review and notify Account Executive
7. WHEN scraping is scheduled THEN the system SHALL allow pausing/resuming without losing schedule configuration

### Requirement 3: Custom Interval Scheduling

**User Story:** As a Campaign Manager, I want to set custom scraping intervals for specific KOLs or campaigns, so that I can monitor high-priority influencers more frequently.

#### Acceptance Criteria

1. WHEN a user sets custom interval THEN the system SHALL allow selecting hourly, every 6 hours, daily, weekly, or custom
2. WHEN a KOL is in active campaign THEN the system SHALL allow setting campaign-specific scraping frequency
3. WHEN campaign ends THEN the system SHALL revert to default scraping frequency for that KOL
4. WHEN hourly scraping is selected THEN the system SHALL warn about API rate limit implications
5. WHEN custom interval is set THEN the system SHALL override default schedule for that KOL
6. WHEN multiple campaigns use same KOL with different intervals THEN the system SHALL use the most frequent interval
7. WHEN user views scraping schedule THEN the system SHALL display next scheduled scrape time for each KOL

### Requirement 4: Multi-Platform Metrics Collection

**User Story:** As an Account Executive, I want to collect metrics from all major social platforms, so that I have comprehensive performance data.

#### Acceptance Criteria

1. WHEN the system scrapes Instagram THEN the system SHALL fetch follower count, following count, post count, engagement rate, and recent posts
2. WHEN the system scrapes TikTok THEN the system SHALL fetch follower count, total likes, video count, average views, and engagement rate
3. WHEN the system scrapes YouTube THEN the system SHALL fetch subscriber count, total views, video count, and average views per video
4. WHEN the system scrapes Twitter/X THEN the system SHALL fetch follower count, tweet count, engagement rate, and recent tweets
5. WHEN the system scrapes Facebook THEN the system SHALL fetch page likes, follower count, post engagement, and reach
6. WHEN a platform API is unavailable THEN the system SHALL log error and continue with other platforms
7. WHEN metrics are collected THEN the system SHALL store raw data and calculated metrics (engagement rate, growth rate)

### Requirement 5: Historical Data Tracking and Trends

**User Story:** As a Campaign Manager, I want to view historical performance trends, so that I can identify growth patterns and anomalies.

#### Acceptance Criteria

1. WHEN a user views KOL performance THEN the system SHALL display line charts for follower growth over last 30, 90, and 365 days
2. WHEN the system calculates growth rate THEN the system SHALL compare current metrics to previous period (day, week, month)
3. WHEN follower count drops significantly (>10% in one day) THEN the system SHALL flag as anomaly and notify Account Executive
4. WHEN follower count increases significantly (>50% in one day) THEN the system SHALL flag for verification (possible bot followers)
5. WHEN engagement rate changes significantly (>20% change) THEN the system SHALL highlight in trend chart
6. WHEN user exports historical data THEN the system SHALL provide CSV with daily metrics for selected date range
7. WHEN the system stores historical data THEN the system SHALL keep daily snapshots for 2 years, then archive to cold storage

### Requirement 6: Content Monitoring and Post Detection

**User Story:** As an Account Executive, I want to automatically detect when KOLs post campaign content, so that I can track deliverables.

#### Acceptance Criteria

1. WHEN a KOL posts content THEN the system SHALL detect new posts within 1 hour of posting
2. WHEN new post is detected THEN the system SHALL check if it matches campaign hashtags, mentions, or keywords
3. WHEN campaign content is detected THEN the system SHALL notify Account Executive and link post to campaign
4. WHEN post is linked to campaign THEN the system SHALL track metrics at 24hr, 3-day, 5-day, and 7-day intervals
5. WHEN post metrics are collected THEN the system SHALL store likes, comments, shares, views, and engagement rate
6. WHEN post underperforms (engagement <50% of KOL average) THEN the system SHALL alert Campaign Manager
7. WHEN all campaign deliverables are posted THEN the system SHALL notify Campaign Manager that content phase is complete

### Requirement 7: KPI Comparison and Achievement Tracking

**User Story:** As a Campaign Manager, I want to compare actual performance against campaign KPIs, so that I can measure success.

#### Acceptance Criteria

1. WHEN a user views campaign performance THEN the system SHALL display KPI targets vs actual results
2. WHEN actual results exceed targets THEN the system SHALL highlight in green with percentage over target
3. WHEN actual results fall short of targets THEN the system SHALL highlight in red with percentage below target
4. WHEN campaign is in progress THEN the system SHALL project final results based on current performance
5. WHEN projection shows KPI miss THEN the system SHALL alert Campaign Manager with recommended actions
6. WHEN campaign ends THEN the system SHALL generate final performance report comparing all KPIs
7. WHEN multiple KOLs are in campaign THEN the system SHALL show individual and aggregate performance

### Requirement 8: API Rate Limit Management

**User Story:** As a system, I want to manage API rate limits intelligently, so that I don't exceed platform limits and get blocked.

#### Acceptance Criteria

1. WHEN the system makes API requests THEN the system SHALL track requests per platform per hour
2. WHEN approaching rate limit (80%) THEN the system SHALL slow down requests and queue remaining
3. WHEN rate limit is exceeded THEN the system SHALL pause requests until limit resets
4. WHEN rate limit resets THEN the system SHALL resume processing queued requests
5. WHEN the system queues requests THEN the system SHALL prioritize manual refresh requests over scheduled scraping
6. WHEN Admin views rate limit dashboard THEN the system SHALL display current usage and limits for each platform
7. WHEN rate limit is consistently hit THEN the system SHALL recommend upgrading API tier or reducing scraping frequency

### Requirement 9: Alert System for Performance Issues

**User Story:** As an Account Executive, I want to receive alerts when KOL performance issues occur, so that I can take corrective action.

#### Acceptance Criteria

1. WHEN engagement rate drops below campaign threshold THEN the system SHALL send alert to Account Executive
2. WHEN KOL misses posting deadline THEN the system SHALL send alert to Account Executive and Campaign Manager
3. WHEN post receives negative comments (>30% negative sentiment) THEN the system SHALL alert for potential crisis
4. WHEN follower count drops significantly THEN the system SHALL alert about potential account issues
5. WHEN user configures alerts THEN the system SHALL allow setting thresholds per KOL or campaign
6. WHEN alert is triggered THEN the system SHALL send via email and in-app notification
7. WHEN alert is acknowledged THEN the system SHALL mark as read and stop repeat notifications
