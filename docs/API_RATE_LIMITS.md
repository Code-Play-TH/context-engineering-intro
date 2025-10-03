# Social Media API Rate Limits Documentation
# KOL Influencer Management System

**Version:** 1.0
**Last Updated:** 2025-10-01
**Status:** Active

---

## 📋 Overview

This document details the rate limits, quotas, and best practices for integrating with social media platform APIs. Understanding these limits is critical for designing a scalable and compliant KOL management system.

**Key Principles:**
- Always respect platform rate limits
- Implement exponential backoff for retries
- Cache data where appropriate to reduce API calls
- Monitor API usage proactively
- Design for graceful degradation

---

## 📊 Platform Comparison

| Platform | Rate Limit Type | Primary Limit | Best for Real-time? | Cost |
|----------|----------------|---------------|---------------------|------|
| Instagram | Per-User & Per-App | 200 calls/hour/user | ⚠️ Moderate | Free (Business) |
| Facebook | Per-App & Per-User | 200 calls/hour/user | ⚠️ Moderate | Free (Basic tier) |
| YouTube | Quota Units | 10,000 units/day | ❌ No | Free (with quotas) |
| TikTok | Per-App | Varies by endpoint | ✅ Yes (webhooks) | Approval required |
| Twitter/X | Per-User & Per-App | 300 requests/15min | ✅ Yes | Paid tiers available |

---

## 1. Instagram Graph API

### Official Documentation
- **Docs**: https://developers.facebook.com/docs/graph-api/overview/rate-limiting
- **API Version**: v18.0 (as of 2025-10-01)
- **Authentication**: OAuth 2.0

### Rate Limits

#### App-Level Limits
- **Default**: 200 calls per hour per user
- **Extended**: Up to 4,800 calls per hour (requires app review)
- **Calculation**: Rolling hourly window

#### Business Discovery Limits
- **Public Data**: 5,000 calls per app per 24 hours
- **Use Case**: Discovering public business accounts

#### Media Retrieval
- **Get User Media**: 200 calls/hour/user
- **Get Media Insights**: 200 calls/hour/user
- **Get Hashtag Search**: 30 calls/hour/app

### Endpoints & Costs

| Endpoint | Method | Rate Limit | Data Retrieved | Cache TTL |
|----------|--------|------------|----------------|-----------|
| `/{ig-user-id}` | GET | 200/hr/user | Profile data | 24 hours |
| `/{ig-user-id}/media` | GET | 200/hr/user | Recent posts (max 25) | 1 hour |
| `/{ig-media-id}/insights` | GET | 200/hr/user | Post metrics | 6 hours |
| `/{ig-user-id}/insights` | GET | 200/hr/user | Account insights | 12 hours |
| `/ig_hashtag_search` | GET | 30/hr/app | Hashtag ID | 7 days |

### Insights Metrics Available

**Profile Insights** (lifetime, daily, weekly):
- `follower_count`
- `impressions`
- `reach`
- `profile_views`
- `website_clicks`

**Post Insights**:
- `engagement` (likes + comments + saves)
- `impressions`
- `reach`
- `saved`
- `video_views` (for videos)

### Quota Management Strategy

```python
# Recommended polling frequency
POLLING_INTERVALS = {
    "profile_metrics": 24 * 3600,     # 24 hours
    "recent_media": 6 * 3600,         # 6 hours
    "media_insights": 12 * 3600,      # 12 hours
    "stories": 2 * 3600,              # 2 hours (24h lifetime)
}

# Priority-based fetching
PRIORITY_LEVELS = {
    "active_campaign": 1,             # Fetch every cycle
    "monitored_kol": 2,               # Fetch daily
    "inactive_kol": 3,                # Fetch weekly
}
```

### Error Codes & Handling

| Error Code | Meaning | Retry Strategy |
|-----------|---------|----------------|
| 4 | Rate limit exceeded | Wait 1 hour, exponential backoff |
| 17 | Too many calls to endpoint | Reduce frequency, implement caching |
| 80004 | API call limit reached | Wait until quota resets |
| 190 | Access token expired | Refresh token, retry request |

### Best Practices

1. **Batch Requests**: Use batch API to combine multiple requests
   ```
   POST https://graph.facebook.com/
   batch=[{...}, {...}]
   ```
2. **Field Selection**: Request only needed fields to reduce response size
   ```
   ?fields=id,username,followers_count,media_count
   ```
3. **Webhooks**: Use webhooks for real-time updates (requires Business approval)
4. **Caching**: Cache profile data for 24h, media insights for 6h

---

## 2. Facebook Graph API

### Official Documentation
- **Docs**: https://developers.facebook.com/docs/graph-api/overview/rate-limiting
- **API Version**: v18.0
- **Authentication**: OAuth 2.0

### Rate Limits

#### Page Public Content Access
- **Application-Level**: 200 calls per hour per user
- **Page-Level**: 4,800 calls per hour (business verified apps)

#### Marketing API
- **Ad Account**: Separate tier, higher limits for verified advertisers
- **Insights API**: Subject to async queries for large datasets

### Endpoints & Costs

| Endpoint | Method | Rate Limit | Data Retrieved | Cache TTL |
|----------|--------|------------|----------------|-----------|
| `/{page-id}` | GET | 200/hr/user | Page info | 24 hours |
| `/{page-id}/posts` | GET | 200/hr/user | Page posts | 1 hour |
| `/{page-id}/insights` | GET | 200/hr/user | Page insights | 12 hours |
| `/{post-id}` | GET | 200/hr/user | Post details | 6 hours |
| `/{post-id}/insights` | GET | 200/hr/user | Post insights | 6 hours |

### Insights Metrics Available

**Page Insights**:
- `page_fans` (total followers)
- `page_impressions`
- `page_engaged_users`
- `page_post_engagements`
- `page_views_total`

**Post Insights**:
- `post_impressions`
- `post_engaged_users`
- `post_clicks`
- `post_reactions_by_type_total`

### Error Handling

| Error Code | Meaning | Retry Strategy |
|-----------|---------|----------------|
| 4 | Rate limit | Wait 1 hour |
| 17 | Too many requests | Reduce frequency |
| 190 | Token expired | Refresh OAuth token |
| 200 | Permission denied | Re-request permissions |

### Best Practices

1. **Use Page Access Tokens**: Long-lived (60 days), auto-renewable
2. **Batch Requests**: Combine up to 50 requests
3. **Async Insights**: For large datasets, use async insights API
4. **Webhooks**: Real-time updates for page changes

---

## 3. YouTube Data API v3

### Official Documentation
- **Docs**: https://developers.google.com/youtube/v3/getting-started
- **Authentication**: OAuth 2.0 or API Key
- **Quota System**: Unit-based (not request-based)

### Quota System

**Daily Quota**: 10,000 units per project per day (default)
**Quota Reset**: Midnight Pacific Time (PT)

#### Cost per Operation (in units)

| Operation | Method | Units | Data Retrieved | Cache TTL |
|-----------|--------|-------|----------------|-----------|
| `channels.list` | GET | 1 | Channel info | 24 hours |
| `videos.list` | GET | 1 | Video details | 6 hours |
| `search.list` | GET | 100 | Search results | 12 hours |
| `playlistItems.list` | GET | 1 | Playlist videos | 6 hours |
| `comments.list` | GET | 1 | Video comments | 12 hours |
| `videos.insert` | POST | 1600 | Upload video | N/A |
| `commentThreads.insert` | POST | 50 | Post comment | N/A |

### Example Daily Budget

```python
# With 10,000 units/day quota
DAILY_OPERATIONS = {
    "channel_info": 100,        # 100 units (100 KOLs)
    "video_details": 500,       # 500 units (500 videos)
    "video_analytics": 1000,    # via YouTube Analytics API (separate quota)
    "search": 50,               # 5,000 units (50 searches)
    # Remaining: 3,400 units for retries/misc
}

# Priority allocation
PRIORITY_QUOTA = {
    "active_campaigns": 5000,   # 50% of quota
    "daily_sync": 3000,         # 30% of quota
    "adhoc_requests": 2000,     # 20% of quota
}
```

### YouTube Analytics API (Separate Quota)

**Purpose**: Historical performance data
**Quota**: Separate from YouTube Data API (typically higher)
**Rate Limit**: 3,000 requests per 100 seconds per user

**Key Metrics**:
- `views`, `likes`, `dislikes`, `comments`
- `estimatedMinutesWatched`, `averageViewDuration`
- `subscribersGained`, `subscribersLost`
- `ctr` (click-through rate), `impressions`

### Quota Management Strategy

```python
# Staggered sync to avoid daily quota exhaustion
SYNC_SCHEDULE = {
    "00:00-04:00": "active_campaigns",      # 4000 units
    "04:00-08:00": "priority_kols",         # 3000 units
    "08:00-16:00": "regular_sync",          # 2000 units
    "16:00-24:00": "buffer",                # 1000 units
}

# Exponential backoff for quota errors
def retry_with_quota_awareness(func):
    if quota_exceeded:
        wait_until_midnight_pt()
    elif quota_low:
        reduce_non_critical_operations()
```

### Error Codes & Handling

| Error Code | Meaning | Retry Strategy |
|-----------|---------|----------------|
| 403 quotaExceeded | Daily quota used up | Wait until midnight PT (next day) |
| 403 rateLimitExceeded | Too many requests/second | Exponential backoff, retry after 1 min |
| 401 unauthorized | Invalid/expired token | Refresh OAuth token |
| 404 videoNotFound | Video deleted/private | Mark as unavailable, don't retry |

### Best Practices

1. **Use API Keys for Read-Only**: Save OAuth quota for write operations
2. **Batch Requests**: Use `id` parameter with comma-separated IDs (up to 50)
   ```
   videos.list?id=video1,video2,video3&part=snippet,statistics
   ```
3. **Minimize `part` Parameter**: Only request needed parts (snippet, statistics, etc.)
4. **Cache Aggressively**: Channel info (24h), video stats (6h)
5. **Monitor Quota Usage**: Use Google Cloud Console quota dashboard
6. **Request Quota Increase**: If needed, apply via Google Cloud Console

---

## 4. TikTok Business API

### Official Documentation
- **Docs**: https://developers.tiktok.com/doc/overview
- **Authentication**: OAuth 2.0
- **Access**: Requires application approval

### Rate Limits

**Note**: TikTok API access is restricted and requires business verification

#### Display API (Public Data)
- **Rate Limit**: Varies by endpoint, typically 100-500 requests/day
- **Approval**: Requires detailed use case explanation
- **Data Access**: Public profile, video data

#### Marketing API (for Advertisers)
- **Rate Limit**: Higher limits, typically 1000+ requests/hour
- **Access**: Requires ad account

### Endpoints & Costs

| Endpoint | Method | Approx. Limit | Data Retrieved | Cache TTL |
|----------|--------|---------------|----------------|-----------|
| `/user/info/` | GET | 500/day | User profile | 24 hours |
| `/video/list/` | GET | 500/day | User videos | 6 hours |
| `/video/query/` | GET | 1000/day | Video details | 6 hours |
| `/video/data/` | GET | 500/day | Video metrics | 12 hours |

### Metrics Available

**Profile Metrics**:
- `follower_count`
- `following_count`
- `likes_count`
- `video_count`

**Video Metrics**:
- `view_count`
- `like_count`
- `comment_count`
- `share_count`
- `play_count`
- `download_count` (if enabled)

### Webhooks

TikTok supports webhooks for real-time updates:
- **Event Types**: video_publish, user_update
- **Benefit**: Reduces API polling needs
- **Requirement**: Verified business account

### Error Codes & Handling

| Error Code | Meaning | Retry Strategy |
|-----------|---------|----------------|
| 50002 | Rate limit exceeded | Wait 24 hours, reduce frequency |
| 10002 | Token expired | Refresh OAuth token |
| 10005 | Permission denied | Re-request scopes |
| 50004 | API not available | Check for platform updates |

### Best Practices

1. **Apply Early**: API approval can take 2-4 weeks
2. **Detailed Use Case**: Clearly explain data usage to get approved
3. **Use Webhooks**: Reduces polling needs significantly
4. **Respect Content Policy**: Follow TikTok's community guidelines
5. **Monitor Approval Status**: TikTok may revoke access for violations

### Alternative: Web Scraping (NOT RECOMMENDED)

⚠️ **Warning**: Web scraping violates TikTok's Terms of Service
- **Risk**: Legal action, IP bans
- **Alternative**: Use official API with proper approval

---

## 5. Twitter/X API v2

### Official Documentation
- **Docs**: https://developer.twitter.com/en/docs/twitter-api/rate-limits
- **Authentication**: OAuth 2.0, Bearer Token
- **Access Tiers**: Free, Basic, Pro, Enterprise

### Rate Limits by Tier

| Tier | Monthly Tweets | Rate Limits | Cost |
|------|---------------|-------------|------|
| Free | 1,500/month | 10,000 read requests/month | $0 |
| Basic | 3,000/month | 100,000 read requests/month | $100/month |
| Pro | 100,000/month | 1,000,000 read requests/month | $5,000/month |
| Enterprise | Custom | Custom | Custom pricing |

**Recommended for KOL System**: Basic or Pro tier

### Endpoints & Costs

#### User Endpoints
| Endpoint | Method | Limit (Basic) | Limit (Pro) | Data Retrieved | Cache TTL |
|----------|--------|---------------|-------------|----------------|-----------|
| `/users/{id}` | GET | 300/15min | 900/15min | User profile | 24 hours |
| `/users/{id}/tweets` | GET | 100/15min | 300/15min | User tweets (max 100) | 1 hour |
| `/tweets/{id}` | GET | 300/15min | 900/15min | Tweet details | 6 hours |
| `/tweets/search/recent` | GET | 10/15min | 60/15min | Recent tweets | 15 min |

#### Metrics Endpoints (requires user auth)
| Endpoint | Method | Limit (Basic) | Limit (Pro) | Data Retrieved |
|----------|--------|---------------|-------------|----------------|
| `/tweets/{id}/metrics` | GET | 300/15min | 900/15min | Tweet analytics |

### Metrics Available

**Public Metrics** (no auth required):
- `retweet_count`
- `reply_count`
- `like_count`
- `quote_count`
- `impression_count` (limited)

**Organic Metrics** (requires user auth):
- `impression_count`
- `url_link_clicks`
- `user_profile_clicks`

**Promoted Metrics** (for ads):
- `impressions`
- `engagements`
- `spend`

### Real-Time Streaming

**Filtered Stream** (requires rules setup):
- **Basic Tier**: 25 rules, 50 requests/month
- **Pro Tier**: 1,000 rules, unlimited requests
- **Use Case**: Monitor brand mentions, hashtags in real-time

### Error Codes & Handling

| Error Code | Meaning | Retry Strategy |
|-----------|---------|----------------|
| 429 | Rate limit exceeded | Wait until reset time (15 min window) |
| 401 | Unauthorized | Check token validity |
| 403 | Forbidden | Verify endpoint access for tier |
| 88 | Rate limit (v1.1) | Wait for reset |

### Best Practices

1. **Use v2 API**: v1.1 is deprecated
2. **Upgrade Tier**: Free tier too limited for production use
3. **Implement Streaming**: More efficient than polling for real-time data
4. **Batch Requests**: Use comma-separated IDs (up to 100)
   ```
   /users?ids=id1,id2,id3
   ```
5. **Request Only Needed Fields**: Use `user.fields`, `tweet.fields` parameters
6. **Monitor Rate Limits**: Check `x-rate-limit-remaining` header
7. **Graceful Degradation**: Handle tier limits gracefully

---

## 🛡️ Rate Limit Handling Strategy

### 1. Detection

**Response Headers**:
- `X-RateLimit-Limit`: Max requests allowed
- `X-RateLimit-Remaining`: Requests left in window
- `X-RateLimit-Reset`: Timestamp when limit resets

**Example**:
```http
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 150
X-RateLimit-Reset: 1696190400
```

### 2. Proactive Throttling

```python
class RateLimiter:
    def __init__(self, max_calls, window_seconds):
        self.max_calls = max_calls
        self.window = window_seconds
        self.calls = []

    def should_throttle(self):
        now = time.time()
        # Remove calls outside window
        self.calls = [t for t in self.calls if now - t < self.window]

        if len(self.calls) >= self.max_calls:
            return True  # Throttle
        return False

    def record_call(self):
        self.calls.append(time.time())
```

### 3. Exponential Backoff

```python
def exponential_backoff_retry(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

### 4. Retry-After Header

```python
def respect_retry_after(response):
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            time.sleep(int(retry_after))
        else:
            # Default to 1 hour for Instagram/Facebook
            time.sleep(3600)
```

### 5. Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None

    def call(self, func):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

---

## 📊 Monitoring & Alerting

### Key Metrics to Track

1. **API Call Volume**: Requests per minute/hour/day per platform
2. **Error Rate**: Percentage of failed requests
3. **Rate Limit Hits**: Frequency of 429 errors
4. **Quota Usage**: Remaining quota (especially YouTube)
5. **Response Time**: API latency trends
6. **Cache Hit Rate**: Effectiveness of caching strategy

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Rate limit hits | > 10/hour | > 50/hour |
| Error rate | > 5% | > 15% |
| Quota usage (YouTube) | > 80% | > 95% |
| API response time | > 2s avg | > 5s avg |
| Cache hit rate | < 70% | < 50% |

### Grafana Dashboard

**Panels to Include**:
- API calls per platform (time series)
- Error rate by endpoint (gauge)
- Quota usage (progress bar)
- Rate limit violations (counter)
- Cache performance (pie chart)

---

## 🗄️ Caching Strategy

### Cache Levels

#### 1. Application Cache (Redis)
- **TTL**: 5 minutes - 24 hours (depends on data type)
- **Use Case**: Frequently accessed, rarely changing data

```python
CACHE_TTL = {
    "profile_info": 24 * 3600,     # 24 hours
    "media_list": 6 * 3600,        # 6 hours
    "media_insights": 12 * 3600,   # 12 hours
    "search_results": 15 * 60,     # 15 minutes
}
```

#### 2. Database Cache
- **TTL**: Permanent (updated on sync)
- **Use Case**: Historical data, trend analysis

#### 3. CDN Cache
- **TTL**: 1 hour
- **Use Case**: Profile images, public content

### Cache Invalidation

**Strategies**:
1. **TTL-based**: Expire after set time
2. **Event-based**: Invalidate on webhook event (post published, profile updated)
3. **Manual**: Admin can force refresh

---

## 🚀 Optimization Techniques

### 1. Batch Requests

Instead of:
```python
for user_id in user_ids:
    get_user(user_id)  # 100 API calls
```

Use:
```python
get_users_batch(user_ids)  # 1 API call (up to 100 IDs)
```

### 2. Conditional Requests (ETags)

```http
GET /api/users/123
If-None-Match: "686897696a7c876b7e"

Response: 304 Not Modified (if no changes)
```

### 3. Pagination Optimization

- Request only needed page size
- Use cursor-based pagination for large datasets
- Cache paginated results

### 4. Field Selection

```http
# Bad: Fetches all fields
GET /users/123

# Good: Fetches only needed fields
GET /users/123?fields=id,username,followers_count
```

### 5. Webhooks Over Polling

**Polling**:
- Check for updates every 5 minutes = 288 requests/day

**Webhooks**:
- Get notified instantly = 0 polling requests

---

## 📋 Implementation Checklist

### Phase 1: Foundation
- [x] Document rate limits per platform
- [ ] Implement rate limiting middleware
- [ ] Set up Redis caching
- [ ] Create rate limit tracking database tables
- [ ] Implement exponential backoff

### Phase 2: Monitoring
- [ ] Set up Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Configure alerting (Slack/Email)
- [ ] Implement quota usage reporting

### Phase 3: Optimization
- [ ] Implement batch requests
- [ ] Set up webhook receivers
- [ ] Optimize caching strategy
- [ ] Implement circuit breakers

### Phase 4: Compliance
- [ ] Review and comply with all ToS
- [ ] Implement data retention policies
- [ ] Set up audit logging for API calls
- [ ] Conduct quarterly rate limit review

---

## 📞 Support & Resources

### Platform Support

| Platform | Support Channel | Response Time |
|----------|----------------|---------------|
| Instagram | Developer Forums | 2-5 days |
| Facebook | Business Support | 1-3 days (verified apps) |
| YouTube | Google Cloud Support | Varies by tier |
| TikTok | Developer Portal | 3-7 days |
| Twitter | Developer Forums | 1-2 days (paid tiers) |

### Internal Contacts

**API Integration Team**: api-team@kolsystem.com
**DevOps (Rate Limit Issues)**: devops@kolsystem.com
**On-Call Engineer**: oncall@kolsystem.com

---

## 📝 Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-01 | Initial API rate limits documentation | Integration Team |

---

**Document Owner**: API Integration Lead
**Reviewed By**: CTO, Backend Team Lead
**Next Review**: 2025-12-01 (quarterly review)
