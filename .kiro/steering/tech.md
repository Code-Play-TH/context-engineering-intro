# Technology Stack

## Backend Technologies

-   **Language**: Python (PEP8 compliant, type hints required)
-   **Web Framework**: FastAPI for API endpoints
-   **Database**: PostgreSQL 15+ with psycopg2/asyncpg driver
-   **ORM**: SQLAlchemy/SQLModel for database models
-   **Migrations**: Alembic for database schema management
-   **Data Validation**: Pydantic for request/response models
-   **Authentication**: FastAPI Security with JWT tokens and OAuth2 password flow
-   **Background Jobs**: Celery with Redis broker for async tasks (social media scraping, report generation)
-   **Caching**: Redis for session storage and API response caching
-   **Data Import/Export**:
    -   **CSV/Excel**: pandas for reading/writing CSV and Excel files
    -   **Data Validation**: Great Expectations or custom validators for import data quality
    -   **Duplicate Detection**: fuzzy matching with fuzzywuzzy or RapidFuzz
-   **Report Generation**:
    -   **PowerPoint**: python-pptx for .pptx generation
    -   **PDF**: ReportLab or WeasyPrint for PDF generation
    -   **Charts**: matplotlib or plotly for chart generation
    -   **Template Storage**: Store templates as files in uploads/templates/
    -   **AI Template Analysis**: Use LLM (OpenAI/Anthropic) to analyze sample reports and generate template definitions
-   **File Storage**: Local filesystem or S3/MinIO for uploaded files and generated reports
-   **Environment Management**: python-dotenv with load_env()
-   **Code Formatting**: Black formatter
-   **Testing**: Pytest for unit tests

## Frontend Technologies

-   **Framework**: Next.js (React)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS (recommended)
-   **UI Components**: shadcn/ui or similar component library
-   **State Management**: React Context API / Zustand for global state
-   **Data Fetching**: TanStack Query (React Query) for API calls
-   **Forms**: React Hook Form with Zod validation
-   **Charts**: Recharts or Chart.js for analytics dashboards
-   **Tables**: TanStack Table for KOL database views
-   **Calendar**: FullCalendar or react-big-calendar for scheduling

## Database

### PostgreSQL Features to Leverage

-   **JSONB columns**: Store flexible social media metrics (each platform has different data structures)
-   **Array types**: Store tags, niches, and categories efficiently
-   **Full-text search**: Use `pg_trgm` extension for fuzzy KOL name/niche search
-   **Date ranges**: Track campaign periods with `DATERANGE` type
-   **Partial indexes**: Optimize queries on active KOLs and campaigns
-   **Time-series data**: Track engagement metrics over time (24hr, 3-day, 5-day, 7-day intervals)

### Recommended Extensions

-   `pg_trgm` - Fuzzy text search for KOL names and content
-   `btree_gin` - Index JSONB fields for faster queries
-   `uuid-ossp` - Generate UUIDs for primary keys (optional)

## Virtual Environment

-   Use `venv_linux` virtual environment for all Python commands
-   Always activate the virtual environment before running tests or executing Python scripts

## External Integrations

### Social Media APIs

-   Facebook Graph API
-   Instagram Basic Display API
-   TikTok API for Business
-   YouTube Data API v3
-   Twitter API v2

### Communication APIs

-   Line Messaging API
-   Discord API
-   Email service (SendGrid, AWS SES, or similar SMTP)

### Influencer Database APIs (Optional)

-   HypeAuditor API - Influencer discovery and analytics
-   Upfluence API - Influencer search and management
-   AspireIQ API - Influencer marketplace
-   Klear API - Influencer data and insights
-   Custom integrations based on client needs

### AI/LLM APIs (for Report Template Generation)

-   OpenAI API (GPT-4) or Anthropic Claude API
-   Used for analyzing sample report files and generating template definitions
-   Extract layout structure, placeholder positions, and styling from examples

## Common Commands

### Backend Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_filename.py

# Run with coverage
pytest --cov=app tests/
```

### Frontend Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Run linting
npm run lint

# Run type checking
npm run type-check
```

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Connect to PostgreSQL (local)
psql -U postgres -d kol_management

# Backup database
pg_dump -U postgres kol_management > backup.sql

# Restore database
psql -U postgres kol_management < backup.sql
```

### Background Jobs (Celery)

```bash
# Start Celery worker
celery -A app.worker worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.worker beat --loglevel=info

# Monitor tasks with Flower
celery -A app.worker flower
```

### Redis Operations

```bash
# Start Redis server
redis-server

# Connect to Redis CLI
redis-cli

# Monitor Redis commands
redis-cli monitor
```

### Code Quality

```bash
# Format code with Black
black app/ tests/

# Type checking (if using mypy)
mypy app/
```

## Scalability & Performance Strategies

### Enterprise-Scale Architecture (100K+ KOLs)

-   **Database Sharding**: Consider sharding KOL data by region or ID range for horizontal scaling
-   **Read Replicas**: Use PostgreSQL read replicas for analytics and reporting queries
-   **Elasticsearch**: Implement Elasticsearch for fast full-text search across 100K+ KOL profiles
-   **Message Queue**: Use RabbitMQ or AWS SQS for reliable task distribution across multiple workers
-   **Microservices**: Consider splitting into microservices (KOL service, Campaign service, Scraping service) if monolith becomes bottleneck

### Data Management for Large Datasets

-   **Database Partitioning**: Partition large tables (metrics, posts) by date range (monthly partitions)
-   **Table Partitioning Strategy**:
    -   `kol_metrics` - Partition by month (12 partitions per year)
    -   `social_posts` - Partition by quarter (4 partitions per year)
    -   Keep only 2 years of data in hot storage, archive older data
-   **Data Archiving**: Move old campaign data (>1 year) to S3/MinIO cold storage in Parquet format
-   **Pagination**: Always paginate API responses (default 50 items, max 100)
-   **Cursor-based Pagination**: Use cursor-based pagination for large datasets instead of offset
-   **Lazy Loading**: Load related data only when needed using SQLAlchemy lazy loading
-   **Aggregation Tables**: Pre-calculate daily/weekly/monthly statistics for faster reporting
-   **Materialized Views**: Use PostgreSQL materialized views for complex aggregations, refresh nightly

### Caching Strategy

-   **Redis Cache Layers**:
    -   L1: API response cache (5-15 minutes TTL)
    -   L2: Computed metrics cache (1-24 hours TTL)
    -   L3: Static data cache (KOL profiles, campaign info)
-   **Cache Invalidation**: Invalidate cache on data updates using cache keys pattern
-   **Cache Warming**: Pre-populate cache for frequently accessed data

### Background Job Optimization (100K+ KOLs)

-   **Multiple Worker Pools**: Separate worker pools for different task types (scraping, reporting, notifications)
-   **Task Prioritization**: High priority for manual requests, low priority for scheduled scraping
-   **Batch Processing**: Process KOLs in batches (50-100 per task) to reduce overhead
-   **Smart Scheduling**: Distribute daily scraping across 24 hours to avoid API rate limits
    -   Example: 100K KOLs / 24 hours = ~4,200 KOLs per hour = ~70 per minute
-   **Incremental Updates**: Only scrape active KOLs (in active campaigns) daily, others weekly/monthly
-   **Rate Limiting**: Implement exponential backoff for API rate limits per platform
-   **Task Retry**: Automatic retry with exponential backoff for failed tasks (max 3 retries)
-   **Task Monitoring**: Track task duration and failure rates in Flower dashboard
-   **Dead Letter Queue**: Move permanently failed tasks to DLQ for manual review

### Database Query Optimization (100K+ KOLs)

-   **Strategic Indexes**: Create indexes on frequently queried columns
    -   `kols(status, niche, engagement_rate)` - For filtering active KOLs
    -   `campaigns(status, start_date, end_date)` - For active campaigns
    -   `kol_metrics(kol_id, scraped_at)` - For latest metrics
-   **Composite Indexes**: Use composite indexes for multi-column filters
-   **Partial Indexes**: Index only active records (`WHERE status = 'active'`)
-   **Query Profiling**: Use `EXPLAIN ANALYZE` to identify slow queries (>100ms)
-   **Connection Pooling**: Use SQLAlchemy connection pool (pool_size=50, max_overflow=20 for 100K+ scale)
-   **Async Queries**: Use asyncpg for non-blocking database operations
-   **Query Result Caching**: Cache expensive aggregation queries in Redis
-   **Database Vacuum**: Schedule regular VACUUM ANALYZE to maintain performance

### API Performance

-   **Response Compression**: Enable gzip compression for API responses
-   **Field Selection**: Allow clients to specify which fields to return (`?fields=id,name,metrics`)
-   **Batch Endpoints**: Provide batch endpoints for fetching multiple resources
-   **ETags**: Implement ETags for conditional requests to reduce bandwidth
-   **CDN**: Use CDN for static assets and uploaded files

### Monitoring & Alerts

-   **Metrics to Track**:
    -   API response times (p50, p95, p99)
    -   Database query duration
    -   Celery task queue length
    -   Redis memory usage
    -   Social media API rate limit usage
-   **Alerting**: Set up alerts for slow queries (>1s), high error rates (>5%), queue backlog (>100 tasks)

## Important Considerations

-   **Rate Limiting**: All social media API calls must respect platform rate limits
-   **Authentication**: Handle token expiration and refresh mechanisms for all external APIs
-   **Caching**: Implement appropriate caching strategies to balance data freshness vs. API costs
-   **Background Jobs**: Use async processing for data scraping and report generation
-   **Error Handling**: Graceful fallbacks for all external API failures
-   **Data Growth**: Plan for data growth - implement archiving strategy from day one
-   **Cost Management**: Monitor API usage costs and optimize scraping frequency based on budget
-   **Scale Planning**: With 100K+ KOLs, expect:
    -   Database: ~500GB-1TB for 2 years of metrics data
    -   Daily scraping: ~100K API calls/day (manage rate limits carefully)
    -   Celery workers: 10-20 workers for smooth operation
    -   Redis memory: 8-16GB for caching and task queue
-   **Incremental Rollout**: Start with active KOLs only, gradually expand scraping coverage
