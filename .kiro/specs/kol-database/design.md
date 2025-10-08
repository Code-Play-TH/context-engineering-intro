# Design Document - KOL Database Management

## Overview

The KOL Database Management system provides comprehensive influencer profile management with support for manual entry, bulk CSV/Excel import, API-based discovery, third-party integration, automatic enrichment, and duplicate detection.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  KOL Manager │◀─────│   KOL        │◀─────│  + Elastic  │
└──────────────┘      │   Service    │      │  Search     │
                      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Celery    │
                     │  (Import &   │
                     │  Enrichment) │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Social      │
                     │  Media APIs  │
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class KOLService:
    async def create_kol(kol_data: KOLCreate) -> KOL
    async def get_kol(kol_id: int) -> KOL
    async def update_kol(kol_id: int, kol_data: KOLUpdate) -> KOL
    async def search_kols(query: str, filters: KOLFilters) -> List[KOL]
    async def soft_delete_kol(kol_id: int) -> None

class ImportService:
    async def upload_import_file(file: UploadFile) -> ImportJob
    async def validate_import_data(job_id: int) -> ImportValidation
    async def process_import(job_id: int) -> ImportResult
    async def get_import_status(job_id: int) -> ImportStatus

class EnrichmentService:
    async def enrich_kol_profile(kol_id: int) -> KOL
    async def fetch_social_metrics(platform: str, handle: str) -> SocialMetrics
    async def schedule_enrichment(kol_ids: List[int]) -> None

class DuplicateDetectionService:
    async def find_duplicates(kol_id: int) -> List[KOL]
    async def merge_kols(primary_id: int, duplicate_id: int) -> KOL
    async def scan_all_duplicates() -> List[DuplicatePair]
```

## Data Models

### KOL Model

```python
class KOL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    niche: List[str] = Field(sa_column=Column(ARRAY(String)))
    tier: Optional[str]  # nano, micro, mid, macro, mega
    tags: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    notes: Optional[str]
    status: str = Field(default="active")  # active, inactive, merged
    merged_into_id: Optional[int] = Field(foreign_key="kol.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    social_handles: List["SocialHandle"] = Relationship(back_populates="kol")
    metrics: List["KOLMetrics"] = Relationship(back_populates="kol")
    campaigns: List["CampaignKOL"] = Relationship(back_populates="kol")
```

### SocialHandle Model

```python
class SocialHandle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id")
    platform: str  # instagram, tiktok, youtube, twitter, facebook
    handle: str
    url: str
    follower_count: Optional[int]
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    last_enriched_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### KOLMetrics Model

```python
class KOLMetrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    platform: str
    follower_count: int
    engagement_rate: Decimal = Field(max_digits=5, decimal_places=2)
    avg_likes: Optional[int]
    avg_comments: Optional[int]
    avg_views: Optional[int]
    metrics_data: dict = Field(sa_column=Column(JSON))  # Platform-specific metrics
    scraped_at: datetime = Field(default_factory=datetime.utcnow, index=True)
```

### ImportJob Model

```python
class ImportJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    file_path: str
    status: str  # pending, validating, processing, completed, failed
    total_rows: int
    processed_rows: int = Field(default=0)
    success_count: int = Field(default=0)
    error_count: int = Field(default=0)
    errors: List[dict] = Field(default=[], sa_column=Column(JSON))
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime]
```

## API Endpoints

```python
# KOL Management
POST   /api/v1/kols                      # Create KOL
GET    /api/v1/kols                      # List/Search KOLs
GET    /api/v1/kols/{id}                 # Get KOL details
PUT    /api/v1/kols/{id}                 # Update KOL
DELETE /api/v1/kols/{id}                 # Soft delete KOL
POST   /api/v1/kols/{id}/enrich          # Trigger enrichment
GET    /api/v1/kols/{id}/duplicates      # Find duplicates
POST   /api/v1/kols/{id}/merge           # Merge with another KOL

# Import
POST   /api/v1/kols/import               # Upload import file
GET    /api/v1/kols/import/{job_id}      # Get import status
POST   /api/v1/kols/import/{job_id}/validate  # Validate import
POST   /api/v1/kols/import/{job_id}/process   # Process import

# API Discovery
POST   /api/v1/kols/discover             # Search social media APIs
POST   /api/v1/kols/discover/import      # Import from API results

# Third-party Integration
GET    /api/v1/kols/third-party/search   # Search third-party databases
POST   /api/v1/kols/third-party/import   # Import from third-party
```

## Business Logic

### Import Workflow

```python
1. Upload File → uploads/imports/pending/
2. Validate Data:
   - Check required fields (name, at least one social handle)
   - Validate formats (email, URLs)
   - Detect duplicates (fuzzy matching >85%)
3. Preview with Errors
4. User Confirms
5. Background Processing (Celery):
   - Process in batches of 100
   - Create KOL records
   - Create SocialHandle records
   - Move file to processed/ or failed/
6. Generate Import Report
```

### Duplicate Detection Algorithm

```python
def find_duplicates(kol: KOL) -> List[KOL]:
    candidates = []

    # 1. Exact social handle match
    if kol.social_handles:
        candidates += find_by_social_handles(kol.social_handles)

    # 2. Fuzzy name match (>85% similarity)
    candidates += fuzzy_search_name(kol.name, threshold=0.85)

    # 3. Email match
    if kol.email:
        candidates += find_by_email(kol.email)

    return deduplicate(candidates)
```

### Tier Calculation

```python
def calculate_tier(kol: KOL) -> str:
    max_followers = max([h.follower_count for h in kol.social_handles if h.follower_count])

    if max_followers < 10_000:
        return "nano"
    elif max_followers < 100_000:
        return "micro"
    elif max_followers < 500_000:
        return "mid"
    elif max_followers < 1_000_000:
        return "macro"
    else:
        return "mega"
```

## Search Implementation

### Elasticsearch Integration

```python
# Index mapping
{
  "mappings": {
    "properties": {
      "name": {"type": "text", "analyzer": "standard"},
      "niche": {"type": "keyword"},
      "location": {"type": "keyword"},
      "tier": {"type": "keyword"},
      "tags": {"type": "keyword"},
      "follower_count": {"type": "integer"},
      "engagement_rate": {"type": "float"}
    }
  }
}

# Search query with filters
GET /kols/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"name": "search_term"}}
      ],
      "filter": [
        {"terms": {"niche": ["fashion", "beauty"]}},
        {"range": {"follower_count": {"gte": 10000, "lte": 100000}}},
        {"range": {"engagement_rate": {"gte": 2.0}}}
      ]
    }
  }
}
```

## Performance Considerations

### Database Indexes

```sql
CREATE INDEX idx_kol_name ON kol USING gin(to_tsvector('english', name));
CREATE INDEX idx_kol_niche ON kol USING gin(niche);
CREATE INDEX idx_kol_status ON kol(status);
CREATE INDEX idx_social_handle_platform_handle ON socialhandle(platform, handle);
CREATE INDEX idx_kol_metrics_kol_scraped ON kolmetrics(kol_id, scraped_at DESC);
```

### Caching Strategy

-   KOL profile: 5 min TTL
-   Search results: 2 min TTL
-   Metrics: 15 min TTL

### Pagination

-   Default: 50 items per page
-   Max: 100 items per page
-   Use cursor-based pagination for large datasets

## Background Tasks

```python
@celery_app.task
def process_import_job(job_id: int):
    """Process KOL import in batches"""

@celery_app.task
def enrich_kol_profiles(kol_ids: List[int]):
    """Fetch latest social media metrics"""

@celery_app.task
def scan_duplicates():
    """Scan database for potential duplicates"""

@celery_app.task
def update_kol_tiers():
    """Recalculate KOL tiers based on latest follower counts"""
```

## Testing Strategy

### Unit Tests

-   KOL CRUD operations
-   Duplicate detection algorithm
-   Tier calculation logic
-   Import validation

### Integration Tests

-   CSV import end-to-end
-   API discovery and import
-   Enrichment workflow
-   Duplicate merge process
