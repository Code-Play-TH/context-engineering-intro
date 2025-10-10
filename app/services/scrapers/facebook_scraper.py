"""Facebook scraper using Facebook Graph API."""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .base_scraper import (
    BaseScraper, SocialMetrics, PostData, ScrapingError, 
    RateLimitError, AuthenticationError, PlatformError
)


class FacebookScraper(BaseScraper):
    """Facebook scraper using Facebook Graph API."""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("facebook", api_config)
        
        self.app_id = api_config.get('app_id')
        self.app_secret = api_config.get('app_secret')
        self.access_token = api_config.get('access_token')
        self.page_access_token = api_config.get('page_access_token')
        
        # Facebook API endpoints
        self.base_url = "https://graph.facebook.com"
        self.api_version = "v18.0"
        
        # Rate limits: 200 requests per hour per user
        self.rate_limit = 200
        self.window_duration = 3600
        
        if not all([self.app_id, self.app_secret, self.access_token]):
            raise ValueError("Facebook API credentials are incomplete")
    
    async def authenticate(self) -> bool:
        """Verify Facebook API access token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/me"
                params = {
                    'access_token': self.access_token,
                    'fields': 'id,name'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Facebook authentication successful for user: {data.get('name')}")
                        return True
                    elif response.status == 401:
                        raise AuthenticationError("Invalid Facebook access token")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Facebook API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error during Facebook authentication: {e}")
    
    async def get_user_metrics(self, handle: str) -> SocialMetrics:
        """Get Facebook page metrics."""
        handle = self.validate_handle(handle)
        
        # For Facebook, we primarily work with pages, not personal profiles
        page_info = await self._get_page_info(handle)
        if not page_info:
            raise PlatformError(f"Facebook page not found: {handle}")
        
        page_id = page_info['id']
        recent_posts = await self._get_page_posts(page_id, limit=20)
        
        # Extract metrics from page info
        fan_count = page_info.get('fan_count', 0)
        talking_about_count = page_info.get('talking_about_count', 0)
        
        # Get page insights if available
        insights = await self._get_page_insights(page_id)
        
        # Calculate engagement metrics from recent posts
        if recent_posts:
            avg_likes, avg_comments, avg_shares, avg_views = self.calculate_average_metrics(recent_posts)
            engagement_rate = self.calculate_engagement_rate(
                int(avg_likes), int(avg_comments), int(avg_shares), fan_count
            )
        else:
            avg_likes = avg_comments = avg_shares = Decimal('0')
            avg_views = None
            engagement_rate = Decimal('0.00')
        
        return SocialMetrics(
            follower_count=fan_count,
            following_count=0,  # Facebook pages don't have "following" count
            post_count=len(recent_posts),  # Approximate from recent posts
            engagement_rate=engagement_rate,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_shares,
            avg_views=avg_views,
            platform_specific={
                'page_id': page_id,
                'page_name': page_info.get('name'),
                'page_username': page_info.get('username'),
                'page_category': page_info.get('category'),
                'page_about': page_info.get('about'),
                'page_website': page_info.get('website'),
                'page_phone': page_info.get('phone'),
                'page_location': page_info.get('location'),
                'page_link': page_info.get('link'),
                'verification_status': page_info.get('verification_status'),
                'talking_about_count': talking_about_count,
                'checkins': page_info.get('checkins'),
                'were_here_count': page_info.get('were_here_count'),
                'insights': insights
            }
        )
    
    async def get_recent_posts(self, handle: str, limit: int = 10) -> List[PostData]:
        """Get recent Facebook posts."""
        handle = self.validate_handle(handle)
        
        page_info = await self._get_page_info(handle)
        if not page_info:
            raise PlatformError(f"Facebook page not found: {handle}")
        
        page_id = page_info['id']
        return await self._get_page_posts(page_id, limit=limit)
    
    async def get_post_metrics(self, post_id: str) -> PostData:
        """Get metrics for a specific Facebook post."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/{post_id}"
                params = {
                    'access_token': self.page_access_token or self.access_token,
                    'fields': 'id,message,story,created_time,type,link,picture,source,name,caption,description,from,reactions.summary(true),comments.summary(true),shares'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_post_data(data)
                    elif response.status == 400:
                        error_data = await response.json()
                        if 'rate limit' in str(error_data).lower():
                            raise RateLimitError("Facebook rate limit exceeded")
                        raise PlatformError(f"Facebook API error: {error_data}")
                    elif response.status == 404:
                        raise PlatformError(f"Facebook post not found: {post_id}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Facebook API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Facebook post: {e}")
    
    async def _get_page_info(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get Facebook page information."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try direct page access first
                url = f"{self.base_url}/{self.api_version}/{handle}"
                params = {
                    'access_token': self.page_access_token or self.access_token,
                    'fields': 'id,name,username,category,about,website,phone,location,link,fan_count,talking_about_count,checkins,were_here_count,verification_status'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        error_data = await response.json()
                        if 'rate limit' in str(error_data).lower():
                            raise RateLimitError("Facebook rate limit exceeded")
                        # Try search if direct access fails
                        return await self._search_page(handle)
                    else:
                        return await self._search_page(handle)
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Facebook page info: {e}")
    
    async def _search_page(self, handle: str) -> Optional[Dict[str, Any]]:
        """Search for Facebook page."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/search"
                params = {
                    'access_token': self.access_token,
                    'q': handle,
                    'type': 'page',
                    'fields': 'id,name,username,category,link',
                    'limit': 10
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        pages = data.get('data', [])
                        
                        # Look for exact or close match
                        for page in pages:
                            page_username = page.get('username', '').lower()
                            page_name = page.get('name', '').lower()
                            
                            if (handle.lower() == page_username or 
                                handle.lower() in page_name or
                                page_name in handle.lower()):
                                # Get full page info
                                return await self._get_page_by_id(page['id'])
                        
                        # If no exact match, return first result
                        if pages:
                            return await self._get_page_by_id(pages[0]['id'])
                    
                    return None
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error searching Facebook page: {e}")
    
    async def _get_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get full page information by page ID."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/{page_id}"
                params = {
                    'access_token': self.page_access_token or self.access_token,
                    'fields': 'id,name,username,category,about,website,phone,location,link,fan_count,talking_about_count,checkins,were_here_count,verification_status'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except aiohttp.ClientError:
            return None
    
    async def _get_page_posts(self, page_id: str, limit: int = 10) -> List[PostData]:
        """Get recent posts from a Facebook page."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/{page_id}/posts"
                params = {
                    'access_token': self.page_access_token or self.access_token,
                    'fields': 'id,message,story,created_time,type,link,picture,source,name,caption,description,from,reactions.summary(true),comments.summary(true),shares',
                    'limit': min(limit, 100)  # Facebook API limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = []
                        
                        for post in data.get('data', []):
                            try:
                                parsed_post = self._parse_post_data(post)
                                posts.append(parsed_post)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse Facebook post: {e}")
                                continue
                        
                        return posts
                    elif response.status == 400:
                        error_data = await response.json()
                        if 'rate limit' in str(error_data).lower():
                            raise RateLimitError("Facebook rate limit exceeded")
                        raise PlatformError(f"Facebook API error: {error_data}")
                    else:
                        return []
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Facebook posts: {e}")
    
    async def _get_page_insights(self, page_id: str) -> Dict[str, Any]:
        """Get Facebook page insights (requires page access token)."""
        if not self.page_access_token:
            return {}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.api_version}/{page_id}/insights"
                params = {
                    'access_token': self.page_access_token,
                    'metric': 'page_impressions,page_reach,page_engaged_users,page_post_engagements',
                    'period': 'day',
                    'since': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'until': datetime.now().strftime('%Y-%m-%d')
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        insights = {}
                        
                        for metric in data.get('data', []):
                            metric_name = metric.get('name')
                            values = metric.get('values', [])
                            if values:
                                # Get latest value
                                insights[metric_name] = values[-1].get('value', 0)
                        
                        return insights
                    else:
                        return {}
                        
        except aiohttp.ClientError:
            return {}
    
    def _parse_post_data(self, post: Dict[str, Any]) -> PostData:
        """Parse Facebook API response into PostData."""
        try:
            # Parse timestamp
            created_time = post.get('created_time', '')
            if created_time:
                posted_at = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            else:
                posted_at = datetime.utcnow()
            
            # Extract message/story content
            message = post.get('message', '')
            story = post.get('story', '')
            content = message or story
            
            # Extract hashtags and mentions
            hashtags = self.extract_hashtags(content)
            mentions = self.extract_mentions(content)
            
            # Get engagement metrics
            reactions = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
            comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
            shares = post.get('shares', {}).get('count', 0)
            
            # Determine post type
            post_type = post.get('type', 'status')
            if post_type == 'photo':
                post_type = 'post'
            elif post_type == 'video':
                post_type = 'video'
            elif post_type == 'link':
                post_type = 'post'
            
            post_id = post.get('id', '')
            
            return PostData(
                post_id=post_id,
                url=f"https://www.facebook.com/{post_id}",
                post_type=post_type,
                caption=content,
                posted_at=posted_at,
                likes=reactions,  # Facebook uses reactions instead of likes
                comments=comments,
                shares=shares,
                views=None,  # Not available in basic API
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse Facebook post data: {e}")
    
    async def refresh_access_token(self) -> str:
        """Refresh Facebook access token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/oauth/access_token"
                params = {
                    'grant_type': 'fb_exchange_token',
                    'client_id': self.app_id,
                    'client_secret': self.app_secret,
                    'fb_exchange_token': self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        new_token = data.get('access_token')
                        expires_in = data.get('expires_in')
                        
                        self.logger.info(f"Facebook access token refreshed, expires in {expires_in} seconds")
                        return new_token
                    else:
                        error_data = await response.json()
                        raise AuthenticationError(f"Failed to refresh Facebook token: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error refreshing Facebook token: {e}")
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get Facebook API rate limits and usage."""
        return {
            'platform': 'facebook',
            'rate_limit_per_hour': 200,
            'rate_limit_per_day': 4800,  # 200 * 24
            'current_usage': self.requests_made,
            'window_remaining': self.get_rate_limit_status()['window_remaining_seconds'],
            'endpoints': {
                'page_info': {'limit': 200, 'window': 3600},
                'page_posts': {'limit': 200, 'window': 3600},
                'page_insights': {'limit': 200, 'window': 3600, 'requires': 'page_access_token'},
                'search': {'limit': 200, 'window': 3600}
            },
            'notes': [
                'Rate limits are per app per user',
                'Page access token required for insights and some page data',
                'Business verification may be required for some features',
                'Different permissions affect available data',
                'Some metrics require page admin access'
            ]
        }