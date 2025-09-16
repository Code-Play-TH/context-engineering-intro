"""
Instagram Graph API service for KOL data collection and content monitoring.
Implements Instagram Graph API v18.0 for comprehensive influencer analytics.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode

from app.core.config import get_settings
from app.services.social_media.base import BaseSocialMediaService
from app.models.content import ContentType, VerificationStatus

logger = logging.getLogger(__name__)


class InstagramService(BaseSocialMediaService):
    """
    Instagram Graph API service for KOL management and content monitoring.

    Features:
    - KOL profile data collection
    - Content discovery and monitoring
    - Performance metrics tracking
    - Automated content verification
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.platform = "instagram"
        self.api_base_url = "https://graph.instagram.com"
        self.graph_base_url = "https://graph.facebook.com/v18.0"

        # Rate limiting (200 calls per hour per user)
        self.rate_limit_calls = 200
        self.rate_limit_window = 3600  # 1 hour

        # Initialize session
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "KOL-Management-System/1.0",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_user_profile(self, user_id: str, access_token: str) -> Dict[str, Any]:
        """
        Get Instagram user profile information.

        Args:
            user_id: Instagram user ID
            access_token: User access token

        Returns:
            Dict containing user profile data

        Raises:
            ValueError: If API response is invalid
            aiohttp.ClientError: If API request fails
        """
        await self._check_rate_limit(access_token)

        fields = [
            "id", "username", "name", "biography", "profile_picture_url",
            "followers_count", "follows_count", "media_count", "website"
        ]

        params = {
            "fields": ",".join(fields),
            "access_token": access_token
        }

        url = f"{self.graph_base_url}/{user_id}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_profile_data(data)
                elif response.status == 429:
                    # Rate limit exceeded
                    retry_after = int(response.headers.get("Retry-After", 3600))
                    raise ValueError(f"Rate limit exceeded. Retry after {retry_after} seconds")
                else:
                    error_data = await response.json()
                    raise ValueError(f"Instagram API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"Instagram API request failed: {str(e)}")
            raise

    async def get_user_media(
        self,
        user_id: str,
        access_token: str,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's media posts with pagination.

        Args:
            user_id: Instagram user ID
            access_token: User access token
            limit: Number of posts to retrieve (max 25)
            after: Pagination cursor

        Returns:
            Dict containing media data and pagination info
        """
        await self._check_rate_limit(access_token)

        fields = [
            "id", "media_type", "media_url", "thumbnail_url", "permalink",
            "caption", "timestamp", "like_count", "comments_count", "shares"
        ]

        params = {
            "fields": ",".join(fields),
            "limit": min(limit, 25),  # API max is 25
            "access_token": access_token
        }

        if after:
            params["after"] = after

        url = f"{self.graph_base_url}/{user_id}/media"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_media_data(data)
                else:
                    error_data = await response.json()
                    raise ValueError(f"Instagram API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"Instagram media request failed: {str(e)}")
            raise

    async def get_media_insights(
        self,
        media_id: str,
        access_token: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get insights for a specific media post.

        Args:
            media_id: Instagram media ID
            access_token: User access token
            metrics: List of metrics to retrieve

        Returns:
            Dict containing media insights
        """
        await self._check_rate_limit(access_token)

        if not metrics:
            metrics = [
                "impressions", "reach", "likes", "comments", "shares", "saves",
                "profile_visits", "follows", "video_views", "video_plays"
            ]

        params = {
            "metric": ",".join(metrics),
            "access_token": access_token
        }

        url = f"{self.graph_base_url}/{media_id}/insights"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_insights_data(data)
                else:
                    error_data = await response.json()
                    logger.warning(f"Instagram insights error for {media_id}: {error_data}")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"Instagram insights request failed: {str(e)}")
            return {}

    async def search_hashtag_media(
        self,
        hashtag: str,
        access_token: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Search for media posts by hashtag.

        Args:
            hashtag: Hashtag to search (without #)
            access_token: App access token
            limit: Number of posts to retrieve

        Returns:
            List of media posts
        """
        await self._check_rate_limit(access_token)

        # First, get hashtag ID
        hashtag_id = await self._get_hashtag_id(hashtag, access_token)
        if not hashtag_id:
            return []

        fields = [
            "id", "media_type", "media_url", "permalink", "caption",
            "timestamp", "like_count", "comments_count", "owner"
        ]

        params = {
            "user_id": self.settings.INSTAGRAM_USER_ID,
            "fields": ",".join(fields),
            "limit": min(limit, 25),
            "access_token": access_token
        }

        url = f"{self.graph_base_url}/{hashtag_id}/recent_media"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.warning(f"Hashtag search failed for #{hashtag}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"Hashtag search request failed: {str(e)}")
            return []

    async def verify_content_match(
        self,
        content_data: Dict[str, Any],
        campaign_criteria: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verify if content matches campaign criteria.

        Args:
            content_data: Instagram content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Tuple of (is_match, confidence_score, match_criteria)
        """
        match_criteria = []
        confidence_scores = []

        caption = content_data.get("caption", "").lower()

        # Check required hashtags
        required_hashtags = campaign_criteria.get("required_hashtags", [])
        if required_hashtags:
            hashtag_matches = sum(1 for tag in required_hashtags if f"#{tag.lower()}" in caption)
            if hashtag_matches > 0:
                match_criteria.append("hashtag_match")
                confidence_scores.append(hashtag_matches / len(required_hashtags))

        # Check keywords
        keywords = campaign_criteria.get("keywords", [])
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in caption)
            if keyword_matches > 0:
                match_criteria.append("keyword_match")
                confidence_scores.append(keyword_matches / len(keywords))

        # Check mentions
        required_mentions = campaign_criteria.get("required_mentions", [])
        if required_mentions:
            mention_matches = sum(1 for mention in required_mentions if f"@{mention.lower()}" in caption)
            if mention_matches > 0:
                match_criteria.append("mention_match")
                confidence_scores.append(mention_matches / len(required_mentions))

        # Check posting timeframe
        posted_at = datetime.fromisoformat(content_data.get("timestamp", "").replace("Z", "+00:00"))
        campaign_start = campaign_criteria.get("start_date")
        campaign_end = campaign_criteria.get("end_date")

        if campaign_start and campaign_end:
            if campaign_start <= posted_at <= campaign_end:
                match_criteria.append("timeframe_match")
                confidence_scores.append(1.0)

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_match = overall_confidence > 0.5 and len(match_criteria) > 0

        return is_match, overall_confidence, match_criteria

    async def get_account_insights(
        self,
        user_id: str,
        access_token: str,
        period: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get account-level insights and analytics.

        Args:
            user_id: Instagram user ID
            access_token: User access token
            period: Insights period (day, week, days_28)
            since: Start date for insights
            until: End date for insights

        Returns:
            Dict containing account insights
        """
        await self._check_rate_limit(access_token)

        metrics = [
            "impressions", "reach", "profile_views", "website_clicks",
            "follower_count", "email_contacts", "phone_call_clicks",
            "text_message_clicks", "get_directions_clicks"
        ]

        params = {
            "metric": ",".join(metrics),
            "period": period,
            "access_token": access_token
        }

        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())

        url = f"{self.graph_base_url}/{user_id}/insights"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_account_insights(data)
                else:
                    error_data = await response.json()
                    logger.warning(f"Account insights error: {error_data}")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"Account insights request failed: {str(e)}")
            return {}

    # Private helper methods

    async def _get_hashtag_id(self, hashtag: str, access_token: str) -> Optional[str]:
        """Get hashtag ID for hashtag search."""
        params = {
            "q": hashtag,
            "access_token": access_token
        }

        url = f"{self.graph_base_url}/ig_hashtag_search"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    hashtags = data.get("data", [])
                    if hashtags:
                        return hashtags[0]["id"]
                return None

        except aiohttp.ClientError:
            return None

    def _transform_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Instagram profile data to standard format."""
        return {
            "platform_user_id": data.get("id"),
            "username": data.get("username"),
            "display_name": data.get("name"),
            "bio": data.get("biography"),
            "profile_picture_url": data.get("profile_picture_url"),
            "follower_count": data.get("followers_count", 0),
            "following_count": data.get("follows_count", 0),
            "media_count": data.get("media_count", 0),
            "website": data.get("website"),
            "verified": data.get("is_verified", False),
            "updated_at": datetime.utcnow().isoformat()
        }

    def _transform_media_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Instagram media data to standard format."""
        media_items = []

        for item in data.get("data", []):
            media_type = item.get("media_type", "").lower()
            content_type = ContentType.POST

            if media_type == "video":
                content_type = ContentType.VIDEO
            elif media_type == "carousel_album":
                content_type = ContentType.CAROUSEL

            media_items.append({
                "platform_post_id": item.get("id"),
                "content_type": content_type,
                "content": item.get("caption", ""),
                "media_url": item.get("media_url"),
                "thumbnail_url": item.get("thumbnail_url"),
                "permalink": item.get("permalink"),
                "posted_at": item.get("timestamp"),
                "like_count": item.get("like_count", 0),
                "comment_count": item.get("comments_count", 0),
                "share_count": item.get("shares", 0)
            })

        return {
            "data": media_items,
            "paging": data.get("paging", {}),
            "total_count": len(media_items)
        }

    def _transform_insights_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Instagram insights data to standard format."""
        insights = {}

        for metric_data in data.get("data", []):
            metric_name = metric_data.get("name")
            values = metric_data.get("values", [])

            if values:
                # Get the most recent value
                latest_value = values[-1].get("value", 0)
                insights[metric_name] = latest_value

        return insights

    def _transform_account_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform account insights data to standard format."""
        insights = {}

        for metric_data in data.get("data", []):
            metric_name = metric_data.get("name")
            values = metric_data.get("values", [])

            if values:
                total_value = sum(item.get("value", 0) for item in values)
                insights[metric_name] = total_value

        return insights

    async def _check_rate_limit(self, access_token: str) -> None:
        """Check and enforce rate limiting."""
        # Rate limiting logic would be implemented here
        # For now, we'll add a small delay to be respectful
        await asyncio.sleep(0.1)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.platform

    def get_api_version(self) -> str:
        """Get API version."""
        return "v18.0"