"""
Twitter/X API v2 service for KOL data collection and content monitoring.
Implements Twitter API v2 for comprehensive influencer analytics.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode
import base64

from app.core.config import get_settings
from app.services.social_media.base import BaseSocialMediaService
from app.models.content import ContentType, VerificationStatus

logger = logging.getLogger(__name__)


class TwitterService(BaseSocialMediaService):
    """
    Twitter API v2 service for KOL management and content monitoring.

    Features:
    - User profile data collection
    - Tweet discovery and monitoring
    - Performance metrics tracking
    - Real-time content detection
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.platform = "twitter"
        self.api_base_url = "https://api.twitter.com/2"

        # Rate limiting (varies by endpoint)
        self.rate_limit_calls = 300
        self.rate_limit_window = 900  # 15 minutes

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

    async def get_user_profile(self, user_id: str, access_token: str = None) -> Dict[str, Any]:
        """
        Get Twitter user profile information.

        Args:
            user_id: Twitter user ID or username
            access_token: Optional user access token for private data

        Returns:
            Dict containing user profile data
        """
        await self._check_rate_limit(access_token)

        # Determine if user_id is numeric ID or username
        if user_id.isdigit():
            endpoint = f"users/{user_id}"
        else:
            endpoint = f"users/by/username/{user_id}"

        user_fields = [
            "id", "name", "username", "description", "profile_image_url",
            "public_metrics", "verified", "verified_type", "url",
            "location", "created_at", "pinned_tweet_id"
        ]

        params = {
            "user.fields": ",".join(user_fields),
            "expansions": "pinned_tweet_id"
        }

        headers = await self._get_auth_headers(access_token)
        url = f"{self.api_base_url}/{endpoint}"

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data"):
                        return self._transform_profile_data(data["data"])
                    else:
                        raise ValueError(f"User not found: {user_id}")
                elif response.status == 429:
                    retry_after = int(response.headers.get("x-rate-limit-reset", 900))
                    raise ValueError(f"Rate limit exceeded. Retry after {retry_after} seconds")
                else:
                    error_data = await response.json()
                    errors = error_data.get("errors", [])
                    error_msg = errors[0].get("detail", "Unknown error") if errors else "Unknown error"
                    raise ValueError(f"Twitter API error: {error_msg}")

        except aiohttp.ClientError as e:
            logger.error(f"Twitter API request failed: {str(e)}")
            raise

    async def get_user_media(
        self,
        user_id: str,
        access_token: str = None,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's tweets with pagination.

        Args:
            user_id: Twitter user ID
            access_token: Optional user access token
            limit: Number of tweets to retrieve (max 100)
            after: Pagination token

        Returns:
            Dict containing tweet data and pagination info
        """
        await self._check_rate_limit(access_token)

        tweet_fields = [
            "id", "text", "created_at", "public_metrics", "context_annotations",
            "entities", "geo", "in_reply_to_user_id", "referenced_tweets",
            "reply_settings", "source", "withheld"
        ]

        media_fields = [
            "media_key", "type", "url", "duration_ms", "height",
            "preview_image_url", "public_metrics", "width"
        ]

        params = {
            "max_results": min(limit, 100),  # API max is 100
            "tweet.fields": ",".join(tweet_fields),
            "media.fields": ",".join(media_fields),
            "expansions": "attachments.media_keys,author_id,geo.place_id"
        }

        if after:
            params["pagination_token"] = after

        headers = await self._get_auth_headers(access_token)
        url = f"{self.api_base_url}/users/{user_id}/tweets"

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_tweets_data(data)
                else:
                    error_data = await response.json()
                    errors = error_data.get("errors", [])
                    error_msg = errors[0].get("detail", "Unknown error") if errors else "Unknown error"
                    raise ValueError(f"Twitter API error: {error_msg}")

        except aiohttp.ClientError as e:
            logger.error(f"Twitter tweets request failed: {str(e)}")
            raise

    async def get_tweet_details(self, tweet_id: str, access_token: str = None) -> Dict[str, Any]:
        """
        Get detailed information for a specific tweet.

        Args:
            tweet_id: Twitter tweet ID
            access_token: Optional user access token

        Returns:
            Dict containing tweet details
        """
        await self._check_rate_limit(access_token)

        tweet_fields = [
            "id", "text", "created_at", "public_metrics", "context_annotations",
            "entities", "geo", "in_reply_to_user_id", "referenced_tweets",
            "reply_settings", "source", "withheld"
        ]

        user_fields = ["id", "name", "username", "verified", "public_metrics"]
        media_fields = ["media_key", "type", "url", "preview_image_url", "public_metrics"]

        params = {
            "tweet.fields": ",".join(tweet_fields),
            "user.fields": ",".join(user_fields),
            "media.fields": ",".join(media_fields),
            "expansions": "author_id,attachments.media_keys,geo.place_id"
        }

        headers = await self._get_auth_headers(access_token)
        url = f"{self.api_base_url}/tweets/{tweet_id}"

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data"):
                        return self._transform_tweet_data(data["data"], data.get("includes", {}))
                    else:
                        raise ValueError(f"Tweet not found: {tweet_id}")
                else:
                    error_data = await response.json()
                    errors = error_data.get("errors", [])
                    error_msg = errors[0].get("detail", "Unknown error") if errors else "Unknown error"
                    raise ValueError(f"Twitter API error: {error_msg}")

        except aiohttp.ClientError as e:
            logger.error(f"Twitter tweet request failed: {str(e)}")
            raise

    async def search_tweets(
        self,
        query: str,
        access_token: str = None,
        max_results: int = 25,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        next_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets by query.

        Args:
            query: Search query (supports Twitter search operators)
            access_token: Optional user access token
            max_results: Maximum results to return (10-100)
            start_time: Tweets created after this time
            end_time: Tweets created before this time
            next_token: Pagination token

        Returns:
            List of tweet data
        """
        await self._check_rate_limit(access_token)

        tweet_fields = [
            "id", "text", "created_at", "public_metrics", "context_annotations",
            "entities", "geo", "in_reply_to_user_id", "referenced_tweets",
            "reply_settings", "source"
        ]

        params = {
            "query": query,
            "max_results": min(max(max_results, 10), 100),  # API range is 10-100
            "tweet.fields": ",".join(tweet_fields),
            "expansions": "author_id,attachments.media_keys"
        }

        if start_time:
            params["start_time"] = start_time.isoformat() + "Z"
        if end_time:
            params["end_time"] = end_time.isoformat() + "Z"
        if next_token:
            params["next_token"] = next_token

        headers = await self._get_auth_headers(access_token)
        url = f"{self.api_base_url}/tweets/search/recent"

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = data.get("data", [])
                    includes = data.get("includes", {})

                    return [self._transform_tweet_data(tweet, includes) for tweet in tweets]
                else:
                    logger.warning(f"Twitter search failed for query: {query}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"Twitter search request failed: {str(e)}")
            return []

    async def verify_content_match(
        self,
        content_data: Dict[str, Any],
        campaign_criteria: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verify if content matches campaign criteria.

        Args:
            content_data: Twitter content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Tuple of (is_match, confidence_score, match_criteria)
        """
        match_criteria = []
        confidence_scores = []

        text = content_data.get("text", "").lower()
        hashtags = [tag.lower() for tag in content_data.get("hashtags", [])]
        mentions = [mention.lower() for mention in content_data.get("mentions", [])]

        # Check required hashtags
        required_hashtags = campaign_criteria.get("required_hashtags", [])
        if required_hashtags:
            hashtag_matches = sum(1 for tag in required_hashtags if tag.lower() in hashtags)
            if hashtag_matches > 0:
                match_criteria.append("hashtag_match")
                confidence_scores.append(hashtag_matches / len(required_hashtags))

        # Check keywords in text
        keywords = campaign_criteria.get("keywords", [])
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text)
            if keyword_matches > 0:
                match_criteria.append("keyword_match")
                confidence_scores.append(keyword_matches / len(keywords))

        # Check required mentions
        required_mentions = campaign_criteria.get("required_mentions", [])
        if required_mentions:
            mention_matches = sum(1 for mention in required_mentions if mention.lower() in mentions)
            if mention_matches > 0:
                match_criteria.append("mention_match")
                confidence_scores.append(mention_matches / len(required_mentions))

        # Check posting timeframe
        created_at = self.parse_datetime(content_data.get("created_at", ""))
        campaign_start = campaign_criteria.get("start_date")
        campaign_end = campaign_criteria.get("end_date")

        if campaign_start and campaign_end and created_at:
            if campaign_start <= created_at <= campaign_end:
                match_criteria.append("timeframe_match")
                confidence_scores.append(1.0)

        # Check minimum engagement requirements
        min_retweets = campaign_criteria.get("min_retweets", 0)
        min_likes = campaign_criteria.get("min_likes", 0)

        public_metrics = content_data.get("public_metrics", {})
        if (public_metrics.get("retweet_count", 0) >= min_retweets and
            public_metrics.get("like_count", 0) >= min_likes):
            match_criteria.append("engagement_match")
            confidence_scores.append(1.0)

        # Check for media requirements
        has_media_requirement = campaign_criteria.get("requires_media", False)
        has_media = len(content_data.get("media", [])) > 0

        if not has_media_requirement or has_media:
            if has_media_requirement and has_media:
                match_criteria.append("media_match")
                confidence_scores.append(1.0)

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_match = overall_confidence > 0.5 and len(match_criteria) > 0

        return is_match, overall_confidence, match_criteria

    # Private helper methods

    async def _get_auth_headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if access_token:
            # User context (OAuth 2.0)
            return {"Authorization": f"Bearer {access_token}"}
        else:
            # App-only context (Bearer token)
            return {"Authorization": f"Bearer {self.settings.TWITTER_BEARER_TOKEN}"}

    def _transform_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Twitter profile data to standard format."""
        public_metrics = data.get("public_metrics", {})

        return {
            "platform_user_id": data.get("id"),
            "username": data.get("username"),
            "display_name": data.get("name"),
            "bio": data.get("description"),
            "profile_picture_url": data.get("profile_image_url"),
            "follower_count": public_metrics.get("followers_count", 0),
            "following_count": public_metrics.get("following_count", 0),
            "tweet_count": public_metrics.get("tweet_count", 0),
            "listed_count": public_metrics.get("listed_count", 0),
            "website": data.get("url"),
            "location": data.get("location"),
            "verified": data.get("verified", False),
            "verified_type": data.get("verified_type"),
            "created_at": data.get("created_at"),
            "updated_at": datetime.utcnow().isoformat()
        }

    def _transform_tweets_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Twitter tweets data to standard format."""
        tweet_items = []
        tweets = data.get("data", [])
        includes = data.get("includes", {})

        for tweet in tweets:
            tweet_items.append(self._transform_tweet_data(tweet, includes))

        return {
            "data": tweet_items,
            "paging": {
                "next_token": data.get("meta", {}).get("next_token"),
                "previous_token": data.get("meta", {}).get("previous_token"),
                "result_count": data.get("meta", {}).get("result_count", 0)
            },
            "total_count": len(tweet_items)
        }

    def _transform_tweet_data(self, tweet: Dict[str, Any], includes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transform single Twitter tweet data to standard format."""
        if includes is None:
            includes = {}

        public_metrics = tweet.get("public_metrics", {})
        entities = tweet.get("entities", {})

        # Extract hashtags and mentions
        hashtags = [tag["tag"] for tag in entities.get("hashtags", [])]
        mentions = [mention["username"] for mention in entities.get("mentions", [])]

        # Extract media information
        media_data = []
        attachments = tweet.get("attachments", {})
        if attachments.get("media_keys"):
            media_list = includes.get("media", [])
            for media_key in attachments["media_keys"]:
                media_item = next((m for m in media_list if m["media_key"] == media_key), None)
                if media_item:
                    media_data.append({
                        "type": media_item.get("type"),
                        "url": media_item.get("url"),
                        "preview_image_url": media_item.get("preview_image_url"),
                        "width": media_item.get("width"),
                        "height": media_item.get("height")
                    })

        # Determine content type
        content_type = ContentType.POST
        if media_data:
            if any(m["type"] == "video" for m in media_data):
                content_type = ContentType.VIDEO
            elif len(media_data) > 1:
                content_type = ContentType.CAROUSEL

        return {
            "platform_post_id": tweet.get("id"),
            "content_type": content_type,
            "content": tweet.get("text"),
            "permalink": f"https://twitter.com/twitter/status/{tweet.get('id')}",
            "posted_at": tweet.get("created_at"),
            "hashtags": hashtags,
            "mentions": mentions,
            "media": media_data,
            "public_metrics": {
                "retweet_count": public_metrics.get("retweet_count", 0),
                "reply_count": public_metrics.get("reply_count", 0),
                "like_count": public_metrics.get("like_count", 0),
                "quote_count": public_metrics.get("quote_count", 0),
                "bookmark_count": public_metrics.get("bookmark_count", 0),
                "impression_count": public_metrics.get("impression_count", 0)
            },
            "context_annotations": tweet.get("context_annotations", []),
            "source": tweet.get("source"),
            "reply_settings": tweet.get("reply_settings"),
            "geo": tweet.get("geo")
        }

    async def _check_rate_limit(self, access_token: Optional[str]) -> None:
        """Check and enforce rate limiting."""
        # Twitter has strict rate limits - implement proper tracking
        await asyncio.sleep(0.1)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.platform

    def get_api_version(self) -> str:
        """Get API version."""
        return "v2"