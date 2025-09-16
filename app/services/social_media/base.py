"""
Base social media service class providing common functionality.
All platform-specific services inherit from this base class.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for API calls."""
    calls_made: int = 0
    reset_time: datetime = None
    max_calls: int = 100
    window_seconds: int = 3600


class BaseSocialMediaService(ABC):
    """
    Abstract base class for social media API services.

    Provides common functionality:
    - Rate limiting
    - Error handling
    - Data transformation
    - Caching
    """

    def __init__(self):
        self.platform = "unknown"
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @abstractmethod
    async def get_user_profile(self, user_id: str, access_token: str) -> Dict[str, Any]:
        """
        Get user profile information from the platform.

        Args:
            user_id: Platform-specific user ID
            access_token: User or app access token

        Returns:
            Dict containing standardized user profile data
        """
        pass

    @abstractmethod
    async def get_user_media(
        self,
        user_id: str,
        access_token: str,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's media posts with pagination.

        Args:
            user_id: Platform-specific user ID
            access_token: User or app access token
            limit: Number of posts to retrieve
            after: Pagination cursor

        Returns:
            Dict containing media data and pagination info
        """
        pass

    @abstractmethod
    async def verify_content_match(
        self,
        content_data: Dict[str, Any],
        campaign_criteria: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Verify if content matches campaign criteria.

        Args:
            content_data: Platform content data
            campaign_criteria: Campaign matching criteria

        Returns:
            Tuple of (is_match, confidence_score, match_criteria)
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform name."""
        pass

    @abstractmethod
    def get_api_version(self) -> str:
        """Get API version."""
        pass

    async def get_rate_limit_status(self, access_token: str) -> RateLimitInfo:
        """
        Get current rate limit status for a token.

        Args:
            access_token: API access token

        Returns:
            Current rate limit information
        """
        return self.rate_limits.get(access_token, RateLimitInfo())

    async def update_rate_limit(
        self,
        access_token: str,
        calls_made: int,
        reset_time: datetime,
        max_calls: int = None
    ) -> None:
        """
        Update rate limit information for a token.

        Args:
            access_token: API access token
            calls_made: Number of calls made in current window
            reset_time: When the rate limit resets
            max_calls: Maximum calls allowed in window
        """
        if access_token not in self.rate_limits:
            self.rate_limits[access_token] = RateLimitInfo()

        rate_limit = self.rate_limits[access_token]
        rate_limit.calls_made = calls_made
        rate_limit.reset_time = reset_time

        if max_calls:
            rate_limit.max_calls = max_calls

    async def wait_for_rate_limit_reset(self, access_token: str) -> None:
        """
        Wait for rate limit to reset if necessary.

        Args:
            access_token: API access token
        """
        rate_limit = self.rate_limits.get(access_token)
        if not rate_limit or not rate_limit.reset_time:
            return

        now = datetime.utcnow()
        if rate_limit.calls_made >= rate_limit.max_calls and rate_limit.reset_time > now:
            wait_seconds = (rate_limit.reset_time - now).total_seconds()
            self.logger.info(f"Rate limit reached for {self.platform}. Waiting {wait_seconds} seconds.")
            await asyncio.sleep(wait_seconds)

    def extract_hashtags(self, text: str) -> List[str]:
        """
        Extract hashtags from text content.

        Args:
            text: Text content to parse

        Returns:
            List of hashtags (without # symbol)
        """
        import re
        if not text:
            return []

        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text.lower())
        return list(set(hashtags))  # Remove duplicates

    def extract_mentions(self, text: str) -> List[str]:
        """
        Extract user mentions from text content.

        Args:
            text: Text content to parse

        Returns:
            List of mentions (without @ symbol)
        """
        import re
        if not text:
            return []

        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text.lower())
        return list(set(mentions))  # Remove duplicates

    def calculate_engagement_rate(
        self,
        likes: int,
        comments: int,
        shares: int,
        followers: int
    ) -> float:
        """
        Calculate engagement rate.

        Args:
            likes: Number of likes
            comments: Number of comments
            shares: Number of shares
            followers: Number of followers

        Returns:
            Engagement rate as percentage
        """
        if followers == 0:
            return 0.0

        total_engagement = likes + comments + shares
        return (total_engagement / followers) * 100

    def standardize_media_type(self, platform_type: str) -> str:
        """
        Standardize media type across platforms.

        Args:
            platform_type: Platform-specific media type

        Returns:
            Standardized media type
        """
        type_mapping = {
            # Instagram
            "image": "post",
            "video": "video",
            "carousel_album": "carousel",
            "story": "story",

            # YouTube
            "upload": "video",
            "short": "short",
            "live": "live",

            # TikTok
            "photo": "post",

            # Twitter
            "photo": "post",
            "animated_gif": "video",

            # Facebook
            "link": "post",
            "status": "post",
            "photo": "post",
        }

        return type_mapping.get(platform_type.lower(), "post")

    def parse_datetime(self, date_string: str) -> Optional[datetime]:
        """
        Parse datetime string from various platform formats.

        Args:
            date_string: Date string from platform API

        Returns:
            Parsed datetime object or None
        """
        if not date_string:
            return None

        # Common datetime formats from social media APIs
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
            "%Y-%m-%dT%H:%M:%SZ",   # ISO format UTC
            "%Y-%m-%d %H:%M:%S",    # Simple format
            "%a %b %d %H:%M:%S %z %Y",  # Twitter format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        # Try parsing as timestamp
        try:
            timestamp = float(date_string)
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            pass

        self.logger.warning(f"Could not parse datetime: {date_string}")
        return None

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text content for storage.

        Args:
            text: Raw text content

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Remove control characters
        import re
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        return text.strip()

    def validate_content_criteria(self, criteria: Dict[str, Any]) -> List[str]:
        """
        Validate campaign content criteria.

        Args:
            criteria: Content matching criteria

        Returns:
            List of validation errors
        """
        errors = []

        required_fields = ["required_hashtags", "keywords", "start_date", "end_date"]
        for field in required_fields:
            if field not in criteria:
                errors.append(f"Missing required field: {field}")

        # Validate date formats
        for date_field in ["start_date", "end_date"]:
            if date_field in criteria and criteria[date_field]:
                if not isinstance(criteria[date_field], (datetime, str)):
                    errors.append(f"Invalid {date_field} format")

        # Validate hashtags
        if "required_hashtags" in criteria:
            hashtags = criteria["required_hashtags"]
            if not isinstance(hashtags, list):
                errors.append("required_hashtags must be a list")
            elif not hashtags:
                errors.append("At least one hashtag is required")

        return errors

    def build_error_response(self, error_message: str, error_code: str = None) -> Dict[str, Any]:
        """
        Build standardized error response.

        Args:
            error_message: Error message
            error_code: Platform-specific error code

        Returns:
            Standardized error response
        """
        return {
            "success": False,
            "error": {
                "message": error_message,
                "code": error_code,
                "platform": self.platform,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    def build_success_response(self, data: Any, message: str = "Success") -> Dict[str, Any]:
        """
        Build standardized success response.

        Args:
            data: Response data
            message: Success message

        Returns:
            Standardized success response
        """
        return {
            "success": True,
            "message": message,
            "data": data,
            "platform": self.platform,
            "timestamp": datetime.utcnow().isoformat()
        }