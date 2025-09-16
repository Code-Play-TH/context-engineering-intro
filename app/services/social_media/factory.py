"""
Social Media Service Factory for managing platform-specific API integrations.
Provides centralized access to all social media services.
"""

import logging
from typing import Dict, List, Optional, Any, Type, Union
from enum import Enum

from app.services.social_media.base import BaseSocialMediaService
from app.services.social_media.instagram import InstagramService
from app.services.social_media.youtube import YouTubeService
from app.services.social_media.tiktok import TikTokService
from app.services.social_media.twitter import TwitterService
from app.services.social_media.facebook import FacebookService

logger = logging.getLogger(__name__)


class SupportedPlatform(Enum):
    """Enumeration of supported social media platforms."""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class SocialMediaServiceFactory:
    """
    Factory class for creating and managing social media API services.

    Features:
    - Platform-specific service creation
    - Service caching and reuse
    - Unified interface for all platforms
    - Error handling and fallbacks
    """

    def __init__(self):
        self._services: Dict[str, BaseSocialMediaService] = {}
        self._service_classes: Dict[str, Type[BaseSocialMediaService]] = {
            SupportedPlatform.INSTAGRAM.value: InstagramService,
            SupportedPlatform.YOUTUBE.value: YouTubeService,
            SupportedPlatform.TIKTOK.value: TikTokService,
            SupportedPlatform.TWITTER.value: TwitterService,
            SupportedPlatform.FACEBOOK.value: FacebookService,
        }

    def get_service(self, platform: Union[str, SupportedPlatform]) -> BaseSocialMediaService:
        """
        Get service instance for specified platform.

        Args:
            platform: Platform name or enum

        Returns:
            Platform-specific service instance

        Raises:
            ValueError: If platform is not supported
        """
        if isinstance(platform, SupportedPlatform):
            platform_name = platform.value
        else:
            platform_name = platform.lower()

        if platform_name not in self._service_classes:
            raise ValueError(f"Unsupported platform: {platform_name}")

        # Return cached service or create new one
        if platform_name not in self._services:
            service_class = self._service_classes[platform_name]
            self._services[platform_name] = service_class()

        return self._services[platform_name]

    async def get_all_user_profiles(
        self,
        user_handles: Dict[str, str],
        access_tokens: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Get user profiles from all specified platforms.

        Args:
            user_handles: Dict of platform -> user_id/handle
            access_tokens: Dict of platform -> access_token

        Returns:
            Dict of platform -> profile data
        """
        if access_tokens is None:
            access_tokens = {}

        profiles = {}

        for platform, user_handle in user_handles.items():
            try:
                service = self.get_service(platform)
                access_token = access_tokens.get(platform)

                async with service:
                    profile = await service.get_user_profile(user_handle, access_token)
                    profiles[platform] = {
                        "success": True,
                        "data": profile
                    }

            except Exception as e:
                logger.error(f"Failed to get profile for {platform}/{user_handle}: {str(e)}")
                profiles[platform] = {
                    "success": False,
                    "error": str(e)
                }

        return profiles

    async def get_all_user_media(
        self,
        user_handles: Dict[str, str],
        access_tokens: Dict[str, str] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Get recent media from all specified platforms.

        Args:
            user_handles: Dict of platform -> user_id/handle
            access_tokens: Dict of platform -> access_token
            limit: Number of media items per platform

        Returns:
            Dict of platform -> media data
        """
        if access_tokens is None:
            access_tokens = {}

        media_data = {}

        for platform, user_handle in user_handles.items():
            try:
                service = self.get_service(platform)
                access_token = access_tokens.get(platform)

                async with service:
                    media = await service.get_user_media(user_handle, access_token, limit)
                    media_data[platform] = {
                        "success": True,
                        "data": media
                    }

            except Exception as e:
                logger.error(f"Failed to get media for {platform}/{user_handle}: {str(e)}")
                media_data[platform] = {
                    "success": False,
                    "error": str(e)
                }

        return media_data

    async def search_content_across_platforms(
        self,
        search_criteria: Dict[str, Any],
        platforms: List[str] = None,
        access_tokens: Dict[str, str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for content across multiple platforms.

        Args:
            search_criteria: Search parameters (hashtags, keywords, etc.)
            platforms: List of platforms to search (default: all)
            access_tokens: Platform access tokens

        Returns:
            Dict of platform -> list of content
        """
        if platforms is None:
            platforms = list(self._service_classes.keys())

        if access_tokens is None:
            access_tokens = {}

        results = {}

        for platform in platforms:
            try:
                service = self.get_service(platform)
                access_token = access_tokens.get(platform)

                async with service:
                    content = await self._search_platform_content(
                        service, search_criteria, access_token
                    )
                    results[platform] = content

            except Exception as e:
                logger.error(f"Failed to search content on {platform}: {str(e)}")
                results[platform] = []

        return results

    async def verify_content_matches(
        self,
        content_data: Dict[str, Dict[str, Any]],
        campaign_criteria: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Verify content matches across all platforms.

        Args:
            content_data: Dict of platform -> content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Dict of platform -> verification results
        """
        verification_results = {}

        for platform, content in content_data.items():
            try:
                service = self.get_service(platform)

                async with service:
                    is_match, confidence, criteria = await service.verify_content_match(
                        content, campaign_criteria
                    )

                    verification_results[platform] = {
                        "is_match": is_match,
                        "confidence_score": confidence,
                        "match_criteria": criteria,
                        "success": True
                    }

            except Exception as e:
                logger.error(f"Failed to verify content for {platform}: {str(e)}")
                verification_results[platform] = {
                    "is_match": False,
                    "confidence_score": 0.0,
                    "match_criteria": [],
                    "success": False,
                    "error": str(e)
                }

        return verification_results

    async def get_platform_analytics(
        self,
        platform_data: Dict[str, Dict[str, Any]],
        access_tokens: Dict[str, str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get analytics data from multiple platforms.

        Args:
            platform_data: Dict of platform -> request parameters
            access_tokens: Platform access tokens

        Returns:
            Dict of platform -> analytics data
        """
        if access_tokens is None:
            access_tokens = {}

        analytics = {}

        for platform, data in platform_data.items():
            try:
                service = self.get_service(platform)
                access_token = access_tokens.get(platform)

                async with service:
                    # Platform-specific analytics logic
                    platform_analytics = await self._get_platform_specific_analytics(
                        service, data, access_token
                    )
                    analytics[platform] = {
                        "success": True,
                        "data": platform_analytics
                    }

            except Exception as e:
                logger.error(f"Failed to get analytics for {platform}: {str(e)}")
                analytics[platform] = {
                    "success": False,
                    "error": str(e)
                }

        return analytics

    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platform names."""
        return list(self._service_classes.keys())

    def is_platform_supported(self, platform: str) -> bool:
        """Check if platform is supported."""
        return platform.lower() in self._service_classes

    async def validate_access_tokens(
        self,
        access_tokens: Dict[str, str]
    ) -> Dict[str, bool]:
        """
        Validate access tokens for multiple platforms.

        Args:
            access_tokens: Dict of platform -> access_token

        Returns:
            Dict of platform -> is_valid
        """
        validation_results = {}

        for platform, token in access_tokens.items():
            try:
                service = self.get_service(platform)

                async with service:
                    # Try to make a simple API call to validate token
                    await service.get_user_profile("me", token)
                    validation_results[platform] = True

            except Exception as e:
                logger.warning(f"Invalid token for {platform}: {str(e)}")
                validation_results[platform] = False

        return validation_results

    def get_platform_capabilities(self, platform: str) -> Dict[str, bool]:
        """
        Get capabilities of a specific platform service.

        Args:
            platform: Platform name

        Returns:
            Dict of capability -> is_supported
        """
        try:
            service = self.get_service(platform)

            # Check which methods are implemented
            capabilities = {
                "user_profiles": hasattr(service, 'get_user_profile'),
                "user_media": hasattr(service, 'get_user_media'),
                "content_search": hasattr(service, 'search_videos') or hasattr(service, 'search_tweets'),
                "analytics": hasattr(service, 'get_video_analytics') or hasattr(service, 'get_account_insights'),
                "content_verification": hasattr(service, 'verify_content_match'),
                "real_time_data": platform in ['twitter', 'instagram'],
                "historical_data": platform in ['youtube', 'facebook'],
                "hashtag_search": platform in ['instagram', 'tiktok', 'twitter'],
                "demographics": platform in ['youtube', 'facebook', 'tiktok']
            }

            return capabilities

        except ValueError:
            return {}

    # Private helper methods

    async def _search_platform_content(
        self,
        service: BaseSocialMediaService,
        criteria: Dict[str, Any],
        access_token: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search for content on a specific platform."""
        platform = service.get_platform_name()
        hashtags = criteria.get("hashtags", [])
        keywords = criteria.get("keywords", [])

        all_content = []

        # Search by hashtags
        for hashtag in hashtags:
            try:
                if platform == "instagram":
                    content = await service.search_hashtag_media(hashtag, access_token)
                elif platform == "youtube":
                    content = await service.search_videos(f"#{hashtag}")
                elif platform == "tiktok":
                    content = await service.search_videos_by_hashtag(hashtag, access_token)
                elif platform == "twitter":
                    content = await service.search_tweets(f"#{hashtag}", access_token)
                elif platform == "facebook":
                    content = await service.search_posts_by_hashtag(hashtag, access_token)
                else:
                    content = []

                all_content.extend(content)

            except Exception as e:
                logger.warning(f"Hashtag search failed for {platform}#{hashtag}: {str(e)}")

        # Search by keywords
        for keyword in keywords:
            try:
                if platform == "youtube":
                    content = await service.search_videos(keyword)
                elif platform == "twitter":
                    content = await service.search_tweets(keyword, access_token)
                # Other platforms may not support keyword search

                all_content.extend(content)

            except Exception as e:
                logger.warning(f"Keyword search failed for {platform}/{keyword}: {str(e)}")

        return all_content

    async def _get_platform_specific_analytics(
        self,
        service: BaseSocialMediaService,
        data: Dict[str, Any],
        access_token: Optional[str]
    ) -> Dict[str, Any]:
        """Get analytics data for a specific platform."""
        platform = service.get_platform_name()
        analytics = {}

        try:
            if platform == "youtube" and hasattr(service, 'get_video_analytics'):
                video_id = data.get("video_id")
                if video_id:
                    analytics = await service.get_video_analytics(video_id, access_token)

            elif platform == "instagram" and hasattr(service, 'get_account_insights'):
                user_id = data.get("user_id")
                if user_id:
                    analytics = await service.get_account_insights(user_id, access_token)

            elif platform == "facebook" and hasattr(service, 'get_page_insights'):
                page_id = data.get("page_id")
                if page_id:
                    analytics = await service.get_page_insights(page_id, access_token)

            elif platform == "tiktok" and hasattr(service, 'get_user_followers_insights'):
                analytics = await service.get_user_followers_insights(access_token)

        except Exception as e:
            logger.error(f"Failed to get {platform} analytics: {str(e)}")

        return analytics


# Global factory instance
social_media_factory = SocialMediaServiceFactory()