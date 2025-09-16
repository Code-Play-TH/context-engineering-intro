"""
YouTube Data API v3 service for KOL data collection and content monitoring.
Implements comprehensive YouTube analytics for influencer management.
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


class YouTubeService(BaseSocialMediaService):
    """
    YouTube Data API v3 service for KOL management and content monitoring.

    Features:
    - Channel profile data collection
    - Video discovery and monitoring
    - Performance metrics tracking
    - Analytics data collection
    """

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.platform = "youtube"
        self.api_base_url = "https://www.googleapis.com/youtube/v3"

        # Rate limiting (10,000 quota units per day)
        self.rate_limit_calls = 10000
        self.rate_limit_window = 86400  # 24 hours

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
        Get YouTube channel information.

        Args:
            user_id: YouTube channel ID or username
            access_token: Optional access token for private data

        Returns:
            Dict containing channel profile data
        """
        await self._check_rate_limit()

        # Determine if user_id is channel ID or username
        if user_id.startswith('UC') and len(user_id) == 24:
            # Channel ID format
            id_param = user_id
            id_type = "id"
        else:
            # Username format
            id_param = user_id
            id_type = "forUsername"

        parts = ["snippet", "statistics", "brandingSettings", "status"]

        params = {
            "part": ",".join(parts),
            id_type: id_param,
            "key": self.settings.YOUTUBE_API_KEY
        }

        url = f"{self.api_base_url}/channels"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("items"):
                        return self._transform_channel_data(data["items"][0])
                    else:
                        raise ValueError(f"Channel not found: {user_id}")
                elif response.status == 403:
                    error_data = await response.json()
                    raise ValueError(f"YouTube API quota exceeded: {error_data.get('error', {}).get('message', 'Unknown error')}")
                else:
                    error_data = await response.json()
                    raise ValueError(f"YouTube API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"YouTube API request failed: {str(e)}")
            raise

    async def get_user_media(
        self,
        user_id: str,
        access_token: str = None,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get channel's videos with pagination.

        Args:
            user_id: YouTube channel ID
            access_token: Optional access token
            limit: Number of videos to retrieve (max 50)
            after: Page token for pagination

        Returns:
            Dict containing video data and pagination info
        """
        await self._check_rate_limit()

        # First get the uploads playlist ID
        uploads_playlist_id = await self._get_uploads_playlist_id(user_id)
        if not uploads_playlist_id:
            return {"data": [], "paging": {}, "total_count": 0}

        parts = ["snippet", "contentDetails"]
        params = {
            "part": ",".join(parts),
            "playlistId": uploads_playlist_id,
            "maxResults": min(limit, 50),  # API max is 50
            "key": self.settings.YOUTUBE_API_KEY
        }

        if after:
            params["pageToken"] = after

        url = f"{self.api_base_url}/playlistItems"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Get video statistics
                    video_ids = [item["contentDetails"]["videoId"] for item in data.get("items", [])]
                    video_stats = await self._get_video_statistics(video_ids)

                    return self._transform_videos_data(data, video_stats)
                else:
                    error_data = await response.json()
                    raise ValueError(f"YouTube API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except aiohttp.ClientError as e:
            logger.error(f"YouTube videos request failed: {str(e)}")
            raise

    async def get_video_analytics(
        self,
        video_id: str,
        access_token: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific video.

        Args:
            video_id: YouTube video ID
            access_token: Channel owner access token
            start_date: Analytics start date
            end_date: Analytics end date

        Returns:
            Dict containing video analytics
        """
        await self._check_rate_limit()

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        metrics = [
            "views", "likes", "dislikes", "comments", "shares",
            "estimatedMinutesWatched", "averageViewDuration",
            "subscribersGained", "subscribersLost"
        ]

        params = {
            "ids": f"video=={video_id}",
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "metrics": ",".join(metrics),
            "access_token": access_token
        }

        url = "https://youtubeanalytics.googleapis.com/v2/reports"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_analytics_data(data, metrics)
                else:
                    error_data = await response.json()
                    logger.warning(f"YouTube analytics error for {video_id}: {error_data}")
                    return {}

        except aiohttp.ClientError as e:
            logger.error(f"YouTube analytics request failed: {str(e)}")
            return {}

    async def search_videos(
        self,
        query: str,
        max_results: int = 25,
        published_after: Optional[datetime] = None,
        published_before: Optional[datetime] = None,
        channel_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for videos by query.

        Args:
            query: Search query
            max_results: Maximum results to return
            published_after: Videos published after this date
            published_before: Videos published before this date
            channel_id: Specific channel to search

        Returns:
            List of video data
        """
        await self._check_rate_limit()

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": "relevance",
            "key": self.settings.YOUTUBE_API_KEY
        }

        if published_after:
            params["publishedAfter"] = published_after.isoformat() + "Z"
        if published_before:
            params["publishedBefore"] = published_before.isoformat() + "Z"
        if channel_id:
            params["channelId"] = channel_id

        url = f"{self.api_base_url}/search"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Get video statistics
                    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
                    video_stats = await self._get_video_statistics(video_ids)

                    return self._transform_search_results(data, video_stats)
                else:
                    logger.warning(f"YouTube search failed for query: {query}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"YouTube search request failed: {str(e)}")
            return []

    async def verify_content_match(
        self,
        content_data: Dict[str, Any],
        campaign_criteria: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verify if content matches campaign criteria.

        Args:
            content_data: YouTube content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Tuple of (is_match, confidence_score, match_criteria)
        """
        match_criteria = []
        confidence_scores = []

        title = content_data.get("title", "").lower()
        description = content_data.get("description", "").lower()
        tags = content_data.get("tags", [])
        combined_text = f"{title} {description} {' '.join(tags)}".lower()

        # Check required keywords in title/description
        keywords = campaign_criteria.get("keywords", [])
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in combined_text)
            if keyword_matches > 0:
                match_criteria.append("keyword_match")
                confidence_scores.append(keyword_matches / len(keywords))

        # Check hashtags in tags or description
        required_hashtags = campaign_criteria.get("required_hashtags", [])
        if required_hashtags:
            hashtag_matches = sum(1 for tag in required_hashtags if tag.lower() in combined_text)
            if hashtag_matches > 0:
                match_criteria.append("hashtag_match")
                confidence_scores.append(hashtag_matches / len(required_hashtags))

        # Check video category
        required_category = campaign_criteria.get("category_id")
        if required_category and content_data.get("category_id") == required_category:
            match_criteria.append("category_match")
            confidence_scores.append(1.0)

        # Check posting timeframe
        published_at = self.parse_datetime(content_data.get("published_at", ""))
        campaign_start = campaign_criteria.get("start_date")
        campaign_end = campaign_criteria.get("end_date")

        if campaign_start and campaign_end and published_at:
            if campaign_start <= published_at <= campaign_end:
                match_criteria.append("timeframe_match")
                confidence_scores.append(1.0)

        # Check video duration requirements
        duration_requirement = campaign_criteria.get("min_duration_seconds")
        if duration_requirement and content_data.get("duration_seconds", 0) >= duration_requirement:
            match_criteria.append("duration_match")
            confidence_scores.append(1.0)

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_match = overall_confidence > 0.5 and len(match_criteria) > 0

        return is_match, overall_confidence, match_criteria

    # Private helper methods

    async def _get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """Get the uploads playlist ID for a channel."""
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self.settings.YOUTUBE_API_KEY
        }

        url = f"{self.api_base_url}/channels"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("items"):
                        content_details = data["items"][0].get("contentDetails", {})
                        related_playlists = content_details.get("relatedPlaylists", {})
                        return related_playlists.get("uploads")
                return None

        except aiohttp.ClientError:
            return None

    async def _get_video_statistics(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get statistics for multiple videos."""
        if not video_ids:
            return {}

        # YouTube API allows up to 50 IDs per request
        chunks = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
        all_stats = {}

        for chunk in chunks:
            params = {
                "part": "statistics,contentDetails,status",
                "id": ",".join(chunk),
                "key": self.settings.YOUTUBE_API_KEY
            }

            url = f"{self.api_base_url}/videos"

            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get("items", []):
                            all_stats[item["id"]] = item
                    await asyncio.sleep(0.1)  # Rate limiting

            except aiohttp.ClientError as e:
                logger.error(f"Failed to get video statistics: {str(e)}")

        return all_stats

    def _transform_channel_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform YouTube channel data to standard format."""
        snippet = data.get("snippet", {})
        statistics = data.get("statistics", {})
        branding = data.get("brandingSettings", {}).get("channel", {})

        return {
            "platform_user_id": data.get("id"),
            "username": snippet.get("customUrl", "").replace("@", ""),
            "display_name": snippet.get("title"),
            "bio": snippet.get("description"),
            "profile_picture_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "subscriber_count": int(statistics.get("subscriberCount", 0)),
            "video_count": int(statistics.get("videoCount", 0)),
            "view_count": int(statistics.get("viewCount", 0)),
            "website": branding.get("unsubscribedTrailer"),
            "country": snippet.get("country"),
            "created_at": snippet.get("publishedAt"),
            "verified": True,  # Most channels accessible via API are verified
            "updated_at": datetime.utcnow().isoformat()
        }

    def _transform_videos_data(self, data: Dict[str, Any], video_stats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Transform YouTube videos data to standard format."""
        video_items = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item["contentDetails"]["videoId"]
            stats = video_stats.get(video_id, {}).get("statistics", {})
            content_details = video_stats.get(video_id, {}).get("contentDetails", {})

            # Parse duration
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = self._parse_duration(duration_str)

            video_items.append({
                "platform_post_id": video_id,
                "content_type": ContentType.VIDEO,
                "title": snippet.get("title"),
                "content": snippet.get("description", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "permalink": f"https://www.youtube.com/watch?v={video_id}",
                "posted_at": snippet.get("publishedAt"),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration_seconds": duration_seconds,
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId")
            })

        return {
            "data": video_items,
            "paging": {
                "nextPageToken": data.get("nextPageToken"),
                "prevPageToken": data.get("prevPageToken")
            },
            "total_count": len(video_items)
        }

    def _transform_search_results(self, data: Dict[str, Any], video_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform YouTube search results to standard format."""
        results = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item["id"]["videoId"]
            stats = video_stats.get(video_id, {}).get("statistics", {})

            results.append({
                "platform_post_id": video_id,
                "content_type": ContentType.VIDEO,
                "title": snippet.get("title"),
                "content": snippet.get("description", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "permalink": f"https://www.youtube.com/watch?v={video_id}",
                "posted_at": snippet.get("publishedAt"),
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle"),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0))
            })

        return results

    def _transform_analytics_data(self, data: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Transform YouTube analytics data to standard format."""
        rows = data.get("rows", [])
        if not rows:
            return {}

        # YouTube Analytics returns data in the same order as requested metrics
        analytics = {}
        for i, metric in enumerate(metrics):
            if i < len(rows[0]):
                analytics[metric] = rows[0][i]

        return analytics

    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration string to seconds."""
        import re

        # Pattern for ISO 8601 duration (PT#H#M#S)
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        # Basic rate limiting - in production, implement proper quota tracking
        await asyncio.sleep(0.1)

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.platform

    def get_api_version(self) -> str:
        """Get API version."""
        return "v3"