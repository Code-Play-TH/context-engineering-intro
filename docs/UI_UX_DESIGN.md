# UI/UX Design Specifications
# KOL Influencer Management System

**Version:** 1.0
**Last Updated:** 2025-10-01
**Design System:** Shadcn/ui + Tailwind CSS

---

## 🎨 Design System

### Color Palette

```css
/* Primary Colors */
--primary: 222.2 47.4% 11.2%        /* Main brand color (dark) */
--primary-foreground: 210 40% 98%   /* Text on primary */

/* Secondary Colors */
--secondary: 210 40% 96.1%          /* Light gray for secondary actions */
--secondary-foreground: 222.2 47.4% 11.2%

/* Accent Colors */
--accent: 210 40% 96.1%
--accent-foreground: 222.2 47.4% 11.2%

/* Destructive (Errors, Warnings) */
--destructive: 0 84.2% 60.2%        /* Red for errors */
--destructive-foreground: 210 40% 98%

/* Status Colors */
--success: 142 76% 36%              /* Green */
--warning: 38 92% 50%               /* Orange */
--info: 221 83% 53%                 /* Blue */

/* Background */
--background: 0 0% 100%             /* White */
--foreground: 222.2 84% 4.9%        /* Dark text */

/* Card */
--card: 0 0% 100%
--card-foreground: 222.2 84% 4.9%

/* Muted */
--muted: 210 40% 96.1%
--muted-foreground: 215.4 16.3% 46.9%

/* Border */
--border: 214.3 31.8% 91.4%
--input: 214.3 31.8% 91.4%
--ring: 222.2 84% 4.9%
```

### Typography

```css
/* Font Family */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Font Sizes */
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
--text-4xl: 2.25rem   /* 36px */

/* Font Weights */
--font-normal: 400
--font-medium: 500
--font-semibold: 600
--font-bold: 700
```

### Spacing Scale

```css
/* Based on 4px base unit */
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-5: 1.25rem   /* 20px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
--space-10: 2.5rem   /* 40px */
--space-12: 3rem     /* 48px */
--space-16: 4rem     /* 64px */
```

### Border Radius

```css
--radius-sm: 0.25rem   /* 4px */
--radius-md: 0.375rem  /* 6px */
--radius-lg: 0.5rem    /* 8px */
--radius-xl: 0.75rem   /* 12px */
--radius-2xl: 1rem     /* 16px */
--radius-full: 9999px  /* Pill shape */
```

---

## 📱 Page Designs

### 1. Dashboard (Home)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🏠 Dashboard                                    👤 User ▼  🔔      │
├─────────────────────────────────────────────────────────────────────┤
│ 📊 KOL Mgmt  📋 Campaigns  📈 Analytics  💬 Messages  ⚙️ Settings │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 Overview                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ 👥 Total   │ │ 📋 Active  │ │ 📈 Avg     │ │ 💰 Total   │     │
│  │   KOLs     │ │  Campaigns │ │  Engage    │ │   Spend    │     │
│  │            │ │            │ │            │ │            │     │
│  │   1,234    │ │     45     │ │   4.2%     │ │  $250K     │     │
│  │   +12%     │ │    +5      │ │   +0.3%    │ │   +15%     │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                     │
│  📈 Performance Trends                    🔥 Top Performing KOLs   │
│  ┌──────────────────────────────┐        ┌───────────────────────┐│
│  │                          ╱   │        │ 1. @influencer1       ││
│  │                      ╱╱      │        │    Platform: IG       ││
│  │                  ╱╱          │        │    Followers: 500K    ││
│  │              ╱╱              │        │    ER: 5.2%          ││
│  │          ╱╱                  │        ├───────────────────────┤│
│  │      ╱╱                      │        │ 2. @influencer2       ││
│  │  ╱╱                          │        │    Platform: TikTok   ││
│  │──────────────────────────────│        │    Followers: 1M      ││
│  │ Jan  Feb  Mar  Apr  May  Jun │        │    ER: 6.8%          ││
│  └──────────────────────────────┘        └───────────────────────┘│
│                                                                     │
│  📋 Recent Activity                       ⚠️ Alerts                │
│  ┌──────────────────────────────┐        ┌───────────────────────┐│
│  │ • Campaign "Summer Sale"     │        │ ⚠️ Low engagement     ││
│  │   started 2 hours ago        │        │    Campaign #123      ││
│  │                              │        │                       ││
│  │ • New KOL added: @newkol    │        │ ℹ️ Brief approval     ││
│  │   by John Doe               │        │    pending (3)        ││
│  │                              │        │                       ││
│  │ • Content posted by         │        │ ✅ Payment processed  ││
│  │   @influencer3              │        │    Invoice #456       ││
│  └──────────────────────────────┘        └───────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `DashboardHeader` - Top navigation with user menu
- `StatCard` - Metric cards with trend indicators
- `PerformanceChart` - Line/area chart (D3.js)
- `TopKOLsList` - Ranked list with avatars
- `ActivityFeed` - Timeline of recent events
- `AlertPanel` - Priority notifications

---

### 2. KOL Management - Table View

```
┌─────────────────────────────────────────────────────────────────────┐
│ 👥 KOL Management                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔍 [Search KOLs by name, platform, niche...]        [+ Add KOL]   │
│                                                                     │
│  🎯 Filters:                                                        │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ [Clear All]    │
│  │Platform▼│ │ Niche ▼ │ │Followers▼│ │   ER   ▼ │               │
│  └─────────┘ └─────────┘ └──────────┘ └──────────┘               │
│                                                                     │
│  📊 Showing 1-20 of 1,234 KOLs                 [⚙️ Columns] [📥 Export]│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │☐│Avatar│Name          │Platform│Followers│ER   │Niche  │Actions││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │☐│ 🖼️  │John Smith    │Instagram│  500K  │5.2% │Fashion│ ⋮    ││
│  │☐│ 🖼️  │Sarah Lee     │TikTok   │  1.2M  │6.8% │Beauty │ ⋮    ││
│  │☐│ 🖼️  │Mike Chen     │YouTube  │  800K  │4.5% │Tech   │ ⋮    ││
│  │☐│ 🖼️  │Lisa Park     │Instagram│  350K  │7.1% │Food   │ ⋮    ││
│  │☐│ 🖼️  │David Kim     │Twitter  │  200K  │3.8% │News   │ ⋮    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  [◄ Previous]  [1] [2] [3] ... [62]  [Next ►]    Show: [20 ▼] per page│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Advanced Filters Panel (Expandable):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🎯 Advanced Filters                                     [Apply] [×] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Platform                          Verification Status              │
│  ☐ Instagram  ☐ Facebook          ⚪ All  ⚪ Verified  ⚪ Unverified│
│  ☐ YouTube    ☐ TikTok                                             │
│  ☐ Twitter                        Engagement Rate                  │
│                                    Min: [    ] %   Max: [    ] %    │
│  Follower Count Range                                               │
│  ──●────────────────────●──        Location                         │
│  1K              10M               [Select location(s)...]          │
│                                                                     │
│  Niche/Category                    Available for Campaign           │
│  [Multi-select dropdown...]        ⚪ Yes  ⚪ No  ⚪ All             │
│                                                                     │
│  Last Activity                     Content Type                     │
│  ⚪ Last 7 days                    ☐ Photos  ☐ Videos              │
│  ⚪ Last 30 days                   ☐ Stories ☐ Reels               │
│  ⚪ Last 90 days                   ☐ Live                           │
│  ⚪ Custom range                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `KOLTable` - Data table with TanStack Table
- `FilterBar` - Quick filter buttons
- `AdvancedFilters` - Collapsible filter panel (Shadcn Dialog)
- `BulkActions` - Multi-select actions dropdown
- `Pagination` - Page navigation controls

---

### 3. KOL Detail Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← Back to KOLs                                    [Edit] [Delete]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  🖼️                  John Smith                                ││
│  │  [Profile]         @johnsmith                                   ││
│  │   Photo            ✅ Verified                                  ││
│  │                    📍 Bangkok, Thailand                         ││
│  │                    📧 john@email.com                            ││
│  │                    📱 +66-XXX-XXX-XXXX                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  📊 Overview  │  📱 Social Accounts  │  📈 Performance  │  📋 Campaigns │  💬 Messages │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  📱 Connected Social Media Accounts                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Instagram                                    [↻ Refresh Stats]  ││
│  │ @johnsmith_official                                             ││
│  │                                                                 ││
│  │ 👥 500,000 followers      📊 4,234 posts     ❤️ 5.2% ER        ││
│  │ 📈 Following: 890         📅 Last post: 2h ago                 ││
│  │                                                                 ││
│  │ [View Full Stats] [Disconnect]                                  ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ TikTok                                       [↻ Refresh Stats]  ││
│  │ @johnsmith                                                      ││
│  │                                                                 ││
│  │ 👥 1,200,000 followers    🎬 892 videos      ❤️ 6.8% ER        ││
│  │ 👍 15.5M total likes      📅 Last post: 5h ago                 ││
│  │                                                                 ││
│  │ [View Full Stats] [Disconnect]                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  [+ Connect New Account]                                            │
│                                                                     │
│  📈 Performance Analytics (Last 30 Days)                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                 ││
│  │  Engagement Rate Trend                                          ││
│  │  8% ┤                                                   ╱╲      ││
│  │  6% ┤                               ╱╲            ╱╲  ╱  ╲     ││
│  │  4% ┤                   ╱╲      ╱╲╱  ╲    ╱╲  ╱╲╱    ╲╱       ││
│  │  2% ┤       ╱╲      ╱╲╱  ╲  ╱╲╱      ╲╱╲╱  ╲╱                 ││
│  │  0% └────────────────────────────────────────────────────────  ││
│  │      Week1  Week2  Week3  Week4                                ││
│  │                                                                 ││
│  │  Top Performing Posts                                           ││
│  │  🖼️ Post 1 - 25K likes, 500 comments                          ││
│  │  🖼️ Post 2 - 22K likes, 450 comments                          ││
│  │  🖼️ Post 3 - 20K likes, 380 comments                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  📋 Campaign History                                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Campaign Name        │ Date        │ Status    │ Performance   ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ Summer Sale 2025     │ Mar - Apr   │ ✅ Done   │ ⭐⭐⭐⭐⭐    ││
│  │ Brand Launch         │ Jan - Feb   │ ✅ Done   │ ⭐⭐⭐⭐      ││
│  │ Holiday Special      │ Dec 2024    │ ✅ Done   │ ⭐⭐⭐⭐⭐    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `ProfileHeader` - KOL profile info with avatar
- `TabNavigation` - Shadcn Tabs component
- `SocialAccountCard` - Connected platform cards
- `PerformanceChart` - Engagement trend chart
- `TopPostsCarousel` - Image carousel with metrics
- `CampaignHistoryTable` - Past campaigns table

---

### 4. Campaign Management

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📋 Campaign Management                         [+ Create Campaign]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔍 [Search campaigns...]                                           │
│                                                                     │
│  Status:  [All ▼]  [Active]  [Draft]  [Completed]  [Archived]      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Campaign Name           │ Status   │ Start Date │ KOLs │ Budget ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ 🔴 Summer Sale 2025    │ Active   │ 2025-06-01 │  12  │ $50K  ││
│  │    Progress: ████████░░ 80%                                     ││
│  │    KPIs: 👁️ 2.5M views • ❤️ 125K engagements • 📈 5.2% ER     ││
│  │    [View Details] [Edit] [Pause]                               ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ 🟡 Product Launch       │ Draft    │ 2025-07-15 │   8  │ $35K  ││
│  │    Progress: ███░░░░░░░ 30%                                     ││
│  │    [View Details] [Edit] [Start]                               ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ ✅ Holiday Special 2024 │ Complete │ 2024-12-01 │  15  │ $75K  ││
│  │    ROI: +245% • Target: ✅ Exceeded                            ││
│  │    [View Report]                                                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Campaign Detail/Edit View:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← Back                  Summer Sale 2025                    [Save]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📋 Basic Info  │  👥 KOLs  │  📝 Brief  │  📊 Performance  │  💰 Budget  │
│  ──────────────────────────────────────────────────────────────     │
│                                                                     │
│  Campaign Details                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Campaign Name*                                                  ││
│  │ [Summer Sale 2025                                             ] ││
│  │                                                                 ││
│  │ Description                                                     ││
│  │ [Promote summer collection with 30% discount...              ] ││
│  │                                                                 ││
│  │ Duration*                                                       ││
│  │ Start: [2025-06-01 ▼]   End: [2025-06-30 ▼]                   ││
│  │                                                                 ││
│  │ Budget*                   Currency                              ││
│  │ [$] [50,000         ]    [USD ▼]                               ││
│  │                                                                 ││
│  │ Target KPIs                                                     ││
│  │ Total Views:     [2,000,000]   Engagement Rate:  [5.0%]       ││
│  │ Engagements:     [100,000  ]   Conversions:      [1,000]      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  👥 Assigned KOLs (12)                          [+ Add KOLs]        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 🖼️ John Smith    Instagram   500K   $3,000  ✅ Accepted        ││
│  │ 🖼️ Sarah Lee     TikTok      1.2M   $5,000  ⏳ Pending         ││
│  │ 🖼️ Mike Chen     YouTube     800K   $4,500  ✅ Accepted        ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  📅 Timeline & Milestones                                           │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ●───────●───────●───────●───────●                              ││
│  │ Start  Brief  Post   D+3    D+7   End                          ││
│  │ 06/01  06/05  06/10  06/13  06/17 06/30                        ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `CampaignCard` - Campaign card with progress bar
- `CampaignForm` - Multi-step form (Shadcn Form)
- `KOLSelector` - Multi-select with search
- `Timeline` - Visual timeline component
- `BudgetTracker` - Budget allocation display
- `KPIGauge` - Progress toward goals

---

### 5. Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📈 Analytics Dashboard                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Date Range: [Last 30 Days ▼]  Campaign: [All ▼]  Platform: [All ▼]│
│                                                                     │
│  📊 Key Metrics                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ 👁️ Total   │ │ ❤️ Engage  │ │ 📊 Avg ER  │ │ 💰 ROI     │     │
│  │  Reach     │ │   ments    │ │            │ │            │     │
│  │            │ │            │ │            │ │            │     │
│  │ 5.2M       │ │  258K      │ │   5.8%     │ │  +245%     │     │
│  │ ▲ +15%     │ │  ▲ +22%    │ │  ▲ +0.5%   │ │  ▲ +12%    │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                     │
│  📈 Performance Over Time                                           │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 6M ┤                                                    ╱       ││
│  │ 5M ┤                                          ╱╲    ╱╲╱        ││
│  │ 4M ┤                                  ╱╲  ╱╲╱  ╲╱╲╱           ││
│  │ 3M ┤                          ╱╲  ╱╲╱  ╲╱                      ││
│  │ 2M ┤                  ╱╲  ╱╲╱  ╲╱                             ││
│  │ 1M ┤          ╱╲  ╱╲╱  ╲╱                                      ││
│  │  0 └─────────────────────────────────────────────────────────  ││
│  │     Jan   Feb   Mar   Apr   May   Jun                         ││
│  │                                                                 ││
│  │ Metrics: ─ Reach  ─ Engagements  ─ Clicks                     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  📊 Platform Breakdown        🎯 Top Performing Campaigns           │
│  ┌──────────────────────┐    ┌─────────────────────────────────┐  │
│  │     📊                │    │ 1. Summer Sale 2025             │  │
│  │   ████  Instagram 45% │    │    ROI: +245%  •  ER: 5.8%     │  │
│  │   ███   TikTok    30% │    │                                 │  │
│  │   ██    YouTube   15% │    │ 2. Product Launch               │  │
│  │   █     Facebook  10% │    │    ROI: +180%  •  ER: 4.2%     │  │
│  └──────────────────────┘    └─────────────────────────────────┘  │
│                                                                     │
│  🏆 Top Performing KOLs       💹 Cost Metrics                      │
│  ┌──────────────────────┐    ┌─────────────────────────────────┐  │
│  │ 1. @johnsmith        │    │ CPM:  $2.50    CPC:  $0.45      │  │
│  │    ER: 6.8% • 500K   │    │ CPE:  $0.15    CPV:  $0.008     │  │
│  │                      │    │                                 │  │
│  │ 2. @sarahlee         │    │ Avg Cost/KOL:  $3,500           │  │
│  │    ER: 5.2% • 1.2M   │    │ Total Spend:   $125,000         │  │
│  └──────────────────────┘    └─────────────────────────────────┘  │
│                                                                     │
│  [📥 Export Report]  [📧 Schedule Report]  [🎨 Customize View]     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `DateRangePicker` - Shadcn Date Picker
- `MetricCard` - KPI card with trend
- `MultiSeriesChart` - D3.js line chart
- `PieChart` - Platform breakdown (Nivo)
- `RankingList` - Top performers list
- `CostMetricsGrid` - Cost breakdown

---

### 6. Brief & Communication

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📝 Briefs & Communication                       [+ Create Brief]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Campaign: [Summer Sale 2025 ▼]   Status: [All ▼]                  │
│                                                                     │
│  📋 Briefs                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Brief: Instagram Post - Fashion Collection                      ││
│  │ KOL: @johnsmith                              ⏳ Pending Approval ││
│  │                                                                 ││
│  │ 📄 Content Requirements:                                        ││
│  │ - 1 Feed post + 3 Stories                                       ││
│  │ - Showcase summer collection items                              ││
│  │ - Include discount code: SUMMER30                               ││
│  │ - Tag @brandname                                                ││
│  │                                                                 ││
│  │ 📅 Deadline: June 10, 2025                                      ││
│  │ 💰 Compensation: $3,000                                         ││
│  │                                                                 ││
│  │ 📎 Attachments: product_images.zip, brand_guidelines.pdf        ││
│  │                                                                 ││
│  │ [Approve] [Request Changes] [Send Message]                      ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ Brief: TikTok Video - Unboxing                                  ││
│  │ KOL: @sarahlee                               ✅ Approved         ││
│  │ [View Details]                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  💬 Messages                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Conversation with @johnsmith                                    ││
│  │                                                                 ││
│  │ [You, 2h ago]                                                   ││
│  │ Hi John! Here's the brief for the Summer Sale campaign.        ││
│  │ Let me know if you have any questions.                          ││
│  │                                                                 ││
│  │ [@johnsmith, 1h ago]                                            ││
│  │ Thanks! Can I use Reels instead of regular posts?               ││
│  │                                                                 ││
│  │ [Type your message...]                              [Send]      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Create Brief Modal:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ Create Brief                                      [Save Draft] [×]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Campaign*                                                          │
│  [Summer Sale 2025                                              ▼] │
│                                                                     │
│  KOL*                                                               │
│  [Select KOL...                                                  ▼] │
│                                                                     │
│  Brief Title*                                                       │
│  [Instagram Post - Fashion Collection                            ] │
│                                                                     │
│  Content Type*                                                      │
│  ☑️ Feed Post (1)   ☑️ Stories (3)   ☐ Reels   ☐ IGTV            │
│                                                                     │
│  Requirements                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ [Rich text editor]                                              ││
│  │                                                                 ││
│  │ • Showcase summer collection items                             ││
│  │ • Include discount code: SUMMER30                               ││
│  │ • Tag @brandname in post                                        ││
│  │ • Use hashtags: #SummerSale #Fashion                            ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Deadline*                  Compensation*                           │
│  [2025-06-10 ▼]           [$] [3,000      ]                        │
│                                                                     │
│  📎 Attachments                                                     │
│  [Drag files here or click to upload]                              │
│  📄 product_images.zip (2.5 MB) [×]                                 │
│  📄 brand_guidelines.pdf (1.2 MB) [×]                               │
│                                                                     │
│                                       [Cancel] [Send Brief]         │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `BriefCard` - Brief display card
- `BriefForm` - Create/edit brief form
- `MessageThread` - Chat interface
- `FileUpload` - Drag-drop file upload (Shadcn)
- `RichTextEditor` - Tiptap or similar
- `ApprovalWorkflow` - Approval status tracker

---

### 7. Content Monitoring

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔍 Content Monitoring                                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Campaign: [Summer Sale 2025 ▼]   Platform: [All ▼]   Status: [All ▼]│
│                                                                     │
│  📊 Content Overview                                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ 📝 Posted  │ │ ⏳ Pending │ │ ✅ Verified│ │ ⚠️ Flagged │     │
│  │            │ │            │ │            │ │            │     │
│  │     45     │ │      8     │ │     42     │ │      3     │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                     │
│  🎬 Content Feed                                   [Grid ⊞] [List ☰]│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ┌─────────┐                                                     ││
│  │ │  📷     │  @johnsmith • Instagram • 2h ago                    ││
│  │ │  Post   │                                                     ││
│  │ │ Image   │  "Check out this amazing summer collection! 🌞      ││
│  │ │         │   Use code SUMMER30 for 30% off! @brandname"        ││
│  │ └─────────┘                                                     ││
│  │                                                                 ││
│  │  👁️ 45.2K views • ❤️ 3.2K likes • 💬 145 comments • 🔄 89 shares││
│  │  📊 ER: 7.2% • ✅ Brand mention detected • ✅ Hashtags correct  ││
│  │  🤖 AI Sentiment: Positive (95%)                                ││
│  │                                                                 ││
│  │  [View Full Post] [Verify] [Flag] [Analytics]                  ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ ┌─────────┐                                                     ││
│  │ │  🎬     │  @sarahlee • TikTok • 5h ago                        ││
│  │ │  Video  │                                                     ││
│  │ │         │  "Unboxing time! 📦 Summer vibes! #SummerSale"      ││
│  │ └─────────┘                                                     ││
│  │                                                                 ││
│  │  👁️ 125K views • ❤️ 8.5K likes • 💬 320 comments               ││
│  │  📊 ER: 6.8% • ⚠️ Missing brand tag                            ││
│  │  🤖 AI Sentiment: Positive (92%)                                ││
│  │                                                                 ││
│  │  [View Full Post] [Request Fix] [Analytics]                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  📈 Performance Tracking (D+1, D+3, D+7)                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Post: @johnsmith - Instagram                                    ││
│  │                                                                 ││
│  │ Checkpoint │ Views   │ Likes  │ Comments │ ER    │ vs Target   ││
│  │ D+1        │  10.5K  │  850   │   32     │ 8.4%  │ ✅ +12%     ││
│  │ D+3        │  28.2K  │  2.1K  │   98     │ 7.8%  │ ✅ +8%      ││
│  │ D+7        │  45.2K  │  3.2K  │  145     │ 7.2%  │ ✅ +5%      ││
│  │ Final      │  -      │   -    │   -      │  -    │  -          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- `ContentCard` - Post display with metrics
- `ContentGrid` - Grid/List toggle view
- `AIAnalysisBadge` - AI-detected insights
- `CheckpointTracker` - D+1/3/7 tracking table
- `ContentVerification` - Verify/flag controls
- `SentimentIndicator` - Sentiment score display

---

### 8. Mobile Responsive Design

**Mobile Navigation (Bottom Tab Bar):**

```
┌─────────────────┐
│                 │
│  Content Area   │
│                 │
│                 │
│                 │
├─────────────────┤
│ 🏠  👥  📋  📊 │
│Home KOL Camp Ana│
└─────────────────┘
```

**Mobile Card Design:**

```
┌─────────────────┐
│ 🖼️ John Smith  │
│ @johnsmith      │
│ ✅ Instagram    │
│                 │
│ 👥 500K         │
│ 📊 5.2% ER      │
│                 │
│ [View] [Edit]   │
└─────────────────┘
```

---

## 🎨 Component Library (Shadcn/ui)

### Primary Components

1. **Button**
   - Variants: default, destructive, outline, secondary, ghost, link
   - Sizes: sm, default, lg, icon

2. **Card**
   - Header, Title, Description, Content, Footer

3. **Dialog/Modal**
   - Full-screen on mobile
   - Overlay with backdrop blur

4. **Table**
   - With TanStack Table
   - Sortable columns
   - Row selection
   - Pagination

5. **Form**
   - Input, Textarea, Select, Checkbox, Radio
   - Built-in validation
   - Error messages

6. **Dropdown Menu**
   - With keyboard navigation
   - Sub-menus support

7. **Tabs**
   - Horizontal & vertical
   - With icons

8. **Badge**
   - Status indicators
   - Variants: default, secondary, destructive, outline

9. **Avatar**
   - With fallback
   - Group avatars

10. **Progress**
    - Linear progress bar
    - Circular progress

---

## 🔄 User Flows

### Flow 1: Create Campaign

```
Login → Dashboard → Campaigns → [+ Create Campaign]
  ↓
Campaign Form (Basic Info)
  ↓
Select KOLs (Search & Filter)
  ↓
Create Briefs for each KOL
  ↓
Set Budget & KPIs
  ↓
Review & Submit
  ↓
Send Briefs to KOLs
```

### Flow 2: Monitor Content

```
Login → Dashboard → Content Monitoring
  ↓
View Posted Content
  ↓
Check AI Analysis
  ↓
Verify Content
  ↓
Track Performance (D+1, D+3, D+7)
  ↓
View Analytics
```

### Flow 3: Search & Hire KOL

```
Login → KOL Management
  ↓
Apply Filters (Platform, Followers, ER)
  ↓
Search by Keywords
  ↓
View KOL Profile
  ↓
Check Performance History
  ↓
Add to Campaign
  ↓
Create Brief
```

---

## 📐 Layout Specifications

### Grid System
- 12-column grid
- Gutter: 24px (desktop), 16px (mobile)
- Max content width: 1280px

### Breakpoints
```css
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */
```

### Spacing
- Section padding: 80px (desktop), 40px (mobile)
- Card padding: 24px (desktop), 16px (mobile)
- Element spacing: 16px default

---

## ♿ Accessibility

### WCAG 2.1 AA Compliance

1. **Color Contrast**
   - Text: Minimum 4.5:1
   - Large text: Minimum 3:1
   - Interactive elements: Minimum 3:1

2. **Keyboard Navigation**
   - All interactive elements focusable
   - Visible focus indicators
   - Logical tab order

3. **Screen Readers**
   - Semantic HTML
   - ARIA labels where needed
   - Alt text for images

4. **Forms**
   - Labels for all inputs
   - Error messages announced
   - Required fields indicated

---

## 🎭 Animations & Transitions

### Micro-interactions
```css
/* Button hover */
transition: all 0.2s ease;

/* Card hover */
transition: transform 0.2s ease, box-shadow 0.2s ease;

/* Page transitions */
transition: opacity 0.3s ease, transform 0.3s ease;

/* Loading states */
animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```

### Motion Principles
- Duration: 150-300ms for micro-interactions
- Easing: ease-in-out for natural feel
- Reduce motion: Respect prefers-reduced-motion

---

**Next Steps:**
1. Create high-fidelity mockups in Figma
2. Build component library with Shadcn/ui
3. Implement responsive layouts
4. Add animations with Framer Motion
5. Test accessibility compliance

Would you like me to:
- Create Figma design files?
- Build specific components?
- Add more detailed specifications?
