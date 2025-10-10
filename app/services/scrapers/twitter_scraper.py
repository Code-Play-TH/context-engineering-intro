"""Twitter scraper using Twitter API v2."""
import asyncio
import aiohttp
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .base_scraper import (
    BaseScraper, SocialMetrics, PostData, ScrapingError, 
    RateLimitError, AuthenticationError, PlatformError
)


class TwitterScraper(BaseScraper):
    """Twitter scraper using Twitter API v2."""
    
    def __init__(self, api_config: Dict[str, Any]):
        super().__init__("twitter", api_config)
        
        self.api_key = api_config.get('api_key')
        self.api_secret = api_config.get('api_secret')
        self.access_token = api_config.get('access_token')
        self.access_token_secret = api_config.get('access_token_secret')
        self.bearer_token = api_config.get('bearer_token')
        
        # Twitter API endpoints
        self.base_url = "https://api.twitter.com/2"
        
        # Rate limits: 300 requests per 15 minutes for most endpoints
        self.rate_limit = 300
        self.window_duration = 900  # 15 minutes
        
        if not (self.bearer_token or (self.api_key and self.api_secret)):
            raise ValueError("Twitter API credentials are incomplete")
    
    async def authenticate(self) -> bool:
        """Verify Twitter API credentials."""
        try:
            if self.bearer_token:
                return await self._authenticate_bearer_token()
            else:
                return await self._authenticate_oauth1()
                
        except Exception as e:
            self.logger.error(f"Twitter authentication failed: {e}")
            return False
    
    async def _authenticate_bearer_token(self) -> bool:
        """Authenticate using Bearer Token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/me"
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        user_data = data.get('data', {})
                        self.logger.info(f"Twitter authentication successful for user: {user_data.get('username')}")
                        return True
                    elif response.status == 401:
                        raise AuthenticationError("Invalid Twitter Bearer Token")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Twitter API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error during Twitter authentication: {e}")
    
    async def _authenticate_oauth1(self) -> bool:
        """Authenticate using OAuth 1.0a (not implemented in this example)."""
        # OAuth 1.0a implementation would be complex and require additional libraries
        # For now, we'll focus on Bearer Token authentication
        self.logger.warning("OAuth 1.0a authentication not implemented. Use Bearer Token instead.")
        return False
    
    async def get_user_metrics(self, handle: str) -> SocialMetrics:
        """Get Twitter user metrics."""
        handle = self.validate_handle(handle)
        
        # Get user info and recent tweets
        user_info = await self._get_user_info(handle)
        if not user_info:
            raise PlatformError(f"Twitter user not found: {handle}")
        
        user_id = user_info['id']
        recent_tweets = await self._get_user_tweets(user_id, limit=20)
        
        # Extract metrics from user info
        public_metrics = user_info.get('public_metrics', {})
        follower_count = public_metrics.get('followers_count', 0)
        following_count = public_metrics.get('following_count', 0)
        tweet_count = public_metrics.get('tweet_count', 0)
        listed_count = public_metrics.get('listed_count', 0)
        
        # Calculate engagement metrics from recent tweets
        if recent_tweets:
            avg_likes, avg_comments, avg_shares, avg_views = self.calculate_average_metrics(recent_tweets)
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
            post_count=tweet_count,
            engagement_rate=engagement_rate,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_shares=avg_shares,
            avg_views=avg_views,
            platform_specific={
                'user_id': user_id,
                'username': user_info.get('username'),
                'name': user_info.get('name'),
                'description': user_info.get('description'),
                'profile_image_url': user_info.get('profile_image_url'),
                'url': user_info.get('url'),
                'location': user_info.get('location'),
                'verified': user_info.get('verified', False),
                'protected': user_info.get('protected', False),
                'created_at': user_info.get('created_at'),
                'listed_count': listed_count,
                'pinned_tweet_id': user_info.get('pinned_tweet_id')
            }
        )
    
    async def get_recent_posts(self, handle: str, limit: int = 10) -> List[PostData]:
        """Get recent Twitter posts."""
        handle = self.validate_handle(handle)
        
        user_info = await self._get_user_info(handle)
        if not user_info:
            raise PlatformError(f"Twitter user not found: {handle}")
        
        user_id = user_info['id']
        return await self._get_user_tweets(user_id, limit=limit)
    
    async def get_post_metrics(self, post_id: str) -> PostData:
        """Get metrics for a specific Twitter tweet."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tweets/{post_id}"
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json'
                }
                
                params = {
                    'tweet.fields': 'created_at,text,public_metrics,context_annotations,entities,referenced_tweets',
                    'expansions': 'author_id'
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweet_data = data.get('data')
                        if tweet_data:
                            return self._parse_tweet_data(tweet_data)
                        else:
                            raise PlatformError(f"Twitter tweet not found: {post_id}")
                    elif response.status == 429:
                        raise RateLimitError("Twitter rate limit exceeded")
                    elif response.status == 404:
                        raise PlatformError(f"Twitter tweet not found: {post_id}")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Twitter API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Twitter tweet: {e}")
    
    async def _get_user_info(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get Twitter user information by username."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/by/username/{handle}"
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json'
                }
                
                params = {
                    'user.fields': 'created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified'
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data')
                    elif response.status == 429:
                        raise RateLimitError("Twitter rate limit exceeded")
                    elif response.status == 404:
                        return None
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Twitter API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Twitter user info: {e}")
    
    async def _get_user_tweets(self, user_id: str, limit: int = 10) -> List[PostData]:
        """Get recent tweets from a Twitter user."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/{user_id}/tweets"
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json'
                }
                
                params = {
                    'max_results': min(limit, 100),  # Twitter API limit
                    'tweet.fields': 'created_at,text,public_metrics,context_annotations,entities,referenced_tweets',
                    'exclude': 'retweets,replies'  # Get only original tweets
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweets = []
                        
                        for tweet in data.get('data', []):
                            try:
                                post = self._parse_tweet_data(tweet)
                                tweets.append(post)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse Twitter tweet: {e}")
                                continue
                        
                        return tweets
                    elif response.status == 429:
                        raise RateLimitError("Twitter rate limit exceeded")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Twitter API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error getting Twitter tweets: {e}")
    
    def _parse_tweet_data(self, tweet: Dict[str, Any]) -> PostData:
        """Parse Twitter API response into PostData."""
        try:
            # Parse timestamp
            created_at = tweet.get('created_at', '')
            if created_at:
                posted_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                posted_at = datetime.utcnow()
            
            # Extract text and hashtags/mentions
            text = tweet.get('text', '')
            
            # Extract entities
            entities = tweet.get('entities', {})
            hashtags = [tag['tag'].lower() for tag in entities.get('hashtags', [])]
            mentions = [mention['username'].lower() for mention in entities.get('mentions', [])]
            
            # Get public metrics
            public_metrics = tweet.get('public_metrics', {})
            
            tweet_id = tweet.get('id', '')
            
            return PostData(
                post_id=tweet_id,
                url=f"https://twitter.com/i/status/{tweet_id}",
                post_type='tweet',
                caption=text,
                posted_at=posted_at,
                likes=public_metrics.get('like_count', 0),
                comments=public_metrics.get('reply_count', 0),
                shares=public_metrics.get('retweet_count', 0),
                views=public_metrics.get('impression_count'),  # May not be available
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse Twitter tweet data: {e}")
    
    async def search_tweets(self, query: str, limit: int = 10) -> List[PostData]:
        """Search for tweets matching a query."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tweets/search/recent"
                headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json'
                }
                
                params = {
                    'query': query,
                    'max_results': min(limit, 100),
                    'tweet.fields': 'created_at,text,public_metrics,context_annotations,entities,referenced_tweets',
                    'expansions': 'author_id'
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweets = []
                        
                        for tweet in data.get('data', []):
                            try:
                                post = self._parse_tweet_data(tweet)
                                tweets.append(post)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse Twitter search result: {e}")
                                continue
                        
                        return tweets
                    elif response.status == 429:
                        raise RateLimitError("Twitter rate limit exceeded")
                    else:
                        error_data = await response.json()
                        raise PlatformError(f"Twitter API error: {error_data}")
                        
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error searching Twitter: {e}")
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get Twitter API rate limits and usage."""
        return {
            'platform': 'twitter',
            'rate_limit_per_15min': 300,
            'rate_limit_per_hour': 1200,  # 300 * 4
            'current_usage': self.requests_made,
            'window_remaining': self.get_rate_limit_status()['window_remaining_seconds'],
            'endpoints': {
                'users/me': {'limit': 75, 'window': 900},
                'users/by/username': {'limit': 300, 'window': 900},
                'users/{id}/tweets': {'limit': 1500, 'window': 900},
                'tweets/{id}': {'limit': 300, 'window': 900},
                'tweets/search/recent': {'limit': 450, 'window': 900}
            },
            'notes': [
                'Rate limits are per 15-minute window',
                'Different endpoints have different limits',
                'Bearer Token provides read-only access',
                'OAuth 1.0a required for write operations',
                'Academic Research access has higher limits'
            ]
        }