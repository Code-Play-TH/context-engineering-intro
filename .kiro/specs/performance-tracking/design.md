# Design Document - Performance Tracking & Social Media Scraping

## Overview

The Performance Tracking system automates social media metrics collection across multiple platforms with configurable scheduling, historical tracking, content monitoring, and intelligent rate limit management for 100K+ KOLs.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Dashboard   │◀─────│   Tracking   │◀─────│ (Partitioned)│
└──────────────┘      │   Service    │      └─────────────┘
                      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Celery    │
                     │   Workers    │
                     │  (10-20)     │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Social      │
                     │  Media APIs  │
                     │  (5 platforms)│
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class PerformanceTrackingService:
    async def manual_refresh(kol_id: int) -> KOLMetrics
    async def get_latest_metrics(kol_id: int) -> Dict[str, KOLMetrics]
    async def get_historical_metrics(kol_id: int, days: int) -> List[KOLMetrics]
    async def get_growth_rate(kol_id: int, period: str) -> GrowthRate

class ScrapingScheduler:
    async def schedule_scraping(kol_id: int, interval: str) -> None
    async def get_scraping_schedule(kol_id: int) -> ScrapingSchedule
    async def pause_scraping(kol_id: int) -> None
    async def resume_scraping(kol_id: int) -> None

class ContentMonitoringService:
    async def detect_new_posts(kol_id: int) -> List[Post]
    async def link_post_to_campaign(post_id: int, campaign_id: int) -> None
    async def collect_post_metrics(post_id: int) -> PostMetrics
    async def check_post_performance(post_id: int) -> PerformanceAlert

class RateLimitManager:
    async def check_rate_limit(platform: str) -> RateLimitStatus
    async def queue_request(platform: str, request: ScrapingRequest) -> None
    async def process_queue() -> None
    async def get_rate_limit_stats() -> Dict[str, RateLimitStats]

class PlatformScrapers:
    async def scrape_instagram(handle: str) -> InstagramMetrics
    async def scrape_tiktok(handle: str) -> TikTokMetrics
    async def scrape_youtube(handle: str) -> YouTubeMetrics
    async def scrape_twitter(handle: str) -> TwitterMetrics
    async def scrape_facebook(handle: str) -> FacebookMetrics
```

## Data Models

### ScrapingSchedule Model

```python
class ScrapingSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    interval: str  # hourly, daily, weekly, custom
    custom_cron: Optional[str]  # For custom intervals
    priority: int = Field(default=5)  # 1-10, higher = more important
    is_active: bool = Field(default=True)
    last_scraped_at: Optional[datetime]
    next_scrape_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Post Model

```python
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    campaign_id: Optional[int] = Field(foreign_key="campaign.id")
    platform: str
    post_id: str  # Platform-specific post ID
    post_url: str
    post_type: str  # post, story, video, reel
    caption: Optional[str]
    posted_at: datetime
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    is_campaign_content: bool = Field(default=False)
```

### PostMetrics Model (Partitioned by month)

```python
class PostMetrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    likes: int
    comments: int
    shares: int
    views: Optional[int]
    engagement_rate: Decimal = Field(max_digits=5, decimal_places=2)
    collected_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    collection_interval: str  # 24hr, 3day, 5day, 7day
```

### RateLimitTracker Model

```python
class RateLimitTracker(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(index=True)
    requests_made: int = Field(default=0)
    requests_limit: int
    window_start: datetime
    window_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### PerformanceAlert Model

```python
class PerformanceAlert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id")
    campaign_id: Optional[int] = Field(foreign_key="campaign.id")
    alert_type: str  # engagement_drop, follower_drop, missed_deadline, negative_sentiment
    severity: str  # info, warning, critical
    message: str
    is_acknowledged: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
```

## API Endpoints

```python
# Manual Refresh
POST   /api/v1/kols/{id}/refresh                    # Trigger manual refresh
GET    /api/v1/kols/{id}/metrics                    # Get latest metrics
GET    /api/v1/kols/{id}/metrics/history            # Get historical metrics

# Scheduling
GET    /api/v1/kols/{id}/scraping-schedule          # Get schedule
PUT    /api/v1/kols/{id}/scraping-schedule          # Update schedule
POST   /api/v1/kols/{id}/scraping-schedule/pause    # Pause scraping
POST   /api/v1/kols/{id}/scraping-schedule/resume   # Resume scraping

# Content Monitoring
GET    /api/v1/kols/{id}/posts                      # Get detected posts
POST   /api/v1/posts/{id}/link-campaign             # Link post to campaign
GET    /api/v1/posts/{id}/metrics                   # Get post metrics
GET    /api/v1/campaigns/{id}/posts                 # Get campaign posts

# Alerts
GET    /api/v1/alerts                                # Get all alerts
PUT    /api/v1/alerts/{id}/acknowledge               # Acknowledge alert
GET    /api/v1/campaigns/{id}/alerts                 # Get campaign alerts

# Rate Limits (Admin only)
GET    /api/v1/admin/rate-limits                     # Get rate limit stats
```

## Scraping Implementation

### Smart Scheduling for 100K+ KOLs

```python
def distribute_scraping_across_day(total_kols: int) -> None:
    """
    Distribute 100K KOLs across 24 hours
    100,000 / 24 hours = 4,167 per hour = ~70 per minute
    """
    kols_per_minute = 70

    for minute in range(24 * 60):  # 1440 minutes in a day
        scheduled_time = datetime.now() + timedelta(minutes=minute)
        kols_batch = get_next_kols_batch(kols_per_minute)

        for kol in kols_batch:
            schedule_scraping_task.apply_async(
                args=[kol.id],
                eta=scheduled_time
            )
```

### Incremental Update Strategy

```python
def determine_scraping_priority(kol: KOL) -> int:
    """
    Priority 1-10:
    - Active in campaign: Priority 10 (daily)
    - Recently active: Priority 7 (every 3 days)
    - Inactive: Priority 3 (weekly)
    """
    if kol.is_in_active_campaign():
        return 10
    elif kol.last_campaign_date > datetime.now() - timedelta(days=30):
        return 7
    else:
        return 3
```

### Platform-Specific Scraping

#### Instagram Scraper

```python
async def scrape_instagram(handle: str) -> InstagramMetrics:
    """Scrape Instagram using Instagram Basic Display API"""
    try:
        user_data = await instagram_api.get_user(handle)
        media = await instagram_api.get_user_media(user_data['id'], limit=10)

        return InstagramMetrics(
            follower_count=user_data['followers_count'],
            following_count=user_data['follows_count'],
            post_count=user_data['media_count'],
            engagement_rate=calculate_engagement_rate(media),
            avg_likes=calculate_avg_likes(media),
            avg_comments=calculate_avg_comments(media)
        )
    except RateLimitError:
        await queue_for_retry(handle, 'instagram')
        raise
```

#### TikTok Scraper

```python
async def scrape_tiktok(handle: str) -> TikTokMetrics:
    """Scrape TikTok using TikTok API for Business"""
    try:
        user_info = await tiktok_api.get_user_info(handle)
        videos = await tiktok_api.get_user_videos(handle, count=10)

        return TikTokMetrics(
            follower_count=user_info['follower_count'],
            total_likes=user_info['likes_count'],
            video_count=user_info['video_count'],
            avg_views=calculate_avg_views(videos),
            engagement_rate=calculate_engagement_rate(videos)
        )
    except RateLimitError:
        await queue_for_retry(handle, 'tiktok')
        raise
```

## Rate Limit Management

### Rate Limit Configuration

```python
RATE_LIMITS = {
    'instagram': {'requests': 200, 'window': 3600},  # 200 per hour
    'tiktok': {'requests': 100, 'window': 3600},     # 100 per hour
    'youtube': {'requests': 10000, 'window': 86400}, # 10K per day
    'twitter': {'requests': 300, 'window': 900},     # 300 per 15 min
    'facebook': {'requests': 200, 'window': 3600}    # 200 per hour
}
```

### Rate Limit Checker

```python
async def check_and_wait_if_needed(platform: str) -> None:
    """Check rate limit and wait if necessary"""
    tracker = await get_rate_limit_tracker(platform)

    if tracker.requests_made >= tracker.requests_limit:
        wait_time = (tracker.window_end - datetime.now()).total_seconds()
        if wait_time > 0:
            logger.info(f"Rate limit reached for {platform}, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            await reset_rate_limit_tracker(platform)

    await increment_request_count(platform)
```

### Exponential Backoff

```python
async def scrape_with_retry(platform: str, handle: str, max_retries: int = 3) -> dict:
    """Scrape with exponential backoff on failure"""
    for attempt in range(max_retries):
        try:
            return await scrape_platform(platform, handle)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt * 60  # 1min, 2min, 4min
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
            else:
                raise
```

## Content Monitoring

### Post Detection

```python
async def detect_new_posts(kol_id: int) -> List[Post]:
    """Detect new posts since last check"""
    kol = await get_kol(kol_id)
    last_check = kol.last_post_check_at or datetime.now() - timedelta(days=7)

    new_posts = []
    for handle in kol.social_handles:
        platform_posts = await fetch_recent_posts(handle.platform, handle.handle, since=last_check)

        for post_data in platform_posts:
            # Check if post matches campaign hashtags/mentions
            is_campaign = await check_campaign_match(post_data, kol_id)

            post = Post(
                kol_id=kol_id,
                platform=handle.platform,
                post_id=post_data['id'],
                post_url=post_data['url'],
                post_type=post_data['type'],
                caption=post_data.get('caption'),
                posted_at=post_data['posted_at'],
                is_campaign_content=is_campaign
            )
            new_posts.append(post)

    return new_posts
```

### Metric Collection Schedule

```python
COLLECTION_INTERVALS = {
    '24hr': timedelta(hours=24),
    '3day': timedelta(days=3),
    '5day': timedelta(days=5),
    '7day': timedelta(days=7)
}

@celery_app.task
def collect_post_metrics_at_intervals(post_id: int):
    """Schedule metric collection at defined intervals"""
    post = get_post(post_id)

    for interval_name, interval_delta in COLLECTION_INTERVALS.items():
        collection_time = post.posted_at + interval_delta

        collect_post_metrics.apply_async(
            args=[post_id, interval_name],
            eta=collection_time
        )
```

## Performance Considerations

### Database Partitioning

```sql
-- Partition PostMetrics by month
CREATE TABLE post_metrics (
    id SERIAL,
    post_id INT,
    collected_at TIMESTAMP,
    ...
) PARTITION BY RANGE (collected_at);

CREATE TABLE post_metrics_2024_01 PARTITION OF post_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Indexes

```sql
CREATE INDEX idx_scraping_schedule_next_scrape ON scrapingschedule(next_scrape_at) WHERE is_active = true;
CREATE INDEX idx_post_kol_posted ON post(kol_id, posted_at DESC);
CREATE INDEX idx_post_metrics_post_collected ON postmetrics(post_id, collected_at DESC);
CREATE INDEX idx_performance_alert_created ON performancealert(created_at DESC) WHERE is_acknowledged = false;
```

### Caching

-   Latest metrics: 15 min TTL
-   Historical data: 1 hour TTL
-   Rate limit status: No cache (real-time)

## Background Tasks

```python
@celery_app.task
def scrape_kol_metrics(kol_id: int):
    """Scrape metrics for a single KOL"""

@celery_app.task
def process_scraping_queue():
    """Process queued scraping requests"""

@celery_app.task
def detect_new_posts_batch(kol_ids: List[int]):
    """Detect new posts for batch of KOLs"""

@celery_app.task
def collect_post_metrics(post_id: int, interval: str):
    """Collect metrics for a post at specific interval"""

@celery_app.task
def check_performance_alerts():
    """Check for performance issues and create alerts"""
```

## Testing Strategy

### Unit Tests

-   Metric calculation logic
-   Rate limit checking
-   Post detection algorithm
-   Alert threshold logic

### Integration Tests

-   End-to-end scraping flow
-   Multi-platform scraping
-   Rate limit handling
-   Post metric collection

### Load Tests

-   100K KOL scraping simulation
-   Concurrent API requests
-   Queue processing performance
