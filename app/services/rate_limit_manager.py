"""Rate limit management service for social media API requests."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
import logging

from app.models.rate_limit_tracker import RateLimitTracker, RateLimitStatus
from app.core.database import get_session

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int, platform: str):
        super().__init__(message)
        self.retry_after = retry_after
        self.platform = platform


class RateLimitManager:
    """Service for managing API rate limits across social media platforms."""
    
    def __init__(self, db: Session):
        self.db = db
        self._request_queue: Dict[str, List[Dict[str, Any]]] = {}
        self._processing_queue: Dict[str, bool] = {}
        
        # Default rate limits for each platform
        self.default_limits = {
            'instagram': {'requests': 200, 'window': 3600},  # 200 per hour
            'tiktok': {'requests': 100, 'window': 3600},     # 100 per hour
            'youtube': {'requests': 10000, 'window': 86400}, # 10K per day
            'twitter': {'requests': 300, 'window': 900},     # 300 per 15 min
            'facebook': {'requests': 200, 'window': 3600}    # 200 per hour
        }
    
    async def check_rate_limit(self, platform: str, endpoint: str = "default") -> bool:
        """Check if a request can be made without exceeding rate limits."""
        tracker = await self._get_or_create_tracker(platform, endpoint)
        
        # Check if window has expired
        if tracker.is_window_expired():
            tracker.reset_window()
            self.db.add(tracker)
            self.db.commit()
        
        return tracker.can_make_request()
    
    async def record_request(self, platform: str, endpoint: str = "default") -> bool:
        """Record a request and update rate limit status."""
        tracker = await self._get_or_create_tracker(platform, endpoint)
        
        # Check if window has expired
        if tracker.is_window_expired():
            tracker.reset_window()
        
        # Record the request
        success = tracker.record_request()
        
        # Update in database
        self.db.add(tracker)
        self.db.commit()
        
        if not success:
            logger.warning(
                f"Rate limit exceeded for {platform} ({endpoint}). "
                f"Used {tracker.requests_made}/{tracker.requests_limit} requests."
            )
        
        return success
    
    async def get_rate_limit_status(self, platform: str, endpoint: str = "default") -> Dict[str, Any]:
        """Get current rate limit status for a platform/endpoint."""
        tracker = await self._get_or_create_tracker(platform, endpoint)
        
        # Check if window has expired
        if tracker.is_window_expired():
            tracker.reset_window()
            self.db.add(tracker)
            self.db.commit()
        
        return {
            'platform': platform,
            'endpoint': endpoint,
            'requests_made': tracker.requests_made,
            'requests_limit': tracker.requests_limit,
            'requests_remaining': tracker.get_remaining_requests(),
            'window_start': tracker.window_start,
            'window_end': tracker.window_end,
            'reset_in_seconds': tracker.get_reset_time_seconds(),
            'usage_percentage': tracker.get_usage_percentage(),
            'status': tracker.status,
            'last_request_at': tracker.last_request_at
        }
    
    async def get_all_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limit status for all platforms."""
        statement = select(RateLimitTracker)
        trackers = self.db.exec(statement).all()
        
        result = {}
        for tracker in trackers:
            platform_key = f"{tracker.platform}_{tracker.endpoint}"
            
            # Check if window has expired
            if tracker.is_window_expired():
                tracker.reset_window()
                self.db.add(tracker)
            
            result[platform_key] = {
                'platform': tracker.platform,
                'endpoint': tracker.endpoint,
                'requests_made': tracker.requests_made,
                'requests_limit': tracker.requests_limit,
                'requests_remaining': tracker.get_remaining_requests(),
                'window_start': tracker.window_start,
                'window_end': tracker.window_end,
                'reset_in_seconds': tracker.get_reset_time_seconds(),
                'usage_percentage': tracker.get_usage_percentage(),
                'status': tracker.status,
                'last_request_at': tracker.last_request_at
            }
        
        # Commit any window resets
        self.db.commit()
        
        return result
    
    async def queue_request(
        self, 
        platform: str, 
        request_func, 
        *args, 
        endpoint: str = "default",
        priority: int = 5,
        **kwargs
    ) -> Any:
        """Queue a request to be processed when rate limits allow."""
        request_data = {
            'platform': platform,
            'endpoint': endpoint,
            'priority': priority,
            'func': request_func,
            'args': args,
            'kwargs': kwargs,
            'queued_at': datetime.utcnow(),
            'future': asyncio.Future()
        }
        
        # Add to queue
        queue_key = f"{platform}_{endpoint}"
        if queue_key not in self._request_queue:
            self._request_queue[queue_key] = []
        
        self._request_queue[queue_key].append(request_data)
        
        # Sort by priority (higher priority first)
        self._request_queue[queue_key].sort(key=lambda x: x['priority'], reverse=True)
        
        # Start processing queue if not already processing
        if not self._processing_queue.get(queue_key, False):
            asyncio.create_task(self._process_queue(queue_key))
        
        # Wait for result
        return await request_data['future']
    
    async def _process_queue(self, queue_key: str) -> None:
        """Process queued requests for a platform/endpoint."""
        self._processing_queue[queue_key] = True
        
        try:
            while queue_key in self._request_queue and self._request_queue[queue_key]:
                request_data = self._request_queue[queue_key][0]
                platform = request_data['platform']
                endpoint = request_data['endpoint']
                
                # Check if we can make the request
                if await self.check_rate_limit(platform, endpoint):
                    # Remove from queue
                    self._request_queue[queue_key].pop(0)
                    
                    try:
                        # Record the request
                        await self.record_request(platform, endpoint)
                        
                        # Execute the request
                        result = await request_data['func'](*request_data['args'], **request_data['kwargs'])
                        request_data['future'].set_result(result)
                        
                    except Exception as e:
                        request_data['future'].set_exception(e)
                else:
                    # Wait before checking again
                    tracker = await self._get_or_create_tracker(platform, endpoint)
                    wait_time = min(tracker.get_reset_time_seconds(), 60)  # Max 1 minute wait
                    
                    logger.info(f"Rate limit reached for {platform} ({endpoint}). Waiting {wait_time} seconds.")
                    await asyncio.sleep(wait_time)
        
        finally:
            self._processing_queue[queue_key] = False
    
    async def wait_for_rate_limit_reset(self, platform: str, endpoint: str = "default") -> int:
        """Wait for rate limit to reset and return wait time in seconds."""
        tracker = await self._get_or_create_tracker(platform, endpoint)
        
        if tracker.status != RateLimitStatus.EXCEEDED:
            return 0
        
        wait_time = tracker.get_reset_time_seconds()
        if wait_time > 0:
            logger.info(f"Waiting {wait_time} seconds for {platform} rate limit reset")
            await asyncio.sleep(wait_time)
        
        return wait_time
    
    async def reset_rate_limit(self, platform: str, endpoint: str = "default") -> None:
        """Manually reset rate limit for a platform/endpoint."""
        tracker = await self._get_or_create_tracker(platform, endpoint)
        tracker.reset_window()
        
        self.db.add(tracker)
        self.db.commit()
        
        logger.info(f"Rate limit manually reset for {platform} ({endpoint})")
    
    async def update_rate_limit(
        self, 
        platform: str, 
        requests_limit: int, 
        window_duration: int,
        endpoint: str = "default"
    ) -> None:
        """Update rate limit configuration for a platform/endpoint."""
        tracker = await self._get_or_create_tracker(platform, endpoint)
        
        tracker.requests_limit = requests_limit
        tracker.window_duration_seconds = window_duration
        
        # Reset window with new configuration
        tracker.reset_window()
        
        self.db.add(tracker)
        self.db.commit()
        
        logger.info(
            f"Rate limit updated for {platform} ({endpoint}): "
            f"{requests_limit} requests per {window_duration} seconds"
        )
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get status of all request queues."""
        status = {}
        
        for queue_key, requests in self._request_queue.items():
            if requests:
                status[queue_key] = {
                    'queue_length': len(requests),
                    'processing': self._processing_queue.get(queue_key, False),
                    'oldest_request': requests[0]['queued_at'] if requests else None,
                    'priorities': [req['priority'] for req in requests[:5]]  # First 5 priorities
                }
        
        return status
    
    async def clear_queue(self, platform: str, endpoint: str = "default") -> int:
        """Clear all queued requests for a platform/endpoint."""
        queue_key = f"{platform}_{endpoint}"
        
        if queue_key in self._request_queue:
            count = len(self._request_queue[queue_key])
            
            # Cancel all futures
            for request_data in self._request_queue[queue_key]:
                if not request_data['future'].done():
                    request_data['future'].cancel()
            
            # Clear queue
            del self._request_queue[queue_key]
            
            logger.info(f"Cleared {count} queued requests for {platform} ({endpoint})")
            return count
        
        return 0
    
    async def get_platform_statistics(self, platform: str, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for a platform over the last N days."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        statement = select(RateLimitTracker).where(
            and_(
                RateLimitTracker.platform == platform,
                RateLimitTracker.created_at >= since_date
            )
        )
        
        trackers = self.db.exec(statement).all()
        
        if not trackers:
            return {
                'platform': platform,
                'period_days': days,
                'total_requests': 0,
                'average_requests_per_day': 0,
                'peak_usage_percentage': 0,
                'rate_limit_hits': 0
            }
        
        total_requests = sum(tracker.requests_made for tracker in trackers)
        peak_usage = max(tracker.get_usage_percentage() for tracker in trackers)
        rate_limit_hits = sum(1 for tracker in trackers if tracker.status == RateLimitStatus.EXCEEDED)
        
        return {
            'platform': platform,
            'period_days': days,
            'total_requests': total_requests,
            'average_requests_per_day': total_requests / days,
            'peak_usage_percentage': peak_usage,
            'rate_limit_hits': rate_limit_hits,
            'endpoints': len(set(tracker.endpoint for tracker in trackers))
        }
    
    async def _get_or_create_tracker(self, platform: str, endpoint: str = "default") -> RateLimitTracker:
        """Get existing rate limit tracker or create a new one."""
        statement = select(RateLimitTracker).where(
            and_(
                RateLimitTracker.platform == platform,
                RateLimitTracker.endpoint == endpoint
            )
        )
        
        tracker = self.db.exec(statement).first()
        
        if not tracker:
            # Get default limits for platform
            limits = self.default_limits.get(platform, {'requests': 100, 'window': 3600})
            
            tracker = RateLimitTracker(
                platform=platform,
                endpoint=endpoint,
                requests_limit=limits['requests'],
                window_duration_seconds=limits['window']
            )
            
            self.db.add(tracker)
            self.db.commit()
            self.db.refresh(tracker)
        
        return tracker
    
    async def cleanup_old_trackers(self, days: int = 30) -> int:
        """Clean up old rate limit trackers."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        statement = select(RateLimitTracker).where(
            RateLimitTracker.created_at < cutoff_date
        )
        
        old_trackers = self.db.exec(statement).all()
        count = len(old_trackers)
        
        for tracker in old_trackers:
            self.db.delete(tracker)
        
        self.db.commit()
        
        logger.info(f"Cleaned up {count} old rate limit trackers")
        return count
    
    def get_recommended_limits(self, platform: str) -> Dict[str, Any]:
        """Get recommended rate limits for a platform."""
        recommendations = {
            'instagram': {
                'requests_per_hour': 200,
                'burst_limit': 50,
                'recommended_interval': 18,  # seconds between requests
                'notes': [
                    'Instagram Basic Display API limit',
                    'Consider user access token rotation',
                    'Business accounts may have higher limits'
                ]
            },
            'tiktok': {
                'requests_per_hour': 100,
                'burst_limit': 25,
                'recommended_interval': 36,  # seconds between requests
                'notes': [
                    'TikTok for Developers limit',
                    'Rate limits are per app, not per user',
                    'Business verification may increase limits'
                ]
            },
            'youtube': {
                'requests_per_day': 10000,
                'quota_cost_per_request': 1,
                'expensive_operations': ['search: 100 units'],
                'recommended_daily_budget': 8000,  # Leave buffer
                'notes': [
                    'Quota-based system, not time-based',
                    'Search operations are expensive (100 units)',
                    'Consider caching to reduce API calls'
                ]
            },
            'twitter': {
                'requests_per_15min': 300,
                'requests_per_hour': 1200,
                'burst_limit': 100,
                'recommended_interval': 3,  # seconds between requests
                'notes': [
                    'Twitter API v2 limits',
                    'Different endpoints have different limits',
                    'Academic Research access has higher limits'
                ]
            },
            'facebook': {
                'requests_per_hour': 200,
                'burst_limit': 50,
                'recommended_interval': 18,  # seconds between requests
                'notes': [
                    'Facebook Graph API limit',
                    'Page access tokens may have different limits',
                    'Business verification affects available features'
                ]
            }
        }
        
        return recommendations.get(platform, {
            'requests_per_hour': 100,
            'burst_limit': 25,
            'recommended_interval': 36,
            'notes': ['Default conservative limits']
        })