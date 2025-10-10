"""Factory for creating and managing social media platform scrapers."""
from typing import Dict, Any, Optional, Type
from enum import Enum

from .base_scraper import BaseScraper
from .instagram_scraper import InstagramScraper
from .tiktok_scraper import TikTokScraper
from .youtube_scraper import YouTubeScraper
from .twitter_scraper import TwitterScraper
from .facebook_scraper import FacebookScraper


class SupportedPlatform(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class ScraperFactory:
    """Factory for creating platform-specific scrapers."""
    
    _scrapers: Dict[str, Type[BaseScraper]] = {
        SupportedPlatform.INSTAGRAM: InstagramScraper,
        SupportedPlatform.TIKTOK: TikTokScraper,
        SupportedPlatform.YOUTUBE: YouTubeScraper,
        SupportedPlatform.TWITTER: TwitterScraper,
        SupportedPlatform.FACEBOOK: FacebookScraper,
    }
    
    @classmethod
    def create_scraper(cls, platform: str, api_config: Dict[str, Any]) -> BaseScraper:
        """Create a scraper for the specified platform."""
        platform = platform.lower()
        
        if platform not in cls._scrapers:
            raise ValueError(f"Unsupported platform: {platform}. Supported platforms: {list(cls._scrapers.keys())}")
        
        scraper_class = cls._scrapers[platform]
        return scraper_class(api_config)
    
    @classmethod
    def get_supported_platforms(cls) -> list:
        """Get list of supported platforms."""
        return list(cls._scrapers.keys())
    
    @classmethod
    def is_platform_supported(cls, platform: str) -> bool:
        """Check if a platform is supported."""
        return platform.lower() in cls._scrapers
    
    @classmethod
    def register_scraper(cls, platform: str, scraper_class: Type[BaseScraper]) -> None:
        """Register a new scraper for a platform."""
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError("Scraper class must inherit from BaseScraper")
        
        cls._scrapers[platform.lower()] = scraper_class
    
    @classmethod
    def get_platform_requirements(cls, platform: str) -> Dict[str, Any]:
        """Get API configuration requirements for a platform."""
        requirements = {
            SupportedPlatform.INSTAGRAM: {
                'required_fields': ['app_id', 'app_secret', 'access_token'],
                'optional_fields': ['redirect_uri'],
                'rate_limits': {'requests_per_hour': 200},
                'documentation': 'https://developers.facebook.com/docs/instagram-basic-display-api',
                'notes': [
                    'Requires Instagram Basic Display API app',
                    'Access token must be obtained through OAuth flow',
                    'Limited to user\'s own content'
                ]
            },
            SupportedPlatform.TIKTOK: {
                'required_fields': ['app_id', 'app_secret', 'access_token'],
                'optional_fields': ['refresh_token'],
                'rate_limits': {'requests_per_hour': 100},
                'documentation': 'https://developers.tiktok.com/doc/login-kit-web',
                'notes': [
                    'Requires TikTok for Developers app',
                    'Access token must be obtained through OAuth flow',
                    'Business account recommended for higher limits'
                ]
            },
            SupportedPlatform.YOUTUBE: {
                'required_fields': ['api_key', 'client_id', 'client_secret'],
                'optional_fields': ['access_token', 'refresh_token'],
                'rate_limits': {'requests_per_day': 10000},
                'documentation': 'https://developers.google.com/youtube/v3',
                'notes': [
                    'Requires Google Cloud Console project',
                    'YouTube Data API v3 must be enabled',
                    'OAuth required for private data'
                ]
            },
            SupportedPlatform.TWITTER: {
                'required_fields': ['api_key', 'api_secret', 'access_token', 'access_token_secret'],
                'optional_fields': ['bearer_token'],
                'rate_limits': {'requests_per_15min': 300},
                'documentation': 'https://developer.twitter.com/en/docs/twitter-api',
                'notes': [
                    'Requires Twitter Developer account',
                    'API v2 recommended',
                    'Rate limits vary by endpoint'
                ]
            },
            SupportedPlatform.FACEBOOK: {
                'required_fields': ['app_id', 'app_secret', 'access_token'],
                'optional_fields': ['page_access_token'],
                'rate_limits': {'requests_per_hour': 200},
                'documentation': 'https://developers.facebook.com/docs/graph-api',
                'notes': [
                    'Requires Facebook App',
                    'Page access token needed for page data',
                    'Business verification may be required'
                ]
            }
        }
        
        platform = platform.lower()
        if platform not in requirements:
            raise ValueError(f"No requirements defined for platform: {platform}")
        
        return requirements[platform]


class ScraperManager:
    """Manager for handling multiple scrapers and their configurations."""
    
    def __init__(self, platform_configs: Dict[str, Dict[str, Any]]):
        """Initialize scraper manager with platform configurations."""
        self.platform_configs = platform_configs
        self._scrapers: Dict[str, BaseScraper] = {}
        self._initialize_scrapers()
    
    def _initialize_scrapers(self) -> None:
        """Initialize scrapers for all configured platforms."""
        for platform, config in self.platform_configs.items():
            try:
                if ScraperFactory.is_platform_supported(platform):
                    scraper = ScraperFactory.create_scraper(platform, config)
                    self._scrapers[platform] = scraper
                else:
                    print(f"Warning: Platform {platform} is not supported yet")
            except Exception as e:
                print(f"Error initializing {platform} scraper: {e}")
    
    def get_scraper(self, platform: str) -> Optional[BaseScraper]:
        """Get scraper for a specific platform."""
        return self._scrapers.get(platform.lower())
    
    def get_available_platforms(self) -> list:
        """Get list of available (configured and working) platforms."""
        return list(self._scrapers.keys())
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all scrapers."""
        results = {}
        
        for platform, scraper in self._scrapers.items():
            try:
                results[platform] = await scraper.health_check()
            except Exception as e:
                print(f"Health check failed for {platform}: {e}")
                results[platform] = False
        
        return results
    
    def get_rate_limit_status_all(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limit status for all scrapers."""
        status = {}
        
        for platform, scraper in self._scrapers.items():
            try:
                status[platform] = scraper.get_rate_limit_status()
            except Exception as e:
                status[platform] = {'error': str(e)}
        
        return status
    
    def add_platform(self, platform: str, config: Dict[str, Any]) -> bool:
        """Add a new platform configuration."""
        try:
            if ScraperFactory.is_platform_supported(platform):
                scraper = ScraperFactory.create_scraper(platform, config)
                self._scrapers[platform] = scraper
                self.platform_configs[platform] = config
                return True
            else:
                print(f"Platform {platform} is not supported")
                return False
        except Exception as e:
            print(f"Error adding {platform} scraper: {e}")
            return False
    
    def remove_platform(self, platform: str) -> bool:
        """Remove a platform configuration."""
        platform = platform.lower()
        
        if platform in self._scrapers:
            del self._scrapers[platform]
        
        if platform in self.platform_configs:
            del self.platform_configs[platform]
        
        return True
    
    def update_platform_config(self, platform: str, config: Dict[str, Any]) -> bool:
        """Update configuration for an existing platform."""
        try:
            if platform.lower() in self._scrapers:
                # Remove old scraper
                del self._scrapers[platform.lower()]
            
            # Create new scraper with updated config
            scraper = ScraperFactory.create_scraper(platform, config)
            self._scrapers[platform.lower()] = scraper
            self.platform_configs[platform.lower()] = config
            
            return True
        except Exception as e:
            print(f"Error updating {platform} scraper config: {e}")
            return False