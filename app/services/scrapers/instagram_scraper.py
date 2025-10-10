"""Instagram scraper using Instagram Basic Display API."""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .base_scraper import (
    BaseScraper, SocialMetrics, PostData, ScrapingError, 
    RateLimitError, AuthenticationError, PlatformError
)


class InstagramScraper(BaseScraper):
    """Instagram scraper using Instagram Basic Display API."""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("instagram", api_config)
        
        self.app_id = api_config.get('app_id')
        self.app_secret = api_config.get('app_secret')
        self.access_token = api_config.get('access_token')
        
        # Instagram API endpoints
        self.base_url = "https://graph.instagram.com"
        self.api_version = "v18.0"
        
        # Rate limits: 200 requests per hour per user
        self.rate_limit = 200
        self.window_duration = 3600
        
        if not all([self.app_id, self.app_secret, self.access_token]):
            raise ValueError("Instagram API credentials are incomplete")
    
    async def authenticate(self) -> bool:
        """Verify Instagram API access token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/me"
                params = {
                    'fields': 'id,username',
                    'access_token': self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Instagram authentication successful for user: {data.get('username')}")
                        return True
                    elif response.status == 401:
                        raise AuthenticationError("Invalid Instagram access token")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Instagram API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error during Instagram authentication: {e}")
    
    async def get_user_metrics(self, handle: str) -> SocialMetrics:
        """Get Instagram user metrics."""
        handle = self.validate_handle(handle)
        
        # First, get user ID from username
        user_id = await self._get_user_id_from_username(handle)
        if not user_id:
            raise PlatformError(f"Instagram user not found: {handle}")
        
        # Get user info and recent media
        user_info, recent_posts = await asyncio.gather(
            self._get_user_info(user_id),
            self._get_user_media(user_id, limit=20)
        )
        
        # Calculate metrics
        follower_count = user_info.get('followers_count', 0)
        following_count = user_info.get('follows_count', 0)
        post_count = user_info.get('media_count', 0)
        
        # Calculate engagement metrics from recent posts
        if recent_posts:
            avg_likes, avg_comments, avg_shares, avg_views = self.calculate_average_metrics(recent_posts)
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
            post_count=post_count,
            engagement_rate=engagement_rate,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_shares,
            avg_views=avg_views,
            platform_specific={
                'username': user_info.get('username'),
                'account_type': user_info.get('account_type'),
                'biography': user_info.get('biography'),
                'website': user_info.get('website'),
                'profile_picture_url': user_info.get('profile_picture_url')
            }
        )
    
    async def get_recent_posts(self, handle: str, limit: int = 10) -> List[PostData]:
        """Get recent Instagram posts."""
        handle = self.validate_handle(handle)
        
        user_id = await self._get_user_id_from_username(handle)
        if not user_id:
            raise PlatformError(f"Instagram user not found: {handle}")
        
        return await self._get_user_media(user_id, limit=limit)
    
    async def get_post_metrics(self, post_id: str) -> PostData:
        """Get metrics for a specific Instagram post."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{post_id}"
                params = {
                    'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                    'access_token': self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_post_data(data)
                    elif response.status == 404:
                        raise PlatformError(f"Instagram post not found: {post_id}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Instagram API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Instagram post: {e}")
    
    async def _get_user_id_from_username(self, username: str) -> Optional[str]:
        """Get Instagram user ID from username using Instagram Basic Display API."""
        # Note: Instagram Basic Display API doesn't provide username search
        # This is a limitation - in production, you'd need Instagram Graph API
        # or maintain a mapping of usernames to user IDs
        
        # For now, we'll use a placeholder approach
        # In production, implement proper username resolution
        self.logger.warning(
            f"Username to ID resolution not implemented for Instagram Basic Display API: {username}"
        )
        return None
    
    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get Instagram user information."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{user_id}"
                params = {
                    'fields': 'id,username,account_type,media_count',
                    'access_token': self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        error_data = await response.json()
                        if 'rate limit' in str(error_data).lower():
                            raise RateLimitError("Instagram rate limit exceeded")
                        raise PlatformError(f"Instagram API error: {error_data}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Instagram API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Instagram user info: {e}")
    
    async def _get_user_media(self, user_id: str, limit: int = 10) -> List[PostData]:
        """Get Instagram user media."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{user_id}/media"
                params = {
                    'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                    'limit': min(limit, 25),  # Instagram API limit
                    'access_token': self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = []
                        
                        for item in data.get('data', []):
                            try:
                                post = self._parse_post_data(item)
                                posts.append(post)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse Instagram post: {e}")
                                continue
                        
                        return posts
                    elif response.status == 400:
                        error_data = await response.json()
                        if 'rate limit' in str(error_data).lower():
                            raise RateLimitError("Instagram rate limit exceeded")
                        raise PlatformError(f"Instagram API error: {error_data}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Instagram API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Instagram media: {e}")
    
    def _parse_post_data(self, item: Dict[str, Any]) -> PostData:
        """Parse Instagram API response into PostData."""
        try:
            # Parse timestamp
            timestamp_str = item.get('timestamp', '')
            if timestamp_str:
                posted_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                posted_at = datetime.utcnow()
            
            # Extract caption and hashtags/mentions
            caption = item.get('caption', '')
            hashtags = self.extract_hashtags(caption)
            mentions = self.extract_mentions(caption)
            
            # Determine post type
            media_type = item.get('media_type', 'IMAGE')
            post_type_map = {
                'IMAGE': 'post',
                'VIDEO': 'video',
                'CAROUSEL_ALBUM': 'post'
            }
            post_type = post_type_map.get(media_type, 'post')
            
            return PostData(
                post_id=item.get('id', ''),
                url=item.get('permalink', ''),
                post_type=post_type,
                caption=caption,
                posted_at=posted_at,
                likes=item.get('like_count', 0),
                comments=item.get('comments_count', 0),
                shares=0,  # Instagram doesn't provide share count via API
                views=None,  # Not available in Basic Display API
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse Instagram post data: {e}")
    
    async def refresh_access_token(self) -> str:
        """Refresh Instagram access token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/refresh_access_token"
                params = {
                    'grant_type': 'ig_refresh_token',
                    'access_token': self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        new_token = data.get('access_token')
                        expires_in = data.get('expires_in')
                        
                        self.logger.info(f"Instagram access token refreshed, expires in {expires_in} seconds")
                        return new_token
                    else:
                        error_data = await response.json()
                        raise AuthenticationError(f"Failed to refresh Instagram token: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error refreshing Instagram token: {e}")
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get Instagram API rate limits and usage."""
        return {
            'platform': 'instagram',
            'rate_limit_per_hour': 200,
            'rate_limit_per_day': 4800,  # 200 * 24
            'current_usage': self.requests_made,
            'window_remaining': self.get_rate_limit_status()['window_remaining_seconds'],
            'endpoints': {
                'user_info': {'limit': 200, 'window': 3600},
                'user_media': {'limit': 200, 'window': 3600},
                'media_info': {'limit': 200, 'window': 3600}
            }
        }