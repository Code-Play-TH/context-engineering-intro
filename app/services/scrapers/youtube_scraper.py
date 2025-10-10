"""YouTube scraper using YouTube Data API v3."""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import re

from .base_scraper import (
    BaseScraper, SocialMetrics, PostData, ScrapingError, 
    RateLimitError, AuthenticationError, PlatformError
)


class YouTubeScraper(BaseScraper):
    """YouTube scraper using YouTube Data API v3."""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("youtube", api_config)
        
        self.api_key = api_config.get('api_key')
        self.client_id = api_config.get('client_id')
        self.client_secret = api_config.get('client_secret')
        self.access_token = api_config.get('access_token')
        
        # YouTube API endpoints
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Rate limits: 10,000 quota units per day
        # Most operations cost 1-100 units
        self.rate_limit = 10000
        self.window_duration = 86400  # 24 hours
        
        if not self.api_key:
            raise ValueError("YouTube API key is required")
    
    async def authenticate(self) -> bool:
        """Verify YouTube API key."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/channels"
                params = {
                    'part': 'id',
                    'mine': 'true',
                    'key': self.api_key
                }
                
                headers = {}
                if self.access_token:
                    headers['Authorization'] = f'Bearer {self.access_token}'
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'items' in data:
                            self.logger.info("YouTube API authentication successful")
                            return True
                        else:
                            # Try without OAuth for public API access
                            return await self._test_public_api()
                    elif response.status == 401:
                        raise AuthenticationError("Invalid YouTube API credentials")
                    elif response.status == 403:
                        error_data = await response.json()
                        if 'quotaExceeded' in str(error_data):
                            raise RateLimitError("YouTube API quota exceeded")
                        raise AuthenticationError(f"YouTube API access denied: {error_data}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"YouTube API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error during YouTube authentication: {e}")
    
    async def _test_public_api(self) -> bool:
        """Test public API access without OAuth."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search"
                params = {
                    'part': 'id',
                    'q': 'test',
                    'type': 'channel',
                    'maxResults': 1,
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        self.logger.info("YouTube public API access confirmed")
                        return True
                    else:
                        return False
        except:
            return False
    
    async def get_user_metrics(self, handle: str) -> SocialMetrics:
        """Get YouTube channel metrics."""
        handle = self.validate_handle(handle)
        
        # Get channel info and recent videos
        channel_info = await self._get_channel_info(handle)
        if not channel_info:
            raise PlatformError(f"YouTube channel not found: {handle}")
        
        channel_id = channel_info['id']
        recent_videos = await self._get_channel_videos(channel_id, limit=20)
        
        # Extract metrics from channel info
        statistics = channel_info.get('statistics', {})
        subscriber_count = int(statistics.get('subscriberCount', 0))
        video_count = int(statistics.get('videoCount', 0))
        view_count = int(statistics.get('viewCount', 0))
        
        # Calculate engagement metrics from recent videos
        if recent_videos:
            avg_likes, avg_comments, avg_shares, avg_views = self.calculate_average_metrics(recent_videos)
            engagement_rate = self.calculate_engagement_rate(
                int(avg_likes), int(avg_comments), int(avg_shares), subscriber_count
            )
        else:
            avg_likes = avg_comments = avg_shares = Decimal('0')
            avg_views = None
            engagement_rate = Decimal('0.00')
        
        return SocialMetrics(
            follower_count=subscriber_count,
            following_count=0,  # YouTube doesn't expose subscription count
            post_count=video_count,
            engagement_rate=engagement_rate,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_shares,
            avg_views=avg_views,
            platform_specific={
                'channel_id': channel_id,
                'channel_title': channel_info.get('snippet', {}).get('title'),
                'channel_description': channel_info.get('snippet', {}).get('description'),
                'channel_url': f"https://www.youtube.com/channel/{channel_id}",
                'custom_url': channel_info.get('snippet', {}).get('customUrl'),
                'thumbnail_url': channel_info.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url'),
                'total_view_count': view_count,
                'published_at': channel_info.get('snippet', {}).get('publishedAt'),
                'country': channel_info.get('snippet', {}).get('country'),
                'default_language': channel_info.get('snippet', {}).get('defaultLanguage')
            }
        )
    
    async def get_recent_posts(self, handle: str, limit: int = 10) -> List[PostData]:
        """Get recent YouTube videos."""
        handle = self.validate_handle(handle)
        
        channel_info = await self._get_channel_info(handle)
        if not channel_info:
            raise PlatformError(f"YouTube channel not found: {handle}")
        
        channel_id = channel_info['id']
        return await self._get_channel_videos(channel_id, limit=limit)
    
    async def get_post_metrics(self, post_id: str) -> PostData:
        """Get metrics for a specific YouTube video."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/videos"
                params = {
                    'part': 'snippet,statistics',
                    'id': post_id,
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        if items:
                            return self._parse_video_data(items[0])
                        else:
                            raise PlatformError(f"YouTube video not found: {post_id}")
                    elif response.status == 403:
                        error_data = await response.json()
                        if 'quotaExceeded' in str(error_data):
                            raise RateLimitError("YouTube API quota exceeded")
                        raise PlatformError(f"YouTube API error: {error_data}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"YouTube API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting YouTube video: {e}")
    
    async def _get_channel_info(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get YouTube channel information by handle or channel ID."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try different methods to find the channel
                search_params = []
                
                # If it looks like a channel ID (starts with UC)
                if handle.startswith('UC') and len(handle) == 24:
                    search_params.append(('id', handle))
                # If it looks like a custom URL
                elif handle.startswith('@') or not handle.startswith('UC'):
                    search_params.append(('forUsername', handle.lstrip('@')))
                    search_params.append(('forHandle', f"@{handle.lstrip('@')}"))
                
                for param_name, param_value in search_params:
                    url = f"{self.base_url}/channels"
                    params = {
                        'part': 'id,snippet,statistics',
                        param_name: param_value,
                        'key': self.api_key
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            items = data.get('items', [])
                            if items:
                                return items[0]
                        elif response.status == 403:
                            error_data = await response.json()
                            if 'quotaExceeded' in str(error_data):
                                raise RateLimitError("YouTube API quota exceeded")
                
                # If direct methods fail, try search
                return await self._search_channel(handle)
                
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting YouTube channel info: {e}")
    
    async def _search_channel(self, handle: str) -> Optional[Dict[str, Any]]:
        """Search for channel using YouTube search API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search"
                params = {
                    'part': 'id',
                    'q': handle,
                    'type': 'channel',
                    'maxResults': 5,
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        # Look for exact or close match
                        for item in items:
                            channel_id = item['id']['channelId']
                            # Get full channel info
                            channel_info = await self._get_channel_by_id(channel_id)
                            if channel_info:
                                channel_title = channel_info.get('snippet', {}).get('title', '').lower()
                                custom_url = channel_info.get('snippet', {}).get('customUrl', '').lower()
                                
                                if (handle.lower() in channel_title or 
                                    handle.lower() in custom_url or
                                    channel_title in handle.lower()):
                                    return channel_info
                        
                        # If no exact match, return first result
                        if items:
                            return await self._get_channel_by_id(items[0]['id']['channelId'])
                    
                    elif response.status == 403:
                        error_data = await response.json()
                        if 'quotaExceeded' in str(error_data):
                            raise RateLimitError("YouTube API quota exceeded")
                
                return None
                
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error searching YouTube channel: {e}")
    
    async def _get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel info by channel ID."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/channels"
                params = {
                    'part': 'id,snippet,statistics',
                    'id': channel_id,
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        return items[0] if items else None
                    return None
                    
        except aiohttp.ClientError:
            return None
    
    async def _get_channel_videos(self, channel_id: str, limit: int = 10) -> List[PostData]:
        """Get recent videos from a YouTube channel."""
        try:
            async with aiohttp.ClientSession() as session:
                # First get the uploads playlist ID
                url = f"{self.base_url}/channels"
                params = {
                    'part': 'contentDetails',
                    'id': channel_id,
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    items = data.get('items', [])
                    if not items:
                        return []
                    
                    uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Get videos from uploads playlist
                url = f"{self.base_url}/playlistItems"
                params = {
                    'part': 'snippet',
                    'playlistId': uploads_playlist_id,
                    'maxResults': min(limit, 50),
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    playlist_items = data.get('items', [])
                    
                    # Get video IDs
                    video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_items]
                    
                    if not video_ids:
                        return []
                    
                    # Get detailed video information
                    return await self._get_videos_details(video_ids)
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting YouTube videos: {e}")
    
    async def _get_videos_details(self, video_ids: List[str]) -> List[PostData]:
        """Get detailed information for multiple videos."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/videos"
                params = {
                    'part': 'snippet,statistics',
                    'id': ','.join(video_ids[:50]),  # API limit
                    'key': self.api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        videos = []
                        
                        for item in data.get('items', []):
                            try:
                                video = self._parse_video_data(item)
                                videos.append(video)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse YouTube video: {e}")
                                continue
                        
                        return videos
                    elif response.status == 403:
                        error_data = await response.json()
                        if 'quotaExceeded' in str(error_data):
                            raise RateLimitError("YouTube API quota exceeded")
                        raise PlatformError(f"YouTube API error: {error_data}")
                    else:
                        return []
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting YouTube video details: {e}")
    
    def _parse_video_data(self, item: Dict[str, Any]) -> PostData:
        """Parse YouTube API response into PostData."""
        try:
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            
            # Parse timestamp
            published_at = snippet.get('publishedAt', '')
            if published_at:
                posted_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            else:
                posted_at = datetime.utcnow()
            
            # Extract description and hashtags/mentions
            description = snippet.get('description', '')
            title = snippet.get('title', '')
            hashtags = self.extract_hashtags(description + ' ' + title)
            mentions = self.extract_mentions(description + ' ' + title)
            
            video_id = item.get('id', '')
            
            return PostData(
                post_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                post_type='youtube_video',
                caption=f"{title}\n\n{description}",
                posted_at=posted_at,
                likes=int(statistics.get('likeCount', 0)),
                comments=int(statistics.get('commentCount', 0)),
                shares=0,  # YouTube doesn't provide share count
                views=int(statistics.get('viewCount', 0)),
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse YouTube video data: {e}")
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get YouTube API rate limits and usage."""
        return {
            'platform': 'youtube',
            'quota_limit_per_day': 10000,
            'current_usage': self.requests_made,
            'quota_costs': {
                'channels': 1,
                'search': 100,
                'videos': 1,
                'playlistItems': 1,
                'commentThreads': 1
            },
            'endpoints': {
                'channels': {'cost': 1, 'limit': 10000},
                'search': {'cost': 100, 'limit': 100},  # 100 searches per day
                'videos': {'cost': 1, 'limit': 10000},
                'playlistItems': {'cost': 1, 'limit': 10000}
            },
            'notes': [
                'Quota resets daily at midnight Pacific Time',
                'Search operations are expensive (100 units each)',
                'Consider caching channel IDs to avoid repeated searches',
                'OAuth required for private data and higher quotas'
            ]
        }