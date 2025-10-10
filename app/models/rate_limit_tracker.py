"""Rate limit tracker model for managing social media API rate limits."""
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum


class RateLimitStatus(str, Enum):
    """Rate limit status options."""
    OK = "ok"
    WARNING = "warning"  # 80% of limit reached
    EXCEEDED = "exceeded"
    RESET = "reset"


class RateLimitTracker(SQLModel, table=True):
    """Model for tracking API rate limits across social media platforms."""
    __tablename__ = "rate_limit_trackers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(index=True)  # instagram, tiktok, youtube, twitter, facebook
    endpoint: str = Field(default="default")  # Specific API endpoint if needed
    
    # Rate limit configuration
    requests_limit: int = Field(default=100)  # Max requests per window
    window_duration_seconds: int = Field(default=3600)  # Window duration (1 hour default)
    
    # Current usage
    requests_made: int = Field(default=0)
    window_start: datetime = Field(default_factory=datetime.utcnow, index=True)
    window_end: datetime = Field(index=True)
    
    # Status tracking
    status: RateLimitStatus = Field(default=RateLimitStatus.OK)
    last_request_at: Optional[datetime] = Field(default=None)
    reset_at: Optional[datetime] = Field(default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.window_end:
            self.window_end = self.window_start + timedelta(seconds=self.window_duration_seconds)
    
    def is_window_expired(self) -> bool:
        """Check if current rate limit window has expired."""
        return datetime.utcnow() >= self.window_end
    
    def reset_window(self) -> None:
        """Reset the rate limit window."""
        now = datetime.utcnow()
        self.window_start = now
        self.window_end = now + timedelta(seconds=self.window_duration_seconds)
        self.requests_made = 0
        self.status = RateLimitStatus.OK
        self.reset_at = now
        self.updated_at = now
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding limits."""
        if self.is_window_expired():
            self.reset_window()
            return True
        
        return self.requests_made < self.requests_limit
    
    def record_request(self) -> bool:
        """Record a new request and update status. Returns True if request was allowed."""
        if self.is_window_expired():
            self.reset_window()
        
        if self.requests_made >= self.requests_limit:
            self.status = RateLimitStatus.EXCEEDED
            return False
        
        self.requests_made += 1
        self.last_request_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Update status based on usage
        usage_percentage = (self.requests_made / self.requests_limit) * 100
        
        if usage_percentage >= 100:
            self.status = RateLimitStatus.EXCEEDED
        elif usage_percentage >= 80:
            self.status = RateLimitStatus.WARNING
        else:
            self.status = RateLimitStatus.OK
        
        return True
    
    def get_remaining_requests(self) -> int:
        """Get number of remaining requests in current window."""
        if self.is_window_expired():
            return self.requests_limit
        
        return max(0, self.requests_limit - self.requests_made)
    
    def get_reset_time_seconds(self) -> int:
        """Get seconds until rate limit window resets."""
        if self.is_window_expired():
            return 0
        
        return int((self.window_end - datetime.utcnow()).total_seconds())
    
    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of limit."""
        if self.requests_limit == 0:
            return 0.0
        
        if self.is_window_expired():
            return 0.0
        
        return (self.requests_made / self.requests_limit) * 100
    
    @classmethod
    def get_default_limits(cls) -> dict:
        """Get default rate limits for each platform."""
        return {
            "instagram": {"requests": 200, "window": 3600},  # 200 per hour
            "tiktok": {"requests": 100, "window": 3600},     # 100 per hour
            "youtube": {"requests": 10000, "window": 86400}, # 10K per day
            "twitter": {"requests": 300, "window": 900},     # 300 per 15 min
            "facebook": {"requests": 200, "window": 3600}    # 200 per hour
        }