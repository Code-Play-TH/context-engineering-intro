"""Base scraper interface and common utilities for social media platforms."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class RateLimitError(ScrapingError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(ScrapingError):
    """Exception raised when authentication fails."""
    pass


class PlatformError(ScrapingError):
    """Exception raised when platform-specific error occurs."""
    pass


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


@dataclass
class SocialMetrics:
    """Standard social media metrics across platforms."""
    follower_count: int
    following_count: int
    post_count: int
    engagement_rate: Decimal
    avg_likes: Decimal
    avg_comments: Decimal
    avg_shares: Decimal = Decimal('0')
    avg_views: Optional[Decimal] = None
    platform_specific: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.platform_specific is None:
            self.platform_specific = {}


@dataclass
class PostData:
    """Standard post data structure."""
    post_id: str
    url: str
    post_type: str
    caption: Optional[str]
    posted_at: datetime
    likes: int
    comments: int
    shares: int
    views: Optional[int] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []


class BaseScraper(ABC):
    """Abstract base class for social media platform scrapers."""
    
    def __init__(self, platform_name: str, api_config: Dict[str, Any]):
        self.platform_name = platform_name
        self.api_config = api_config
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")
        
        # Rate limiting
        self.requests_made = 0
        self.window_start = datetime.utcnow()
        self.rate_limit = api_config.get('rate_limit', 100)
        self.window_duration = api_config.get('window_duration', 3600)  # seconds
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform API."""
        pass
    
    @abstractmethod
    async def get_user_metrics(self, handle: str) -> SocialMetrics:
        """Get user metrics for a given handle."""
        pass
    
    @abstractmethod
    async def get_recent_posts(self, handle: str, limit: int = 10) -> List[PostData]:
        """Get recent posts for a given handle."""
        pass
    
    @abstractmethod
    async def get_post_metrics(self, post_id: str) -> PostData:
        """Get metrics for a specific post."""
        pass
    
    def check_rate_limit(self) -> bool:
        """Check if we can make another request without exceeding rate limits."""
        now = datetime.utcnow()
        
        # Reset window if expired
        if (now - self.window_start).total_seconds() >= self.window_duration:
            self.requests_made = 0
            self.window_start = now
        
        return self.requests_made < self.rate_limit
    
    def record_request(self) -> None:
        """Record that a request was made."""
        self.requests_made += 1
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        now = datetime.utcnow()
        window_elapsed = (now - self.window_start).total_seconds()
        window_remaining = max(0, self.window_duration - window_elapsed)
        
        return {
            'requests_made': self.requests_made,
            'rate_limit': self.rate_limit,
            'requests_remaining': max(0, self.rate_limit - self.requests_made),
            'window_remaining_seconds': int(window_remaining),
            'reset_at': self.window_start + timedelta(seconds=self.window_duration)
        }
    
    async def scrape_with_retry(
        self, 
        operation_func, 
        *args, 
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """Execute scraping operation with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Check rate limit before making request
                if not self.check_rate_limit():
                    status = self.get_rate_limit_status()
                    wait_time = status['window_remaining_seconds']
                    self.logger.warning(
                        f"Rate limit exceeded for {self.platform_name}. "
                        f"Waiting {wait_time} seconds."
                    )
                    raise RateLimitError(
                        f"Rate limit exceeded. Try again in {wait_time} seconds.",
                        retry_after=wait_time
                    )
                
                # Record request and execute operation
                self.record_request()
                start_time = datetime.utcnow()
                
                result = await operation_func(*args, **kwargs)
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.logger.info(
                    f"Successfully scraped {self.platform_name} in {duration:.2f}s "
                    f"(attempt {attempt + 1})"
                )
                
                return result
                
            except RateLimitError:
                # Don't retry rate limit errors immediately
                raise
                
            except (AuthenticationError, PlatformError) as e:
                self.logger.error(f"Non-retryable error in {self.platform_name}: {e}")
                raise
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {self.platform_name}: {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"All {max_retries + 1} attempts failed for {self.platform_name}: {e}"
                    )
        
        # If we get here, all retries failed
        raise ScrapingError(f"Failed after {max_retries + 1} attempts: {last_exception}")
    
    def calculate_engagement_rate(
        self, 
        likes: int, 
        comments: int, 
        shares: int, 
        follower_count: int
    ) -> Decimal:
        """Calculate engagement rate from metrics."""
        if follower_count == 0:
            return Decimal('0.00')
        
        total_engagement = likes + comments + shares
        rate = (total_engagement / follower_count) * 100
        return Decimal(str(round(rate, 2)))
    
    def calculate_average_metrics(self, posts: List[PostData]) -> Tuple[Decimal, Decimal, Decimal, Optional[Decimal]]:
        """Calculate average metrics from a list of posts."""
        if not posts:
            return Decimal('0'), Decimal('0'), Decimal('0'), None
        
        total_likes = sum(post.likes for post in posts)
        total_comments = sum(post.comments for post in posts)
        total_shares = sum(post.shares for post in posts)
        total_views = sum(post.views for post in posts if post.views is not None)
        
        count = len(posts)
        views_count = len([post for post in posts if post.views is not None])
        
        avg_likes = Decimal(str(round(total_likes / count, 2)))
        avg_comments = Decimal(str(round(total_comments / count, 2)))
        avg_shares = Decimal(str(round(total_shares / count, 2)))
        avg_views = Decimal(str(round(total_views / views_count, 2))) if views_count > 0 else None
        
        return avg_likes, avg_comments, avg_shares, avg_views
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        if not text:
            return []
        
        import re
        hashtags = re.findall(r'#(\w+)', text)
        return [tag.lower() for tag in hashtags]
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text."""
        if not text:
            return []
        
        import re
        mentions = re.findall(r'@(\w+)', text)
        return [mention.lower() for mention in mentions]
    
    def validate_handle(self, handle: str) -> str:
        """Validate and normalize social media handle."""
        if not handle:
            raise ValueError("Handle cannot be empty")
        
        # Remove @ symbol if present
        handle = handle.lstrip('@')
        
        # Basic validation (alphanumeric, underscore, dot)
        import re
        if not re.match(r'^[a-zA-Z0-9._]+$', handle):
            raise ValueError(f"Invalid handle format: {handle}")
        
        return handle.lower()
    
    async def health_check(self) -> bool:
        """Check if the API is accessible and authentication is valid."""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Health check failed for {self.platform_name}: {e}")
            return False


class ScrapingUtils:
    """Utility functions for scraping operations."""
    
    @staticmethod
    def normalize_engagement_rate(rate: float) -> Decimal:
        """Normalize engagement rate to a standard format."""
        return Decimal(str(round(max(0, min(100, rate)), 2)))
    
    @staticmethod
    def detect_bot_followers(
        current_followers: int, 
        previous_followers: int, 
        time_diff_hours: float
    ) -> bool:
        """Detect potential bot follower activity."""
        if time_diff_hours <= 0 or previous_followers <= 0:
            return False
        
        growth = current_followers - previous_followers
        growth_rate = (growth / previous_followers) * 100
        
        # Suspicious if growth > 50% in less than 24 hours
        if time_diff_hours < 24 and growth_rate > 50:
            return True
        
        # Suspicious if growth > 100% in less than 48 hours
        if time_diff_hours < 48 and growth_rate > 100:
            return True
        
        return False
    
    @staticmethod
    def calculate_growth_rate(current: int, previous: int) -> Decimal:
        """Calculate growth rate percentage."""
        if previous == 0:
            return Decimal('0.00') if current == 0 else Decimal('100.00')
        
        growth = ((current - previous) / previous) * 100
        return Decimal(str(round(growth, 2)))
    
    @staticmethod
    def is_engagement_anomaly(
        current_rate: float, 
        average_rate: float, 
        threshold_percentage: float = 20.0
    ) -> bool:
        """Detect engagement rate anomalies."""
        if average_rate == 0:
            return False
        
        change_percentage = abs((current_rate - average_rate) / average_rate) * 100
        return change_percentage > threshold_percentage
    
    @staticmethod
    def format_large_number(number: int) -> str:
        """Format large numbers with K, M, B suffixes."""
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.1f}K"
        else:
            return str(number)
    
    @staticmethod
    def parse_relative_time(time_str: str) -> Optional[datetime]:
        """Parse relative time strings like '2h ago', '3d ago'."""
        if not time_str:
            return None
        
        import re
        
        # Match patterns like "2h", "3d", "1w", "5m"
        match = re.match(r'(\d+)([smhdw])', time_str.lower().replace(' ago', '').replace(' ', ''))
        if not match:
            return None
        
        value, unit = match.groups()
        value = int(value)
        
        now = datetime.utcnow()
        
        if unit == 's':
            return now - timedelta(seconds=value)
        elif unit == 'm':
            return now - timedelta(minutes=value)
        elif unit == 'h':
            return now - timedelta(hours=value)
        elif unit == 'd':
            return now - timedelta(days=value)
        elif unit == 'w':
            return now - timedelta(weeks=value)
        
        return None