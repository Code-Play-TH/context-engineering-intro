"""
Social Media Services Package

Provides comprehensive API integrations for major social media platforms:
- Instagram Graph API v18.0
- YouTube Data API v3
- TikTok for Developers API v2
- Twitter API v2
- Facebook Graph API v18.0

Features:
- Unified interface across all platforms
- Comprehensive data collection and monitoring
- Content verification and matching
- Performance analytics and insights
- Rate limiting and error handling
"""

from app.services.social_media.base import BaseSocialMediaService
from app.services.social_media.instagram import InstagramService
from app.services.social_media.youtube import YouTubeService
from app.services.social_media.tiktok import TikTokService
from app.services.social_media.twitter import TwitterService
from app.services.social_media.facebook import FacebookService
from app.services.social_media.factory import (
    SocialMediaServiceFactory,
    SupportedPlatform,
    social_media_factory
)

# Export all classes and the factory instance
__all__ = [
    # Base class
    "BaseSocialMediaService",

    # Platform-specific services
    "InstagramService",
    "YouTubeService",
    "TikTokService",
    "TwitterService",
    "FacebookService",

    # Factory and utilities
    "SocialMediaServiceFactory",
    "SupportedPlatform",
    "social_media_factory",
]

# Convenience functions for common operations
async def get_kol_profile_data(
    platform: str,
    user_id: str,
    access_token: str = None
) -> dict:
    """
    Get KOL profile data from specified platform.

    Args:
        platform: Social media platform name
        user_id: Platform-specific user ID or handle
        access_token: Optional access token

    Returns:
        Standardized profile data dictionary

    Example:
        profile = await get_kol_profile_data("instagram", "username", token)
    """
    service = social_media_factory.get_service(platform)
    async with service:
        return await service.get_user_profile(user_id, access_token)


async def get_kol_recent_content(
    platform: str,
    user_id: str,
    access_token: str = None,
    limit: int = 25
) -> dict:
    """
    Get recent content from KOL on specified platform.

    Args:
        platform: Social media platform name
        user_id: Platform-specific user ID or handle
        access_token: Optional access token
        limit: Number of content items to retrieve

    Returns:
        Content data with pagination info

    Example:
        content = await get_kol_recent_content("youtube", "channel_id", token, 10)
    """
    service = social_media_factory.get_service(platform)
    async with service:
        return await service.get_user_media(user_id, access_token, limit)


async def verify_campaign_content(
    platform: str,
    content_data: dict,
    campaign_criteria: dict
) -> tuple:
    """
    Verify if content matches campaign criteria.

    Args:
        platform: Social media platform name
        content_data: Content data from platform
        campaign_criteria: Campaign matching criteria

    Returns:
        Tuple of (is_match, confidence_score, match_criteria)

    Example:
        is_match, score, criteria = await verify_campaign_content(
            "tiktok", video_data, campaign_rules
        )
    """
    service = social_media_factory.get_service(platform)
    async with service:
        return await service.verify_content_match(content_data, campaign_criteria)


async def search_content_by_hashtag(
    platform: str,
    hashtag: str,
    access_token: str = None,
    limit: int = 25
) -> list:
    """
    Search for content by hashtag on specified platform.

    Args:
        platform: Social media platform name
        hashtag: Hashtag to search (without #)
        access_token: Optional access token
        limit: Number of results to return

    Returns:
        List of content data

    Example:
        posts = await search_content_by_hashtag("twitter", "marketing", token)
    """
    service = social_media_factory.get_service(platform)
    async with service:
        if platform == "instagram":
            return await service.search_hashtag_media(hashtag, access_token, limit)
        elif platform == "youtube":
            return await service.search_videos(f"#{hashtag}", limit)
        elif platform == "tiktok":
            return await service.search_videos_by_hashtag(hashtag, access_token, limit)
        elif platform == "twitter":
            return await service.search_tweets(f"#{hashtag}", access_token, limit)
        elif platform == "facebook":
            return await service.search_posts_by_hashtag(hashtag, access_token, limit)
        else:
            raise ValueError(f"Hashtag search not supported for {platform}")


def get_supported_platforms() -> list:
    """
    Get list of supported social media platforms.

    Returns:
        List of platform names

    Example:
        platforms = get_supported_platforms()
        # Returns: ['instagram', 'youtube', 'tiktok', 'twitter', 'facebook']
    """
    return social_media_factory.get_supported_platforms()


def get_platform_capabilities(platform: str) -> dict:
    """
    Get capabilities of a specific platform.

    Args:
        platform: Platform name

    Returns:
        Dict of capability -> is_supported

    Example:
        caps = get_platform_capabilities("instagram")
        # Returns: {'user_profiles': True, 'hashtag_search': True, ...}
    """
    return social_media_factory.get_platform_capabilities(platform)


# Platform-specific configuration and limits
PLATFORM_LIMITS = {
    "instagram": {
        "max_posts_per_request": 25,
        "rate_limit_per_hour": 200,
        "max_hashtag_search": 25,
        "analytics_retention_days": 30
    },
    "youtube": {
        "max_videos_per_request": 50,
        "rate_limit_quota_per_day": 10000,
        "max_search_results": 50,
        "analytics_retention_days": 60
    },
    "tiktok": {
        "max_videos_per_request": 20,
        "rate_limit_per_hour": 100,
        "max_hashtag_search": 20,
        "analytics_retention_days": 7
    },
    "twitter": {
        "max_tweets_per_request": 100,
        "rate_limit_per_15_min": 300,
        "max_search_results": 100,
        "analytics_retention_days": 90
    },
    "facebook": {
        "max_posts_per_request": 100,
        "rate_limit_per_hour": 200,
        "max_hashtag_search": 25,
        "analytics_retention_days": 90
    }
}


def get_platform_limits(platform: str) -> dict:
    """
    Get rate limits and constraints for a platform.

    Args:
        platform: Platform name

    Returns:
        Dict of limits and constraints

    Example:
        limits = get_platform_limits("instagram")
        # Returns: {'max_posts_per_request': 25, 'rate_limit_per_hour': 200, ...}
    """
    return PLATFORM_LIMITS.get(platform.lower(), {})