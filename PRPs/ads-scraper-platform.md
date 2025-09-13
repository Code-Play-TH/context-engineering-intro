name: "Multi-Platform Ad Scraper with Clean Dashboard"
description: |

## Purpose
Build a production-ready multi-platform ad scraper that extracts campaign data from Facebook, Google Ads, and TikTok using their respective APIs. Features OAuth 2.0 authentication, daily automated scraping via cron jobs, and a clean, intuitive web dashboard for managing accounts and viewing performance data.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a comprehensive ad platform scraper that:
- Connects to Facebook Marketing API, Google Ads API, and TikTok Business API
- Implements secure OAuth 2.0 authentication for all platforms
- Features a clean, minimal web dashboard with responsive card-based design
- Runs daily automated data collection via cron jobs
- Handles rate limiting, error recovery, and token refresh automatically
- Provides real-time insights with today's ad spend per account

## Why
- **Business value**: Centralized ad performance tracking across all major platforms
- **Integration**: Clean OAuth-only authentication eliminates security risks
- **Problems solved**: Manual ad performance tracking, scattered data across platforms, credential security concerns

## What
A full-stack application featuring:
- FastAPI backend with SQLAlchemy ORM
- React frontend with NextUI for clean, minimal design
- OAuth 2.0 flows for Facebook, Google, and TikTok
- Automated daily data scraping with intelligent rate limiting
- Real-time dashboard with account cards and performance metrics

### Success Criteria
- [ ] Successfully authenticate with all three ad platforms using OAuth 2.0
- [ ] Daily cron job scrapes ad data without hitting rate limits
- [ ] Clean dashboard shows empty state and populated states correctly
- [ ] Add account modal supports all three platforms
- [ ] Error handling prevents system crashes when one platform fails
- [ ] All tests pass and code meets CLAUDE.md quality standards

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://developers.facebook.com/docs/marketing-api/authentication/
  why: OAuth flow, permissions (ads_read), access tokens, app setup
  
- url: https://developers.facebook.com/docs/marketing-api/insights/
  why: API endpoints, metrics (spend, impressions, clicks), rate limiting
  
- url: https://developers.google.com/google-ads/api/docs/oauth/cloud-project
  why: OAuth setup, developer token, client credentials, verification process
  
- url: https://developers.google.com/google-ads/api
  why: GAQL query language, reporting, campaign metrics, authentication
  
- url: https://business-api.tiktok.com/portal/docs
  why: Marketing API structure, OAuth flow, campaign data endpoints
  
- url: https://mui.com/store/collections/free-react-dashboard/
  why: Clean dashboard design patterns, responsive cards, minimal UI
  
- url: https://fastapi.tiangolo.com/project-generation/
  why: FastAPI project structure, async patterns, dependency injection

- file: CLAUDE.md
  why: Project conventions, testing requirements, code structure rules
  
- file: PRPs/templates/prp_base.md
  why: Implementation pattern to follow, validation approach
```

### Current Codebase tree
```bash
context-engineering-intro/
├── CLAUDE.md                    # Project rules and conventions
├── INITIAL.md                   # Feature requirements
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md         # PRP template structure
│   └── EXAMPLE_multi_agent_prp.md # Multi-agent implementation example
├── examples/                    # Empty - no existing patterns
├── README.md                    # Context engineering guide
└── LICENSE
```

### Desired Codebase tree with files to be added
```bash
context-engineering-intro/
├── backend/
│   ├── __init__.py             # Package init
│   ├── main.py                 # FastAPI application entry point
│   ├── models/
│   │   ├── __init__.py         # Package init
│   │   ├── database.py         # Database connection and base
│   │   ├── accounts.py         # Ad account models
│   │   ├── campaigns.py        # Campaign data models
│   │   └── auth_tokens.py      # OAuth token storage models
│   ├── api/
│   │   ├── __init__.py         # Package init
│   │   ├── auth.py             # OAuth endpoints for all platforms
│   │   ├── accounts.py         # Account management endpoints
│   │   ├── campaigns.py        # Campaign data endpoints
│   │   └── dashboard.py        # Dashboard summary endpoints
│   ├── services/
│   │   ├── __init__.py         # Package init
│   │   ├── facebook_api.py     # Facebook Marketing API client
│   │   ├── google_ads_api.py   # Google Ads API client
│   │   ├── tiktok_api.py       # TikTok Business API client
│   │   ├── rate_limiter.py     # Intelligent rate limiting service
│   │   └── data_collector.py   # Coordinated data collection service
│   ├── core/
│   │   ├── __init__.py         # Package init
│   │   ├── config.py           # Settings and environment variables
│   │   ├── security.py         # OAuth token handling and encryption
│   │   └── database.py         # Database connection management
│   └── tasks/
│       ├── __init__.py         # Package init
│       ├── celery_app.py       # Celery configuration
│       └── scraper_jobs.py     # Daily scraping tasks
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx   # Main dashboard with cards
│   │   │   ├── EmptyState.jsx  # Empty state for new users
│   │   │   ├── AccountCard.jsx # Individual platform account card
│   │   │   └── AddAccountModal.jsx # Platform selection modal
│   │   ├── services/
│   │   │   ├── api.js          # API client for backend
│   │   │   └── auth.js         # OAuth handling utilities
│   │   ├── hooks/
│   │   │   ├── useAccounts.js  # Account management hook
│   │   │   └── useAuth.js      # Authentication state hook
│   │   ├── App.jsx             # Main application component
│   │   └── main.jsx            # React entry point
│   ├── package.json            # React dependencies
│   └── vite.config.js          # Vite build configuration
├── tests/
│   ├── __init__.py             # Package init
│   ├── test_models.py          # Database model tests
│   ├── test_auth_endpoints.py  # OAuth endpoint tests
│   ├── test_facebook_api.py    # Facebook API client tests
│   ├── test_google_ads_api.py  # Google Ads API client tests
│   ├── test_tiktok_api.py      # TikTok API client tests
│   ├── test_rate_limiter.py    # Rate limiting tests
│   └── test_data_collector.py  # Data collection tests
├── docker-compose.yml          # Development environment
├── Dockerfile                  # Backend container
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── alembic.ini               # Database migration configuration
├── alembic/                  # Database migrations
└── README.md                 # Comprehensive setup guide
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Facebook Marketing API requires ads_read permission and Advanced Access approval
# CRITICAL: Google Ads API needs developer token + OAuth verification (3-5 business days)
# CRITICAL: TikTok Business API access tokens expire after 24 hours, refresh tokens after 1 year
# CRITICAL: All platforms have different rate limits - Facebook: varies by usage, Google: 10000 operations/day, TikTok: varies
# CRITICAL: OAuth refresh tokens must be stored securely and rotated properly
# CRITICAL: FastAPI requires async/await throughout - no sync functions in async context
# CRITICAL: SQLAlchemy 2.0 uses async sessions - async with get_session() pattern
# CRITICAL: Celery with Redis requires proper task serialization
# CRITICAL: React NextUI requires proper Tailwind CSS configuration
# CRITICAL: Never store user credentials - only OAuth access/refresh tokens
# CRITICAL: Each platform API has different data structures - need normalization layer
```

## Implementation Blueprint

### Data models and structure

```python
# models/accounts.py - Core account management
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class Platform(str, enum.Enum):
    FACEBOOK = "facebook"
    GOOGLE_ADS = "google_ads"
    TIKTOK = "tiktok"

class AdAccount(Base):
    __tablename__ = "ad_accounts"
    
    id: str = Column(String, primary_key=True)
    platform: Platform = Column(Enum(Platform), nullable=False)
    account_name: str = Column(String, nullable=False)
    account_id: str = Column(String, nullable=False)  # Platform-specific ID
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    last_sync: datetime = Column(DateTime, nullable=True)
    
    # Relationship to auth tokens
    auth_token = relationship("AuthToken", back_populates="account", uselist=False)
    campaigns = relationship("Campaign", back_populates="account")

# models/auth_tokens.py - Secure OAuth token storage
from cryptography.fernet import Fernet
from sqlalchemy import Column, String, DateTime, ForeignKey, LargeBinary
from .database import Base

class AuthToken(Base):
    __tablename__ = "auth_tokens"
    
    id: str = Column(String, primary_key=True)
    account_id: str = Column(String, ForeignKey("ad_accounts.id"), nullable=False)
    encrypted_access_token: bytes = Column(LargeBinary, nullable=False)
    encrypted_refresh_token: bytes = Column(LargeBinary, nullable=True)
    expires_at: datetime = Column(DateTime, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("AdAccount", back_populates="auth_token")

# models/campaigns.py - Normalized campaign data
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey
from .database import Base

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id: str = Column(String, primary_key=True)
    account_id: str = Column(String, ForeignKey("ad_accounts.id"), nullable=False)
    campaign_id: str = Column(String, nullable=False)  # Platform-specific ID
    campaign_name: str = Column(String, nullable=False)
    
    # Normalized metrics across all platforms
    spend: float = Column(Float, default=0.0)
    impressions: int = Column(Integer, default=0)
    clicks: int = Column(Integer, default=0)
    conversions: int = Column(Integer, default=0)
    
    date: datetime = Column(DateTime, nullable=False)
    synced_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("AdAccount", back_populates="campaigns")
```

### List of tasks to be completed in order

```yaml
Task 1: Setup Project Structure and Configuration
CREATE backend/core/config.py:
  - PATTERN: Use pydantic-settings like CLAUDE.md requires
  - Load all environment variables with validation
  - Include database URL, OAuth credentials, Redis configuration
  
CREATE .env.example:
  - Include all required API keys and configuration
  - Document OAuth setup requirements for each platform

Task 2: Database Models and Migrations
CREATE backend/models/:
  - PATTERN: Follow SQLAlchemy async patterns
  - Implement encrypted token storage using Fernet
  - Create normalized campaign data structure
  - Set up proper relationships between models

Task 3: OAuth Authentication System
CREATE backend/api/auth.py:
  - PATTERN: Follow OAuth 2.0 best practices from research
  - Implement separate OAuth flows for each platform
  - Handle token refresh and rotation automatically
  - Secure token encryption/decryption

Task 4: Platform API Clients
CREATE backend/services/{platform}_api.py:
  - PATTERN: Async HTTP clients using httpx
  - Implement platform-specific data extraction
  - Handle rate limiting with exponential backoff
  - Normalize data structures across platforms

Task 5: Rate Limiting and Error Handling
CREATE backend/services/rate_limiter.py:
  - PATTERN: Intelligent rate limiting from research
  - Implement per-platform rate limiting
  - Add exponential backoff with jitter
  - Handle platform-specific error responses

Task 6: Data Collection Service
CREATE backend/services/data_collector.py:
  - PATTERN: Coordinate collection across all platforms
  - Handle partial failures gracefully
  - Implement data normalization layer
  - Add comprehensive error logging

Task 7: Celery Task Scheduling
CREATE backend/tasks/:
  - PATTERN: Async Celery tasks for automated scraping
  - Schedule daily collection jobs
  - Handle task failures and retries
  - Monitor task performance

Task 8: FastAPI Endpoints
CREATE backend/api/:
  - PATTERN: Follow FastAPI async patterns
  - Implement dashboard data endpoints
  - Add account management endpoints
  - Include WebSocket for real-time updates

Task 9: React Frontend Components
CREATE frontend/src/components/:
  - PATTERN: Follow NextUI design system
  - Implement clean, minimal dashboard design
  - Create responsive account cards
  - Add platform selection modal

Task 10: Frontend Services and Hooks
CREATE frontend/src/services/ and hooks/:
  - PATTERN: Modern React patterns with custom hooks
  - Implement API client with error handling
  - Add OAuth redirect handling
  - Create state management for accounts

Task 11: Comprehensive Testing Suite
CREATE tests/:
  - PATTERN: Follow pytest patterns from CLAUDE.md
  - Mock external API calls properly
  - Test OAuth flows end-to-end
  - Ensure 80%+ coverage

Task 12: Documentation and Deployment
CREATE README.md and docker-compose.yml:
  - PATTERN: Comprehensive setup instructions
  - Include OAuth setup guides for each platform
  - Add troubleshooting section
  - Create development environment
```

### Per task pseudocode

```python
# Task 3: OAuth Authentication System
# services/facebook_api.py
async def initiate_facebook_oauth(redirect_uri: str) -> str:
    """Generate Facebook OAuth URL with required permissions."""
    # CRITICAL: Must include ads_read permission for Advanced Access
    permissions = ["ads_read", "ads_management"]
    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth"
    params = {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": ",".join(permissions),
        "response_type": "code",
        "state": generate_secure_state()  # CSRF protection
    }
    return f"{auth_url}?{urlencode(params)}"

async def handle_facebook_callback(code: str, state: str) -> AccessToken:
    """Exchange authorization code for access token."""
    # PATTERN: Secure token exchange with proper validation
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            data={
                "client_id": settings.FACEBOOK_CLIENT_ID,
                "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
                "code": code
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise OAuthError(f"Facebook OAuth failed: {response.text}")
        
        token_data = response.json()
        
        # CRITICAL: Encrypt tokens before storage
        encrypted_access = encrypt_token(token_data["access_token"])
        
        return AccessToken(
            access_token=encrypted_access,
            expires_at=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        )

# Task 5: Rate Limiting Implementation
class PlatformRateLimiter:
    """Intelligent rate limiter with platform-specific strategies."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.platform_limits = {
            Platform.FACEBOOK: {"requests_per_hour": 200, "burst": 50},
            Platform.GOOGLE_ADS: {"operations_per_day": 10000, "requests_per_second": 10},
            Platform.TIKTOK: {"requests_per_minute": 60, "burst": 20}
        }
    
    async def acquire_permit(self, platform: Platform, account_id: str) -> bool:
        """Acquire permission to make API request with exponential backoff."""
        # PATTERN: Token bucket algorithm with Redis
        key = f"rate_limit:{platform}:{account_id}"
        current = await self.redis.get(key)
        
        if current and int(current) >= self.platform_limits[platform]["burst"]:
            # CRITICAL: Apply exponential backoff
            backoff_time = min(2 ** self.get_retry_count(key), 32)  # Max 32 seconds
            await asyncio.sleep(backoff_time + random.uniform(0, 1))  # Add jitter
            return False
            
        await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1 hour window
        return True

# Task 6: Data Collection Service
class DataCollector:
    """Coordinated data collection across all platforms."""
    
    async def collect_daily_data(self, account_id: str) -> CollectionResult:
        """Collect yesterday's ad performance data."""
        account = await self.get_account(account_id)
        collector_map = {
            Platform.FACEBOOK: self.collect_facebook_data,
            Platform.GOOGLE_ADS: self.collect_google_ads_data,
            Platform.TIKTOK: self.collect_tiktok_data
        }
        
        try:
            # PATTERN: Platform-specific collection with normalization
            raw_data = await collector_map[account.platform](account)
            normalized_data = self.normalize_campaign_data(raw_data, account.platform)
            
            # CRITICAL: Batch insert for performance
            async with get_async_session() as session:
                session.add_all(normalized_data)
                await session.commit()
                
            return CollectionResult(
                success=True,
                campaigns_updated=len(normalized_data),
                last_sync=datetime.utcnow()
            )
            
        except RateLimitError as e:
            # PATTERN: Graceful degradation - reschedule for later
            logger.warning(f"Rate limited for {account.platform}: {e}")
            await self.schedule_retry(account_id, delay_minutes=60)
            raise
            
        except APIError as e:
            # PATTERN: Continue with other accounts on single failure
            logger.error(f"API error for {account.platform}: {e}")
            return CollectionResult(success=False, error=str(e))
```

### Integration Points
```yaml
ENVIRONMENT:
  - add to: .env
  - vars: |
      # Database
      DATABASE_URL=postgresql+asyncpg://user:pass@localhost/adscraper
      
      # Redis for Celery and rate limiting
      REDIS_URL=redis://localhost:6379/0
      
      # Facebook OAuth
      FACEBOOK_CLIENT_ID=your_app_id
      FACEBOOK_CLIENT_SECRET=your_app_secret
      FACEBOOK_REDIRECT_URI=http://localhost:8000/auth/facebook/callback
      
      # Google Ads OAuth
      GOOGLE_ADS_CLIENT_ID=your_client_id
      GOOGLE_ADS_CLIENT_SECRET=your_client_secret
      GOOGLE_ADS_DEVELOPER_TOKEN=your_dev_token
      
      # TikTok Business API
      TIKTOK_CLIENT_ID=your_client_id
      TIKTOK_CLIENT_SECRET=your_client_secret
      
      # Security
      SECRET_KEY=your_32_byte_key_for_encryption
      
CONFIG:
  - OAuth setup requires developer account registration on each platform
  - Facebook requires Advanced Access approval (3-5 business days)
  - Google Ads requires developer token and OAuth verification
  - TikTok requires Business API access approval
  
DEPENDENCIES:
  - Backend: fastapi, sqlalchemy[asyncio], asyncpg, celery[redis], httpx, cryptography
  - Frontend: react, @nextui-org/react, axios, react-router-dom
  - Development: docker, docker-compose, redis, postgresql
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check backend/ --fix          # Auto-fix style issues
mypy backend/                      # Type checking
black backend/                     # Code formatting

# Frontend linting
cd frontend && npm run lint         # ESLint checking
cd frontend && npm run type-check   # TypeScript checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_facebook_api.py
@pytest.mark.asyncio
async def test_facebook_oauth_flow():
    """Test Facebook OAuth initialization and callback handling."""
    service = FacebookAPIService()
    
    # Test OAuth URL generation
    oauth_url = await service.initiate_oauth("http://localhost/callback")
    assert "facebook.com" in oauth_url
    assert "ads_read" in oauth_url
    
    # Mock callback handling
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        token = await service.handle_callback("test_code", "test_state")
        assert token.access_token is not None

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiting with exponential backoff."""
    limiter = PlatformRateLimiter(mock_redis)
    
    # Should allow initial requests
    assert await limiter.acquire_permit(Platform.FACEBOOK, "test_account")
    
    # Should handle burst limits
    for _ in range(50):  # Exceed burst limit
        await limiter.acquire_permit(Platform.FACEBOOK, "test_account")
    
    # Should trigger backoff
    with patch('asyncio.sleep') as mock_sleep:
        result = await limiter.acquire_permit(Platform.FACEBOOK, "test_account")
        assert not result
        mock_sleep.assert_called()

@pytest.mark.asyncio 
async def test_data_collection():
    """Test coordinated data collection across platforms."""
    collector = DataCollector()
    
    with patch.object(collector, 'collect_facebook_data') as mock_collect:
        mock_collect.return_value = [
            {"campaign_id": "123", "spend": 100.0, "impressions": 1000}
        ]
        
        result = await collector.collect_daily_data("test_account")
        assert result.success
        assert result.campaigns_updated > 0

def test_token_encryption():
    """Test OAuth token encryption and decryption."""
    original_token = "sensitive_access_token_123"
    encrypted = encrypt_token(original_token)
    decrypted = decrypt_token(encrypted)
    
    assert encrypted != original_token
    assert decrypted == original_token
```

```bash
# Run tests iteratively until passing:
pytest tests/ -v --cov=backend --cov-report=term-missing
cd frontend && npm test

# If failing: Debug specific test, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start services
docker-compose up -d postgres redis
uvicorn backend.main:app --reload &
cd frontend && npm run dev &

# Test OAuth flows
curl -X GET "http://localhost:8000/auth/facebook/init" \
  -H "Content-Type: application/json"
# Expected: {"auth_url": "https://facebook.com/oauth/..."}

# Test dashboard endpoint
curl -X GET "http://localhost:8000/api/dashboard/summary" \
  -H "Authorization: Bearer test_token"
# Expected: {"total_accounts": 0, "total_spend": 0.0, "accounts": []}

# Test frontend
open http://localhost:3000
# Expected: Empty state with "Add Your First Ad Account" button
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v` and `npm test`
- [ ] No linting errors: `ruff check backend/` and `npm run lint`
- [ ] No type errors: `mypy backend/` and `npm run type-check`
- [ ] OAuth flows work for all three platforms
- [ ] Dashboard shows empty state and populated states correctly
- [ ] Rate limiting prevents API blocking
- [ ] Daily cron job collects data successfully
- [ ] Error handling prevents system crashes
- [ ] All sensitive data encrypted
- [ ] Docker environment runs successfully
- [ ] README includes complete setup instructions

---

## Anti-Patterns to Avoid
- ❌ Don't store user credentials - OAuth tokens only
- ❌ Don't skip rate limiting - all platforms will block you
- ❌ Don't use sync functions in FastAPI async context
- ❌ Don't hardcode API keys - use environment variables
- ❌ Don't ignore OAuth token refresh - implement automatic renewal
- ❌ Don't skip error handling - one platform failure shouldn't crash system
- ❌ Don't commit .env files or API credentials

## Confidence Score: 9/10

High confidence due to:
- Comprehensive research on all three platform APIs
- Clear OAuth implementation patterns from platform documentation
- Proven FastAPI + React architecture patterns
- Detailed rate limiting strategies from real-world implementations
- Complete validation pipeline with specific test cases

Minor uncertainty around platform-specific OAuth approval timelines, but documentation provides clear guidance for all setup requirements.