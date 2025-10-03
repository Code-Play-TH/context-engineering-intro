"""
Metrics normalization utilities for social media platforms.

This module provides functions to normalize metrics from different
social media platforms into a standardized format for comparison
and analytics.
"""

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Social media platforms."""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"


class StandardMetric(str, Enum):
    """Standardized metric names across all platforms."""

    # Profile/Account Metrics
    FOLLOWERS = "followers"
    FOLLOWING = "following"
    TOTAL_POSTS = "total_posts"
    PROFILE_VIEWS = "profile_views"

    # Content Metrics
    VIEWS = "views"
    IMPRESSIONS = "impressions"
    REACH = "reach"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    CLICKS = "clicks"

    # Engagement Metrics (calculated)
    ENGAGEMENT_RATE = "engagement_rate"
    ENGAGEMENT_COUNT = "engagement_count"

    # Video-specific
    VIDEO_VIEWS = "video_views"
    VIDEO_WATCH_TIME = "video_watch_time"
    VIDEO_COMPLETION_RATE = "video_completion_rate"

    # Performance
    CPM = "cpm"  # Cost per thousand impressions
    CPE = "cpe"  # Cost per engagement
    CPC = "cpc"  # Cost per click
    CPV = "cpv"  # Cost per view


# Platform-specific metric mappings to standard metrics

INSTAGRAM_METRIC_MAP = {
    # Profile metrics
    "follower_count": StandardMetric.FOLLOWERS,
    "followers_count": StandardMetric.FOLLOWERS,
    "following_count": StandardMetric.FOLLOWING,
    "media_count": StandardMetric.TOTAL_POSTS,

    # Content metrics
    "impressions": StandardMetric.IMPRESSIONS,
    "reach": StandardMetric.REACH,
    "likes": StandardMetric.LIKES,
    "like_count": StandardMetric.LIKES,
    "comments": StandardMetric.COMMENTS,
    "comments_count": StandardMetric.COMMENTS,
    "shares": StandardMetric.SHARES,
    "saved": StandardMetric.SAVES,
    "saves": StandardMetric.SAVES,

    # Engagement
    "engagement": StandardMetric.ENGAGEMENT_COUNT,

    # Video
    "video_views": StandardMetric.VIDEO_VIEWS,
    "plays": StandardMetric.VIDEO_VIEWS,
}

FACEBOOK_METRIC_MAP = {
    # Profile metrics
    "page_fans": StandardMetric.FOLLOWERS,
    "page_fan_count": StandardMetric.FOLLOWERS,
    "page_views_total": StandardMetric.PROFILE_VIEWS,

    # Content metrics
    "post_impressions": StandardMetric.IMPRESSIONS,
    "post_reach": StandardMetric.REACH,
    "post_reactions_like_total": StandardMetric.LIKES,
    "post_comments": StandardMetric.COMMENTS,
    "post_shares": StandardMetric.SHARES,
    "post_clicks": StandardMetric.CLICKS,

    # Engagement
    "post_engaged_users": StandardMetric.ENGAGEMENT_COUNT,
    "post_engagements": StandardMetric.ENGAGEMENT_COUNT,

    # Video
    "post_video_views": StandardMetric.VIDEO_VIEWS,
    "video_views": StandardMetric.VIDEO_VIEWS,
    "post_video_avg_time_watched": StandardMetric.VIDEO_WATCH_TIME,
}

YOUTUBE_METRIC_MAP = {
    # Profile metrics
    "subscriberCount": StandardMetric.FOLLOWERS,
    "subscriber_count": StandardMetric.FOLLOWERS,
    "viewCount": StandardMetric.PROFILE_VIEWS,
    "videoCount": StandardMetric.TOTAL_POSTS,

    # Content metrics (video)
    "views": StandardMetric.VIEWS,
    "view_count": StandardMetric.VIEWS,
    "likeCount": StandardMetric.LIKES,
    "like_count": StandardMetric.LIKES,
    "commentCount": StandardMetric.COMMENTS,
    "comment_count": StandardMetric.COMMENTS,
    "shareCount": StandardMetric.SHARES,

    # Video specific
    "averageViewDuration": StandardMetric.VIDEO_WATCH_TIME,
    "estimatedMinutesWatched": StandardMetric.VIDEO_WATCH_TIME,
}

TIKTOK_METRIC_MAP = {
    # Profile metrics
    "follower_count": StandardMetric.FOLLOWERS,
    "following_count": StandardMetric.FOLLOWING,
    "video_count": StandardMetric.TOTAL_POSTS,
    "profile_view_count": StandardMetric.PROFILE_VIEWS,

    # Content metrics
    "view_count": StandardMetric.VIEWS,
    "play_count": StandardMetric.VIDEO_VIEWS,
    "like_count": StandardMetric.LIKES,
    "comment_count": StandardMetric.COMMENTS,
    "share_count": StandardMetric.SHARES,

    # Engagement
    "engagement_count": StandardMetric.ENGAGEMENT_COUNT,
}

TWITTER_METRIC_MAP = {
    # Profile metrics
    "followers_count": StandardMetric.FOLLOWERS,
    "following_count": StandardMetric.FOLLOWING,
    "tweet_count": StandardMetric.TOTAL_POSTS,

    # Content metrics
    "impressions": StandardMetric.IMPRESSIONS,
    "impression_count": StandardMetric.IMPRESSIONS,
    "like_count": StandardMetric.LIKES,
    "reply_count": StandardMetric.COMMENTS,
    "retweet_count": StandardMetric.SHARES,
    "quote_count": StandardMetric.SHARES,
    "url_link_clicks": StandardMetric.CLICKS,

    # Engagement
    "engagement_count": StandardMetric.ENGAGEMENT_COUNT,
}

PLATFORM_METRIC_MAPS = {
    Platform.INSTAGRAM: INSTAGRAM_METRIC_MAP,
    Platform.FACEBOOK: FACEBOOK_METRIC_MAP,
    Platform.YOUTUBE: YOUTUBE_METRIC_MAP,
    Platform.TIKTOK: TIKTOK_METRIC_MAP,
    Platform.TWITTER: TWITTER_METRIC_MAP,
}


def normalize_metrics(
    platform: Platform,
    raw_metrics: Dict[str, Any]
) -> Dict[StandardMetric, Any]:
    """
    Normalize platform-specific metrics to standard format.

    Args:
        platform (Platform): The social media platform.
        raw_metrics (Dict[str, Any]): Raw metrics from the platform.

    Returns:
        Dict[StandardMetric, Any]: Normalized metrics.

    Example:
        >>> raw = {"like_count": 1000, "comment_count": 50}
        >>> normalize_metrics(Platform.INSTAGRAM, raw)
        {StandardMetric.LIKES: 1000, StandardMetric.COMMENTS: 50}
    """
    metric_map = PLATFORM_METRIC_MAPS.get(platform, {})
    normalized = {}

    for raw_key, raw_value in raw_metrics.items():
        # Map to standard metric
        standard_metric = metric_map.get(raw_key)

        if standard_metric:
            normalized[standard_metric] = raw_value
        else:
            # Log unmapped metrics for debugging
            logger.debug(f"Unmapped metric from {platform}: {raw_key} = {raw_value}")

    return normalized


def calculate_engagement_rate(
    engagement_count: int,
    followers: int,
    reach: Optional[int] = None
) -> float:
    """
    Calculate engagement rate.

    Formula:
    - If reach is available: (engagement_count / reach) * 100
    - Otherwise: (engagement_count / followers) * 100

    Args:
        engagement_count (int): Total engagements (likes + comments + shares).
        followers (int): Follower count.
        reach (Optional[int]): Reach (impressions that reached unique users).

    Returns:
        float: Engagement rate as percentage.

    Example:
        >>> calculate_engagement_rate(150, 10000)
        1.5
    """
    if reach and reach > 0:
        return (engagement_count / reach) * 100
    elif followers > 0:
        return (engagement_count / followers) * 100
    return 0.0


def calculate_engagement_count(metrics: Dict[StandardMetric, Any]) -> int:
    """
    Calculate total engagement count from metrics.

    Engagement = Likes + Comments + Shares + Saves

    Args:
        metrics (Dict[StandardMetric, Any]): Normalized metrics.

    Returns:
        int: Total engagement count.
    """
    return sum([
        metrics.get(StandardMetric.LIKES, 0),
        metrics.get(StandardMetric.COMMENTS, 0),
        metrics.get(StandardMetric.SHARES, 0),
        metrics.get(StandardMetric.SAVES, 0),
    ])


def enrich_metrics(metrics: Dict[StandardMetric, Any]) -> Dict[StandardMetric, Any]:
    """
    Enrich normalized metrics with calculated fields.

    Adds:
    - engagement_count (if not present)
    - engagement_rate (if possible)

    Args:
        metrics (Dict[StandardMetric, Any]): Normalized metrics.

    Returns:
        Dict[StandardMetric, Any]: Enriched metrics.
    """
    enriched = metrics.copy()

    # Calculate engagement count if not present
    if StandardMetric.ENGAGEMENT_COUNT not in enriched:
        enriched[StandardMetric.ENGAGEMENT_COUNT] = calculate_engagement_count(enriched)

    # Calculate engagement rate if possible
    engagement_count = enriched.get(StandardMetric.ENGAGEMENT_COUNT, 0)
    followers = enriched.get(StandardMetric.FOLLOWERS, 0)
    reach = enriched.get(StandardMetric.REACH)

    if engagement_count and followers:
        enriched[StandardMetric.ENGAGEMENT_RATE] = calculate_engagement_rate(
            engagement_count,
            followers,
            reach
        )

    return enriched


def normalize_and_enrich(
    platform: Platform,
    raw_metrics: Dict[str, Any]
) -> Dict[StandardMetric, Any]:
    """
    Normalize and enrich metrics in one step.

    Args:
        platform (Platform): The social media platform.
        raw_metrics (Dict[str, Any]): Raw metrics from the platform.

    Returns:
        Dict[StandardMetric, Any]: Normalized and enriched metrics.
    """
    normalized = normalize_metrics(platform, raw_metrics)
    return enrich_metrics(normalized)


def compare_metrics(
    metrics_a: Dict[StandardMetric, Any],
    metrics_b: Dict[StandardMetric, Any]
) -> Dict[StandardMetric, Dict[str, Any]]:
    """
    Compare two sets of metrics.

    Args:
        metrics_a (Dict[StandardMetric, Any]): First metrics set (e.g., current).
        metrics_b (Dict[StandardMetric, Any]): Second metrics set (e.g., previous).

    Returns:
        Dict[StandardMetric, Dict[str, Any]]: Comparison results.

    Example:
        >>> current = {StandardMetric.FOLLOWERS: 1100}
        >>> previous = {StandardMetric.FOLLOWERS: 1000}
        >>> compare_metrics(current, previous)
        {
            StandardMetric.FOLLOWERS: {
                "current": 1100,
                "previous": 1000,
                "change": 100,
                "change_pct": 10.0
            }
        }
    """
    comparison = {}
    all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())

    for metric in all_metrics:
        value_a = metrics_a.get(metric, 0)
        value_b = metrics_b.get(metric, 0)

        # Handle numeric values only
        if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
            change = value_a - value_b
            change_pct = (change / value_b * 100) if value_b != 0 else 0

            comparison[metric] = {
                "current": value_a,
                "previous": value_b,
                "change": change,
                "change_pct": round(change_pct, 2)
            }

    return comparison


def aggregate_metrics(
    metrics_list: list[Dict[StandardMetric, Any]],
    method: str = "sum"
) -> Dict[StandardMetric, Any]:
    """
    Aggregate multiple metrics sets.

    Args:
        metrics_list (list[Dict[StandardMetric, Any]]): List of metrics to aggregate.
        method (str): Aggregation method - "sum", "avg", "max", "min".

    Returns:
        Dict[StandardMetric, Any]: Aggregated metrics.

    Example:
        >>> metrics = [
        ...     {StandardMetric.VIEWS: 1000, StandardMetric.LIKES: 50},
        ...     {StandardMetric.VIEWS: 1500, StandardMetric.LIKES: 75}
        ... ]
        >>> aggregate_metrics(metrics, method="sum")
        {StandardMetric.VIEWS: 2500, StandardMetric.LIKES: 125}
    """
    if not metrics_list:
        return {}

    # Collect all metric keys
    all_metrics = set()
    for metrics in metrics_list:
        all_metrics.update(metrics.keys())

    aggregated = {}

    for metric in all_metrics:
        values = [m.get(metric, 0) for m in metrics_list if isinstance(m.get(metric), (int, float))]

        if not values:
            continue

        if method == "sum":
            aggregated[metric] = sum(values)
        elif method == "avg":
            aggregated[metric] = sum(values) / len(values)
        elif method == "max":
            aggregated[metric] = max(values)
        elif method == "min":
            aggregated[metric] = min(values)
        else:
            logger.warning(f"Unknown aggregation method: {method}. Using sum.")
            aggregated[metric] = sum(values)

    return aggregated


def metrics_to_dict(
    metrics: Dict[StandardMetric, Any],
    include_enum_values: bool = False
) -> Dict[str, Any]:
    """
    Convert StandardMetric enum keys to string keys for JSON serialization.

    Args:
        metrics (Dict[StandardMetric, Any]): Metrics with enum keys.
        include_enum_values (bool): If True, use enum values; otherwise use enum names.

    Returns:
        Dict[str, Any]: Metrics with string keys.
    """
    if include_enum_values:
        return {k.value: v for k, v in metrics.items()}
    else:
        return {k.name: v for k, v in metrics.items()}


def dict_to_metrics(data: Dict[str, Any]) -> Dict[StandardMetric, Any]:
    """
    Convert string keys back to StandardMetric enum keys.

    Args:
        data (Dict[str, Any]): Metrics with string keys.

    Returns:
        Dict[StandardMetric, Any]: Metrics with enum keys.
    """
    metrics = {}
    for key, value in data.items():
        try:
            # Try to get enum by name
            metric = StandardMetric[key]
            metrics[metric] = value
        except KeyError:
            # Try to get enum by value
            try:
                metric = StandardMetric(key)
                metrics[metric] = value
            except ValueError:
                logger.warning(f"Unknown metric key: {key}")

    return metrics
