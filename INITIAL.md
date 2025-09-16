## FEATURE:

KOL Influencer Management System - A comprehensive platform for managing Key Opinion Leader (KOL) campaigns from initial contact through final reporting. The system handles KOL database management, performance tracking, brief creation and distribution, communication scheduling, calendar management, content monitoring, and campaign reporting.

## EXAMPLES:

The system workflow includes the following key processes:

1. **KOL Database Search & Management**

    - Query existing KOL database for suitable influencers
    - Filter by demographics, niche, engagement rates, and past performance

2. **Performance Tracking & Social Media Scraping**

    - One-click performance check button for each KOL
    - Automated data scraping from multiple platforms (Facebook, Instagram, TikTok, YouTube, X/Twitter)
    - Real-time follower count, engagement rate, and content analysis

3. **Brief Creation System**

    - Custom brief generation interface for each KOL
    - Template-based brief creation with campaign-specific details
    - Brief versioning and approval workflow

4. **Multi-Channel Communication**

    - Automated brief distribution via Email, Line, Discord, Inbox, and DM
    - Communication preference tracking per KOL
    - Message template management

5. **Follow-up Automation**

    - Scheduled follow-up reminders at 1, 3, and 5-day intervals
    - Automated reminder notifications and manual override options
    - Communication history tracking

6. **Calendar Management**

    - Project timeline visualization
    - KOL availability scheduling
    - Deadline tracking and milestone management

7. **Content Monitoring & Analytics**

    - Post detection and verification system
    - Automated stat collection at 24hr, 3-day, 5-day, and 7-day intervals
    - KPI comparison and achievement tracking
    - Alert system for underperforming content

8. **Final Reporting**
    - Automated report generation at project completion
    - Comprehensive campaign analytics and ROI calculation
    - Performance comparison against initial KPIs

## DOCUMENTATION:

**Core System Requirements:**

-   Database integration for KOL management (user profiles, contact information, performance history)
-   Web scraping capabilities for social media platforms (Facebook, Instagram, TikTok, YouTube, X/Twitter)
-   Multi-channel communication APIs (Email SMTP, Line Messaging API, Discord API, Social Media APIs)
-   Calendar and scheduling system integration
-   Automated notification and alert system
-   Report generation and data visualization tools

**External API Documentation:**

-   Facebook Graph API - for Facebook data scraping and insights
-   Instagram Basic Display API - for Instagram content and metrics
-   TikTok API for Business - for TikTok analytics and content data
-   YouTube Data API v3 - for YouTube channel and video statistics
-   Twitter API v2 - for X/Twitter content and engagement metrics
-   Line Messaging API - for Line communication
-   Discord API - for Discord messaging functionality
-   Email service providers (SendGrid, AWS SES, or similar)

**Technical Considerations:**

-   Rate limiting compliance for all social media APIs
-   Data privacy and GDPR compliance requirements
-   Real-time data synchronization and caching strategies
-   Scalable database design for handling large KOL datasets
-   User authentication and role-based access control
-   Mobile-responsive design for campaign management on-the-go

## OTHER CONSIDERATIONS:

**Critical Implementation Notes:**

1. **API Rate Limiting & Compliance**

    - Social media platforms have strict rate limits and ToS requirements
    - Implement proper delay mechanisms and respect platform guidelines
    - Consider using official business APIs where available to avoid account suspension

2. **Data Accuracy & Real-time Updates**

    - Social media metrics can change rapidly; implement appropriate caching strategies
    - Consider data freshness vs. API call costs when designing update frequencies
    - Handle API failures gracefully with fallback mechanisms

3. **Multi-Platform Complexity**

    - Each social media platform has different data structures and limitations
    - Authentication tokens may expire and require refresh mechanisms
    - Platform-specific content format requirements for posting

4. **Communication Channel Management**

    - Different KOLs prefer different communication methods
    - Track message delivery status and read receipts where possible
    - Handle bounced emails and invalid contact information

5. **Time Zone Considerations**

    - KOLs may be in different time zones for follow-up scheduling
    - Campaign deadlines should account for local time zones
    - Statistics collection timing should be consistent across regions

6. **Scalability & Performance**

    - System should handle hundreds of KOLs simultaneously
    - Background job processing for data scraping and report generation
    - Database indexing for efficient KOL search and filtering

7. **Security & Privacy**

    - Secure storage of KOL contact information and campaign data
    - Audit trails for all communications and system actions
    - Compliance with data protection regulations

8. **Common AI Assistant Pitfalls to Avoid**
    - Don't assume all social media APIs work the same way
    - Each platform requires different authentication methods and data parsing
    - Campaign timeline calculations must account for weekends and holidays
    - KPI thresholds should be configurable, not hardcoded
    - Always implement proper error handling for external API calls
