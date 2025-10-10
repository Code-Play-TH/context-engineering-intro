"""TikTok scraper using TikTok API for Business."""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .base_scraper import (
    BaseScraper, SocialMetrics, PostData, ScrapingError, 
    RateLimitError, AuthenticationError, PlatformError
)


class TikTokScraper(BaseScraper):
    """TikTok scraper using TikTok API for Business."""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("tiktok", api_config)
        
        self.app_id = api_config.get('app_id')
        self.app_secret = api_config.get('app_secret')
        self.access_token = api_config.get('access_token')
        
        # TikTok API endpoints
        self.base_url = "https://open-api.tiktok.com"
        self.api_version = "v1.3"
        
        # Rate limits: 100 requests per hour per app
        self.rate_limit = 100
        self.window_duration = 3600
        
        if not all([self.app_id, self.app_secret, self.access_token]):
            raise ValueError("TikTok API credentials are incomplete")
    
    async def authenticate(self) -> bool:
        """Verify TikTok API access token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/user/info/"
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('error', {}).get('code') == 'ok':
                            user_info = data.get('data', {}).get('user', {})
                            self.logger.info(f"TikTok authentication successful for user: {user_info.get('display_name')}")
                            return True
                        else:
                            raise AuthenticationError(f"TikTok API error: {data.get('error', {})}")
                    elif response.status == 401:
                        raise AuthenticationError("Invalid TikTok access token")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"TikTok API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error during TikTok authentication: {e}")
    
    async def get_user_metrics(self, handle: str) -> SocialMetrics:
        """Get TikTok user metrics."""
        handle = self.validate_handle(handle)
        
        # Get user info and recent videos
        user_info, recent_videos = await asyncio.gather(
            self._get_user_info(),
            self._get_user_videos(limit=20)
        )
        
        # Calculate metrics
        follower_count = user_info.get('follower_count', 0)
        following_count = user_info.get('following_count', 0)
        video_count = user_info.get('video_count', 0)
        likes_count = user_info.get('likes_count', 0)
        
        # Calculate engagement metrics from recent videos
        if recent_videos:
            avg_likes, avg_comments, avg_shares, avg_views = self.calculate_average_metrics(recent_videos)
            engagement_rate = self.calculate_engagement_rate(
                int(avg_likes), int(avg_comments), int(avg_shares), follower_count
            )
        else:
            avg_likes = avg_comments = avg_shares = Decimal('0')
            avg_views = None
            engagement_rate = Decimal('0.00')
        
        return SocialMetrics(
            follower_count=follower_count,
            following_count=following_count,
            post_count=video_count,
            engagement_rate=engagement_rate,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_shares,
            avg_views=avg_views,
            platform_specific={
                'username': user_info.get('username'),
                'display_name': user_info.get('display_name'),
                'bio_description': user_info.get('bio_description'),
                'profile_deep_link': user_info.get('profile_deep_link'),
                'avatar_url': user_info.get('avatar_url'),
                'avatar_url_100': user_info.get('avatar_url_100'),
                'avatar_url_200': user_info.get('avatar_url_200'),
                'is_verified': user_info.get('is_verified', False),
                'total_likes': likes_count
            }
        )
    
    async def get_recent_posts(self, handle: str, limit: int = 10) -> List[PostData]:
        """Get recent TikTok videos."""
        handle = self.validate_handle(handle)
        return await self._get_user_videos(limit=limit)
    
    async def get_post_metrics(self, post_id: str) -> PostData:
        """Get metrics for a specific TikTok video."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/video/query/"
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'filters': {
                        'video_ids': [post_id]
                    },
                    'fields': [
                        'id', 'title', 'video_description', 'create_time',
                        'cover_image_url', 'share_url', 'embed_html', 'embed_link',
                        'like_count', 'comment_count', 'share_count', 'view_count'
                    ]
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('error', {}).get('code') == 'ok':
                            videos = data.get('data', {}).get('videos', [])
                            if videos:
                                return self._parse_video_data(videos[0])
                            else:
                                raise PlatformError(f"TikTok video not found: {post_id}")
                        else:
                            raise PlatformError(f"TikTok API error: {data.get('error', {})}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"TikTok API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting TikTok video: {e}")
    
    async def _get_user_info(self) -> Dict[str, Any]:
        """Get TikTok user information."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/user/info/"
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'fields': [
                        'open_id', 'union_id', 'avatar_url', 'avatar_url_100', 'avatar_url_200',
                        'display_name', 'bio_description', 'profile_deep_link', 'is_verified',
                        'follower_count', 'following_count', 'likes_count', 'video_count'
                    ]
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('error', {}).get('code') == 'ok':
                            return data.get('data', {}).get('user', {})
                        else:
                            raise PlatformError(f"TikTok API error: {data.get('error', {})}")
                    elif response.status == 429:
                        raise RateLimitError("TikTok rate limit exceeded")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"TikTok API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting TikTok user info: {e}")
    
    async def _get_user_videos(self, limit: int = 10) -> List[PostData]:
        """Get TikTok user videos."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/video/list/"
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'max_count': min(limit, 20),  # TikTok API limit
                    'fields': [
                        'id', 'title', 'video_description', 'create_time',
                        'cover_image_url', 'share_url', 'embed_html', 'embed_link',
                        'like_count', 'comment_count', 'share_count', 'view_count'
                    ]
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('error', {}).get('code') == 'ok':
                            videos = data.get('data', {}).get('videos', [])
                            posts = []
                            
                            for video in videos:
                                try:
                                    post = self._parse_video_data(video)
                                    posts.append(post)
                                except Exception as e:
                                    self.logger.warning(f"Failed to parse TikTok video: {e}")
                                    continue
                            
                            return posts
                        else:
                            raise PlatformError(f"TikTok API error: {data.get('error', {})}")
                    elif response.status == 429:
                        raise RateLimitError("TikTok rate limit exceeded")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"TikTok API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting TikTok videos: {e}")
    
    def _parse_video_data(self, video: Dict[str, Any]) -> PostData:
        """Parse TikTok API response into PostData."""
        try:
            # Parse timestamp
            create_time = video.get('create_time', 0)
            if create_time:
                posted_at = datetime.fromtimestamp(create_time)
            else:
                posted_at = datetime.utcnow()
            
            # Extract description and hashtags/mentions
            description = video.get('video_description', '') or video.get('title', '')
            hashtags = self.extract_hashtags(description)
            mentions = self.extract_mentions(description)
            
            return PostData(
                post_id=video.get('id', ''),
                url=video.get('share_url', ''),
                post_type='tiktok_video',
                caption=description,
                posted_at=posted_at,
                likes=video.get('like_count', 0),
                comments=video.get('comment_count', 0),
                shares=video.get('share_count', 0),
                views=video.get('view_count'),
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse TikTok video data: {e}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh TikTok access token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/oauth/refresh_token/"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Cache-Control': 'no-cache'
                }
                
                data = {
                    'client_key': self.app_id,
                    'client_secret': self.app_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token
                }
                
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        if token_data.get('error', {}).get('code') == 'ok':
                            data = token_data.get('data', {})
                            self.logger.info(f"TikTok access token refreshed, expires in {data.get('expires_in')} seconds")
                            return data
                        else:
                            raise AuthenticationError(f"Failed to refresh TikTok token: {token_data.get('error', {})}")
                    else:
                        error_data = await response.json()
                        raise AuthenticationError(f"Failed to refresh TikTok token: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error refreshing TikTok token: {e}")
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get TikTok API rate limits and usage."""
        return {
            'platform': 'tiktok',
            'rate_limit_per_hour': 100,
            'rate_limit_per_day': 2400,  # 100 * 24
            'current_usage': self.requests_made,
            'window_remaining': self.get_rate_limit_status()['window_remaining_seconds'],
            'endpoints': {
                'user_info': {'limit': 100, 'window': 3600},
                'video_list': {'limit': 100, 'window': 3600},
                'video_query': {'limit': 100, 'window': 3600}
            },
            'notes': [
                'Rate limits are per app, not per user',
                'Some endpoints may have additional daily limits',
                'Business accounts may have higher limits'
            ]
        }