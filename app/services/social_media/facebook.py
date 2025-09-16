"""
Facebook Graph API service for KOL data collection and content monitoring.
Implements Facebook Graph API v18.0 for comprehensive page analytics.
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


class FacebookService(BaseSocialMediaService):
    """
    Facebook Graph API service for KOL management and content monitoring.

    Features:
    - Page profile data collection
    - Post discovery and monitoring
    - Performance metrics tracking
    - Page insights analytics
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.platform = "facebook"
        self.api_base_url = "https://graph.facebook.com/v18.0"

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
        Get Facebook page information.

        Args:
            user_id: Facebook page ID
            access_token: Page or user access token

        Returns:
            Dict containing page profile data
        """
        await self._check_rate_limit(access_token)

        fields = [
            "id", "name", "about", "description", "picture", "cover",
            "fan_count", "talking_about_count", "website", "username",
            "category", "verification_status", "location", "phone",
            "emails", "founded", "link", "is_verified"
        ]

        params = {
            "fields": ",".join(fields),
            "access_token": access_token
        }

        url = f"{self.api_base_url}/{user_id}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_profile_data(data)
                elif response.status == 400:
                    error_data = await response.json()
                    error = error_data.get("error", {})
                    if error.get("code") == 190:
                        raise ValueError("Invalid access token")
                    else:
                        raise ValueError(f"Facebook API error: {error.get('message', 'Unknown error')}")
                elif response.status == 429:
                    raise ValueError("Rate limit exceeded")
                else:
                    error_data = await response.json()
                    raise ValueError(f"Facebook API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"Facebook API request failed: {str(e)}")
            raise

    async def get_user_media(
        self,
        user_id: str,
        access_token: str,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get page's posts with pagination.

        Args:
            user_id: Facebook page ID
            access_token: Page or user access token
            limit: Number of posts to retrieve (max 100)
            after: Pagination cursor

        Returns:
            Dict containing post data and pagination info
        """
        await self._check_rate_limit(access_token)

        fields = [
            "id", "message", "story", "created_time", "type", "status_type",
            "link", "picture", "full_picture", "source", "place",
            "attachments", "shares", "reactions.summary(total_count)",
            "comments.summary(total_count)", "likes.summary(total_count)"
        ]

        params = {
            "fields": ",".join(fields),
            "limit": min(limit, 100),  # API max is 100
            "access_token": access_token
        }

        if after:
            params["after"] = after

        url = f"{self.api_base_url}/{user_id}/posts"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_posts_data(data)
                else:
                    error_data = await response.json()
                    raise ValueError(f"Facebook API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"Facebook posts request failed: {str(e)}")
            raise

    async def get_post_insights(
        self,
        post_id: str,
        access_token: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get insights for a specific post.

        Args:
            post_id: Facebook post ID
            access_token: Page access token
            metrics: List of metrics to retrieve

        Returns:
            Dict containing post insights
        """
        await self._check_rate_limit(access_token)

        if not metrics:
            metrics = [
                "post_impressions", "post_impressions_unique", "post_reach",
                "post_clicks", "post_reactions_by_type_total", "post_video_views",
                "post_video_view_time", "post_engaged_users"
            ]

        params = {
            "metric": ",".join(metrics),
            "access_token": access_token
        }

        url = f"{self.api_base_url}/{post_id}/insights"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_insights_data(data)
                else:
                    error_data = await response.json()
                    logger.warning(f"Facebook insights error for {post_id}: {error_data}")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"Facebook insights request failed: {str(e)}")
            return {}

    async def search_posts_by_hashtag(
        self,
        hashtag: str,
        access_token: str,
        limit: int = 25,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for posts by hashtag.
        Note: Facebook's hashtag search is limited and requires special permissions.

        Args:
            hashtag: Hashtag to search (without #)
            access_token: App or user access token
            limit: Number of posts to retrieve
            since: Posts created after this date
            until: Posts created before this date

        Returns:
            List of post data
        """
        await self._check_rate_limit(access_token)

        # Note: Facebook's public post search is very limited
        # This would typically require Instagram Basic Display API or specific partnerships

        params = {
            "q": f"#{hashtag}",
            "type": "post",
            "limit": min(limit, 25),
            "access_token": access_token
        }

        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())

        url = f"{self.api_base_url}/search"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.warning(f"Facebook hashtag search failed for #{hashtag}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"Facebook hashtag search failed: {str(e)}")
            return []

    async def get_page_insights(
        self,
        page_id: str,
        access_token: str,
        period: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get page-level insights and analytics.

        Args:
            page_id: Facebook page ID
            access_token: Page access token
            period: Insights period (day, week, days_28)
            since: Start date for insights
            until: End date for insights
            metrics: List of metrics to retrieve

        Returns:
            Dict containing page insights
        """
        await self._check_rate_limit(access_token)

        if not metrics:
            metrics = [
                "page_impressions", "page_impressions_unique", "page_reach",
                "page_fan_adds", "page_fan_removes", "page_engaged_users",
                "page_post_engagements", "page_video_views", "page_views_total"
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

        url = f"{self.api_base_url}/{page_id}/insights"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_page_insights(data)
                else:
                    error_data = await response.json()
                    logger.warning(f"Facebook page insights error: {error_data}")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"Facebook page insights request failed: {str(e)}")
            return {}

    async def verify_content_match(
        self,
        content_data: Dict[str, Any],
        campaign_criteria: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verify if content matches campaign criteria.

        Args:
            content_data: Facebook content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Tuple of (is_match, confidence_score, match_criteria)
        """
        match_criteria = []
        confidence_scores = []

        message = content_data.get("message", "").lower()
        story = content_data.get("story", "").lower()
        combined_text = f"{message} {story}".lower()

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

        # Check posting timeframe
        created_time = self.parse_datetime(content_data.get("created_time", ""))
        campaign_start = campaign_criteria.get("start_date")
        campaign_end = campaign_criteria.get("end_date")

        if campaign_start and campaign_end and created_time:
            if campaign_start <= created_time <= campaign_end:
                match_criteria.append("timeframe_match")
                confidence_scores.append(1.0)

        # Check post type requirements
        required_type = campaign_criteria.get("post_type")
        if required_type:
            post_type = content_data.get("type", "").lower()
            if post_type == required_type.lower():
                match_criteria.append("type_match")
                confidence_scores.append(1.0)

        # Check media requirements
        requires_media = campaign_criteria.get("requires_media", False)
        has_media = bool(content_data.get("picture") or content_data.get("full_picture") or
                        content_data.get("source") or content_data.get("attachments"))

        if not requires_media or has_media:
            if requires_media and has_media:
                match_criteria.append("media_match")
                confidence_scores.append(1.0)

        # Check minimum engagement requirements
        min_likes = campaign_criteria.get("min_likes", 0)
        min_shares = campaign_criteria.get("min_shares", 0)

        likes_count = content_data.get("likes", {}).get("summary", {}).get("total_count", 0)
        shares_count = content_data.get("shares", {}).get("count", 0)

        if likes_count >= min_likes and shares_count >= min_shares:
            match_criteria.append("engagement_match")
            confidence_scores.append(1.0)

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_match = overall_confidence > 0.5 and len(match_criteria) > 0

        return is_match, overall_confidence, match_criteria

    # Private helper methods

    def _transform_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Facebook page data to standard format."""
        picture_data = data.get("picture", {}).get("data", {}) if data.get("picture") else {}
        cover_data = data.get("cover", {}) if data.get("cover") else {}
        location_data = data.get("location", {}) if data.get("location") else {}

        return {
            "platform_user_id": data.get("id"),
            "username": data.get("username"),
            "display_name": data.get("name"),
            "bio": data.get("about", ""),
            "description": data.get("description", ""),
            "profile_picture_url": picture_data.get("url"),
            "cover_image_url": cover_data.get("source"),
            "fan_count": data.get("fan_count", 0),
            "talking_about_count": data.get("talking_about_count", 0),
            "website": data.get("website"),
            "category": data.get("category"),
            "verification_status": data.get("verification_status"),
            "verified": data.get("is_verified", False),
            "location": {
                "city": location_data.get("city"),
                "country": location_data.get("country"),
                "street": location_data.get("street"),
                "zip": location_data.get("zip")
            },
            "phone": data.get("phone"),
            "emails": data.get("emails", []),
            "founded": data.get("founded"),
            "link": data.get("link"),
            "updated_at": datetime.utcnow().isoformat()
        }

    def _transform_posts_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Facebook posts data to standard format."""
        post_items = []

        for post in data.get("data", []):
            # Determine content type
            post_type = post.get("type", "status")
            content_type = ContentType.POST

            if post_type == "video":
                content_type = ContentType.VIDEO
            elif post_type == "link":
                content_type = ContentType.POST
            elif post_type == "photo":
                content_type = ContentType.POST

            # Extract engagement metrics
            likes = post.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
            reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
            shares = post.get("shares", {}).get("count", 0)

            # Handle attachments
            media_urls = []
            attachments = post.get("attachments", {}).get("data", [])
            for attachment in attachments:
                if attachment.get("media"):
                    media_urls.append(attachment["media"].get("image", {}).get("src"))

            post_items.append({
                "platform_post_id": post.get("id"),
                "content_type": content_type,
                "content": post.get("message", "") or post.get("story", ""),
                "permalink": f"https://www.facebook.com/{post.get('id')}",
                "posted_at": post.get("created_time"),
                "post_type": post_type,
                "status_type": post.get("status_type"),
                "link": post.get("link"),
                "picture": post.get("picture"),
                "full_picture": post.get("full_picture"),
                "source": post.get("source"),
                "media_urls": media_urls,
                "like_count": likes,
                "comment_count": comments,
                "reaction_count": reactions,
                "share_count": shares,
                "place": post.get("place")
            })

        return {
            "data": post_items,
            "paging": data.get("paging", {}),
            "total_count": len(post_items)
        }

    def _transform_insights_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Facebook insights data to standard format."""
        insights = {}

        for metric_data in data.get("data", []):
            metric_name = metric_data.get("name")
            values = metric_data.get("values", [])

            if values:
                # Get the most recent value
                latest_value = values[-1].get("value", 0)
                insights[metric_name] = latest_value

        return insights

    def _transform_page_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform page insights data to standard format."""
        insights = {}

        for metric_data in data.get("data", []):
            metric_name = metric_data.get("name")
            values = metric_data.get("values", [])

            if values:
                # Sum values for the period
                total_value = sum(item.get("value", 0) for item in values)
                insights[metric_name] = total_value

        return insights

    async def _check_rate_limit(self, access_token: str) -> None:
        """Check and enforce rate limiting."""
        # Facebook has app-level and page-level rate limits
        await asyncio.sleep(0.1)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.platform

    def get_api_version(self) -> str:
        """Get API version."""
        return "v18.0"