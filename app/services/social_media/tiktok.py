"""
TikTok API service for KOL data collection and content monitoring.
Implements TikTok for Developers API for influencer management.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode
import hashlib
import hmac
import json

from app.core.config import get_settings
from app.services.social_media.base import BaseSocialMediaService
from app.models.content import ContentType, VerificationStatus

logger = logging.getLogger(__name__)


class TikTokService(BaseSocialMediaService):
    """
    TikTok API service for KOL management and content monitoring.

    Features:
    - User profile data collection
    - Video discovery and monitoring
    - Performance metrics tracking
    - Content verification
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.platform = "tiktok"
        self.api_base_url = "https://open-api.tiktok.com"

        # Rate limiting (varies by endpoint)
        self.rate_limit_calls = 100
        self.rate_limit_window = 3600  # 1 hour

        # Initialize session
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "KOL-Management-System/1.0",
                "Content-Type": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_user_profile(self, user_id: str, access_token: str) -> Dict[str, Any]:
        """
        Get TikTok user profile information.

        Args:
            user_id: TikTok user ID or open_id
            access_token: User access token

        Returns:
            Dict containing user profile data
        """
        await self._check_rate_limit(access_token)

        fields = [
            "open_id", "display_name", "bio_description", "avatar_url",
            "follower_count", "following_count", "likes_count", "video_count"
        ]

        params = {
            "fields": ",".join(fields)
        }

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        url = f"{self.api_base_url}/v2/user/info/"

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data"):
                        return self._transform_profile_data(data["data"])
                    else:
                        raise ValueError(f"User not found: {user_id}")
                elif response.status == 429:
                    raise ValueError("Rate limit exceeded")
                else:
                    error_data = await response.json()
                    raise ValueError(f"TikTok API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"TikTok API request failed: {str(e)}")
            raise

    async def get_user_media(
        self,
        user_id: str,
        access_token: str,
        limit: int = 20,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's videos with pagination.

        Args:
            user_id: TikTok user ID or open_id
            access_token: User access token
            limit: Number of videos to retrieve (max 20)
            after: Cursor for pagination

        Returns:
            Dict containing video data and pagination info
        """
        await self._check_rate_limit(access_token)

        fields = [
            "id", "title", "video_description", "duration", "cover_image_url",
            "share_url", "view_count", "like_count", "comment_count", "share_count",
            "create_time"
        ]

        params = {
            "fields": ",".join(fields),
            "max_count": min(limit, 20)  # API max is 20
        }

        if after:
            params["cursor"] = after

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        url = f"{self.api_base_url}/v2/video/list/"

        try:
            async with self.session.post(url, json=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_videos_data(data)
                else:
                    error_data = await response.json()
                    raise ValueError(f"TikTok API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"TikTok videos request failed: {str(e)}")
            raise

    async def get_video_details(self, video_id: str, access_token: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific video.

        Args:
            video_id: TikTok video ID
            access_token: User access token

        Returns:
            Dict containing video details
        """
        await self._check_rate_limit(access_token)

        fields = [
            "id", "title", "video_description", "duration", "cover_image_url",
            "embed_html", "embed_link", "share_url", "view_count", "like_count",
            "comment_count", "share_count", "create_time"
        ]

        params = {
            "fields": ",".join(fields),
            "video_ids": [video_id]
        }

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        url = f"{self.api_base_url}/v2/video/query/"

        try:
            async with self.session.post(url, json=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = data.get("data", {}).get("videos", [])
                    if videos:
                        return self._transform_video_data(videos[0])
                    else:
                        raise ValueError(f"Video not found: {video_id}")
                else:
                    error_data = await response.json()
                    raise ValueError(f"TikTok API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"TikTok video request failed: {str(e)}")
            raise

    async def search_videos_by_hashtag(
        self,
        hashtag: str,
        access_token: str,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for videos by hashtag.

        Args:
            hashtag: Hashtag to search (without #)
            access_token: App access token
            limit: Number of videos to retrieve
            cursor: Pagination cursor

        Returns:
            List of video data
        """
        await self._check_rate_limit(access_token)

        # Note: Hashtag search may require special permissions
        fields = [
            "id", "title", "video_description", "duration", "cover_image_url",
            "share_url", "view_count", "like_count", "comment_count",
            "share_count", "create_time"
        ]

        params = {
            "fields": ",".join(fields),
            "hashtag_name": hashtag,
            "max_count": min(limit, 20)
        }

        if cursor:
            params["cursor"] = cursor

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        url = f"{self.api_base_url}/v2/research/video/query/"

        try:
            async with self.session.post(url, json=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = data.get("data", {}).get("videos", [])
                    return [self._transform_video_data(video) for video in videos]
                else:
                    logger.warning(f"TikTok hashtag search failed for #{hashtag}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"TikTok hashtag search failed: {str(e)}")
            return []

    async def verify_content_match(
        self,
        content_data: Dict[str, Any],
        campaign_criteria: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verify if content matches campaign criteria.

        Args:
            content_data: TikTok content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Tuple of (is_match, confidence_score, match_criteria)
        """
        match_criteria = []
        confidence_scores = []

        title = content_data.get("title", "").lower()
        description = content_data.get("description", "").lower()
        combined_text = f"{title} {description}".lower()

        # Check required hashtags
        required_hashtags = campaign_criteria.get("required_hashtags", [])
        if required_hashtags:
            hashtag_matches = sum(1 for tag in required_hashtags if f"#{tag.lower()}" in combined_text)
            if hashtag_matches > 0:
                match_criteria.append("hashtag_match")
                confidence_scores.append(hashtag_matches / len(required_hashtags))

        # Check keywords
        keywords = campaign_criteria.get("keywords", [])
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in combined_text)
            if keyword_matches > 0:
                match_criteria.append("keyword_match")
                confidence_scores.append(keyword_matches / len(keywords))

        # Check video duration requirements
        min_duration = campaign_criteria.get("min_duration_seconds", 0)
        max_duration = campaign_criteria.get("max_duration_seconds", float('inf'))
        video_duration = content_data.get("duration", 0)

        if min_duration <= video_duration <= max_duration:
            match_criteria.append("duration_match")
            confidence_scores.append(1.0)

        # Check posting timeframe
        created_time = content_data.get("create_time")
        if created_time:
            posted_at = datetime.fromtimestamp(created_time)
            campaign_start = campaign_criteria.get("start_date")
            campaign_end = campaign_criteria.get("end_date")

            if campaign_start and campaign_end:
                if campaign_start <= posted_at <= campaign_end:
                    match_criteria.append("timeframe_match")
                    confidence_scores.append(1.0)

        # Check minimum engagement requirements
        min_views = campaign_criteria.get("min_views", 0)
        min_likes = campaign_criteria.get("min_likes", 0)

        if (content_data.get("view_count", 0) >= min_views and
            content_data.get("like_count", 0) >= min_likes):
            match_criteria.append("engagement_match")
            confidence_scores.append(1.0)

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_match = overall_confidence > 0.5 and len(match_criteria) > 0

        return is_match, overall_confidence, match_criteria

    async def get_user_followers_insights(
        self,
        access_token: str,
        date_range: int = 7
    ) -> Dict[str, Any]:
        """
        Get user's follower insights and demographics.

        Args:
            access_token: User access token
            date_range: Number of days for insights (7, 28, or 60)

        Returns:
            Dict containing follower insights
        """
        await self._check_rate_limit(access_token)

        params = {
            "date_range": date_range
        }

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        url = f"{self.api_base_url}/v2/user/insights/"

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_insights_data(data.get("data", {}))
                else:
                    error_data = await response.json()
                    logger.warning(f"TikTok insights error: {error_data}")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"TikTok insights request failed: {str(e)}")
            return {}

    # Private helper methods

    def _transform_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform TikTok profile data to standard format."""
        user_data = data.get("user", data)

        return {
            "platform_user_id": user_data.get("open_id"),
            "username": user_data.get("unique_id", ""),
            "display_name": user_data.get("display_name"),
            "bio": user_data.get("bio_description"),
            "profile_picture_url": user_data.get("avatar_url"),
            "follower_count": user_data.get("follower_count", 0),
            "following_count": user_data.get("following_count", 0),
            "video_count": user_data.get("video_count", 0),
            "total_likes": user_data.get("likes_count", 0),
            "verified": user_data.get("is_verified", False),
            "updated_at": datetime.utcnow().isoformat()
        }

    def _transform_videos_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform TikTok videos data to standard format."""
        video_items = []
        videos = data.get("data", {}).get("videos", [])

        for video in videos:
            video_items.append(self._transform_video_data(video))

        return {
            "data": video_items,
            "paging": {
                "cursor": data.get("data", {}).get("cursor"),
                "has_more": data.get("data", {}).get("has_more", False)
            },
            "total_count": len(video_items)
        }

    def _transform_video_data(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Transform single TikTok video data to standard format."""
        return {
            "platform_post_id": video.get("id"),
            "content_type": ContentType.VIDEO,
            "title": video.get("title", ""),
            "content": video.get("video_description", ""),
            "thumbnail_url": video.get("cover_image_url"),
            "permalink": video.get("share_url"),
            "posted_at": datetime.fromtimestamp(video.get("create_time", 0)).isoformat() if video.get("create_time") else None,
            "view_count": video.get("view_count", 0),
            "like_count": video.get("like_count", 0),
            "comment_count": video.get("comment_count", 0),
            "share_count": video.get("share_count", 0),
            "duration": video.get("duration", 0),
            "embed_html": video.get("embed_html"),
            "embed_link": video.get("embed_link")
        }

    def _transform_insights_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform TikTok insights data to standard format."""
        insights = {}

        # Profile views
        profile_views = data.get("profile_views", {})
        if profile_views:
            insights["profile_views"] = profile_views.get("value", 0)

        # Follower demographics
        demographics = data.get("followers", {})
        if demographics:
            insights["follower_demographics"] = {
                "gender": demographics.get("gender", {}),
                "age": demographics.get("age", {}),
                "territory": demographics.get("territory", {})
            }

        # Video views
        video_views = data.get("video_views", {})
        if video_views:
            insights["video_views"] = video_views.get("value", 0)

        return insights

    def _generate_signature(self, params: Dict[str, Any], app_secret: str) -> str:
        """Generate signature for TikTok API requests."""
        # Sort parameters
        sorted_params = sorted(params.items())

        # Create query string
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            app_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _check_rate_limit(self, access_token: str) -> None:
        """Check and enforce rate limiting."""
        # TikTok has different rate limits per endpoint
        # Implement proper rate limiting based on endpoint
        await asyncio.sleep(0.1)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.platform

    def get_api_version(self) -> str:
        """Get API version."""
        return "v2"