"""Social media scrapers package."""

from .base_scraper import (
    BaseScraper,
    SocialMetrics,
    PostData,
    ScrapingResult,
    ScrapingError,
    RateLimitError,
    AuthenticationError,
    PlatformError,
    ScrapingUtils
)

from .instagram_scraper import InstagramScraper
from .tiktok_scraper import TikTokScraper
from .youtube_scraper import YouTubeScraper
from .twitter_scraper import TwitterScraper
from .facebook_scraper import FacebookScraper

from .scraper_factory import (
    ScraperFactory,
    ScraperManager,
    SupportedPlatform
)

__all__ = [
    # Base classes and utilities
    'BaseScraper',
    'SocialMetrics',
    'PostData',
    'ScrapingResult',
    'ScrapingError',
    'RateLimitError',
    'AuthenticationError',
    'PlatformError',
    'ScrapingUtils',
    
    # Platform scrapers
    'InstagramScraper',
    'TikTokScraper',
    'YouTubeScraper',
    'TwitterScraper',
    'FacebookScraper',
    
    # Factory and management
    'ScraperFactory',
    'ScraperManager',
    'SupportedPlatform'
]