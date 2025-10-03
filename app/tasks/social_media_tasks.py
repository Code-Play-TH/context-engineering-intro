"""
Celery tasks for social media data ingestion.

This module contains background tasks for fetching and syncing data
from various social media platforms (Instagram, TikTok, YouTube, etc.).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from celery import shared_task
import logging

from app.models.kol import KOL
from app.models.campaign_content import CampaignContent
from app.utils.metrics_normalization import normalize_metrics, Platform
from app.utils.datetime_utils import get_current_utc

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_kol_profile(self, kol_id: int, platform: str) -> Dict[str, Any]:
    """
    Sync KOL profile data from social media platform.

    Args:
        kol_id (int): KOL database ID.
        platform (str): Platform name (instagram, tiktok, youtube, etc.).

    Returns:
        Dict[str, Any]: Sync result with updated metrics.

    Raises:
        Exception: If sync fails after retries.
    """
    try:
        logger.info(f"Starting profile sync for KOL {kol_id} on {platform}")

        # In production, this would call actual API
        # For now, simulating with placeholder

        from app.core.database import get_db_session
        db = next(get_db_session())

        kol = db.query(KOL).filter(KOL.id == kol_id).first()

        if not kol:
            raise ValueError(f"KOL not found: {kol_id}")

        # Fetch data from platform API
        raw_data = _fetch_platform_profile(platform, kol.username)

        # Normalize metrics
        normalized = normalize_metrics(Platform(platform), raw_data)

        # Update KOL record
        kol.followers_count = normalized.get("followers", kol.followers_count)
        kol.engagement_rate = normalized.get("engagement_rate", kol.engagement_rate)
        kol.posts_count = normalized.get("posts_count", kol.posts_count)
        kol.last_sync_at = get_current_utc()

        # Update metadata
        if not kol.metadata:
            kol.metadata = {}
        kol.metadata["last_sync"] = get_current_utc().isoformat()
        kol.metadata["raw_metrics"] = raw_data

        db.commit()

        logger.info(f"Profile sync completed for KOL {kol_id}")

        return {
            "success": True,
            "kol_id": kol_id,
            "platform": platform,
            "followers_count": kol.followers_count,
            "engagement_rate": kol.engagement_rate,
            "synced_at": kol.last_sync_at.isoformat()
        }

    except Exception as exc:
        logger.error(f"Error syncing KOL {kol_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def sync_content_metrics(self, content_id: int) -> Dict[str, Any]:
    """
    Sync content metrics from social media platform.

    Args:
        content_id (int): Content database ID.

    Returns:
        Dict[str, Any]: Sync result with updated metrics.

    Raises:
        Exception: If sync fails after retries.
    """
    try:
        logger.info(f"Starting metrics sync for content {content_id}")

        from app.core.database import get_db_session
        db = next(get_db_session())

        content = db.query(CampaignContent).filter(
            CampaignContent.id == content_id
        ).first()

        if not content:
            raise ValueError(f"Content not found: {content_id}")

        if not content.content_url:
            raise ValueError(f"Content URL not available for {content_id}")

        # Fetch metrics from platform
        raw_metrics = _fetch_content_metrics(
            content.platform,
            content.content_url
        )

        # Normalize metrics
        normalized = normalize_metrics(
            Platform(content.platform),
            raw_metrics
        )

        # Update content record
        content.reach = normalized.get("reach", content.reach)
        content.impressions = normalized.get("impressions", content.impressions)
        content.engagement_rate = normalized.get("engagement_rate", content.engagement_rate)

        # Update detailed metrics
        if not content.metrics:
            content.metrics = {}
        content.metrics.update(normalized)
        content.last_metrics_update = get_current_utc()

        db.commit()

        logger.info(f"Metrics sync completed for content {content_id}")

        return {
            "success": True,
            "content_id": content_id,
            "reach": content.reach,
            "engagement_rate": content.engagement_rate,
            "synced_at": content.last_metrics_update.isoformat()
        }

    except Exception as exc:
        logger.error(f"Error syncing content {content_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def bulk_sync_kol_profiles(kol_ids: List[int]) -> Dict[str, Any]:
    """
    Bulk sync multiple KOL profiles.

    Args:
        kol_ids (List[int]): List of KOL IDs to sync.

    Returns:
        Dict[str, Any]: Bulk sync results.
    """
    logger.info(f"Starting bulk sync for {len(kol_ids)} KOLs")

    results = {
        "total": len(kol_ids),
        "success": 0,
        "failed": 0,
        "failed_ids": []
    }

    from app.core.database import get_db_session
    db = next(get_db_session())

    for kol_id in kol_ids:
        try:
            kol = db.query(KOL).filter(KOL.id == kol_id).first()
            if kol:
                # Trigger individual sync task
                sync_kol_profile.delay(kol_id, kol.platform)
                results["success"] += 1
        except Exception as e:
            logger.error(f"Failed to trigger sync for KOL {kol_id}: {e}")
            results["failed"] += 1
            results["failed_ids"].append(kol_id)

    logger.info(f"Bulk sync triggered: {results['success']} successful, {results['failed']} failed")

    return results


@shared_task
def bulk_sync_campaign_content(campaign_id: int) -> Dict[str, Any]:
    """
    Sync all content for a campaign.

    Args:
        campaign_id (int): Campaign ID.

    Returns:
        Dict[str, Any]: Bulk sync results.
    """
    logger.info(f"Starting bulk content sync for campaign {campaign_id}")

    from app.core.database import get_db_session
    from app.models.campaign_content import ContentStatus
    db = next(get_db_session())

    # Get all published content for campaign
    content_list = db.query(CampaignContent).filter(
        CampaignContent.campaign_id == campaign_id,
        CampaignContent.status == ContentStatus.PUBLISHED
    ).all()

    results = {
        "campaign_id": campaign_id,
        "total_content": len(content_list),
        "synced": 0,
        "failed": 0
    }

    for content in content_list:
        try:
            sync_content_metrics.delay(content.id)
            results["synced"] += 1
        except Exception as e:
            logger.error(f"Failed to trigger sync for content {content.id}: {e}")
            results["failed"] += 1

    logger.info(f"Campaign content sync triggered: {results['synced']} tasks queued")

    return results


@shared_task
def scheduled_sync_all_kols() -> Dict[str, Any]:
    """
    Scheduled task to sync all active KOLs.
    Typically run daily or weekly.

    Returns:
        Dict[str, Any]: Sync summary.
    """
    logger.info("Starting scheduled sync for all KOLs")

    from app.core.database import get_db_session
    db = next(get_db_session())

    # Get KOLs that need syncing (last sync > 24 hours ago or never synced)
    cutoff_time = get_current_utc() - timedelta(hours=24)

    kols = db.query(KOL).filter(
        (KOL.last_sync_at < cutoff_time) | (KOL.last_sync_at == None)
    ).all()

    kol_ids = [kol.id for kol in kols]

    if kol_ids:
        result = bulk_sync_kol_profiles(kol_ids)
        logger.info(f"Scheduled sync completed: {result['success']} KOLs queued")
        return result
    else:
        logger.info("No KOLs need syncing")
        return {"message": "No KOLs need syncing", "total": 0}


@shared_task
def scheduled_sync_recent_content() -> Dict[str, Any]:
    """
    Scheduled task to sync recently published content.
    Typically run every few hours.

    Returns:
        Dict[str, Any]: Sync summary.
    """
    logger.info("Starting scheduled sync for recent content")

    from app.core.database import get_db_session
    from app.models.campaign_content import ContentStatus
    db = next(get_db_session())

    # Get content published in last 7 days
    cutoff_date = get_current_utc() - timedelta(days=7)

    content_list = db.query(CampaignContent).filter(
        CampaignContent.status == ContentStatus.PUBLISHED,
        CampaignContent.published_at >= cutoff_date
    ).all()

    results = {
        "total_content": len(content_list),
        "synced": 0,
        "failed": 0
    }

    for content in content_list:
        try:
            sync_content_metrics.delay(content.id)
            results["synced"] += 1
        except Exception as e:
            logger.error(f"Failed to trigger sync for content {content.id}: {e}")
            results["failed"] += 1

    logger.info(f"Recent content sync triggered: {results['synced']} tasks queued")

    return results


# Helper functions (would be replaced with actual API calls)

def _fetch_platform_profile(platform: str, username: str) -> Dict[str, Any]:
    """
    Fetch profile data from platform API.

    Note: This is a placeholder. In production, integrate with:
    - Instagram Graph API
    - TikTok Business API
    - YouTube Data API v3
    - Twitter API v2
    - Facebook Graph API

    Args:
        platform (str): Platform name.
        username (str): Username/handle.

    Returns:
        Dict[str, Any]: Raw profile data.
    """
    logger.info(f"Fetching profile data for {username} on {platform}")

    # Placeholder - would call actual API
    # Example for Instagram:
    # response = instagram_api.get_user_profile(username)
    # return response.json()

    return {
        "followers_count": 50000,
        "following_count": 500,
        "posts_count": 150,
        "engagement_rate": 3.5,
        "avg_likes": 1500,
        "avg_comments": 250
    }


def _fetch_content_metrics(platform: str, content_url: str) -> Dict[str, Any]:
    """
    Fetch content metrics from platform API.

    Args:
        platform (str): Platform name.
        content_url (str): Content URL.

    Returns:
        Dict[str, Any]: Raw content metrics.
    """
    logger.info(f"Fetching metrics for {content_url} on {platform}")

    # Placeholder - would call actual API
    # Example for Instagram:
    # media_id = extract_media_id(content_url)
    # response = instagram_api.get_media_insights(media_id)
    # return response.json()

    return {
        "reach": 10000,
        "impressions": 15000,
        "likes": 800,
        "comments": 120,
        "shares": 50,
        "saves": 150,
        "engagement_count": 1120
    }


@shared_task
def check_rate_limits(platform: str) -> Dict[str, Any]:
    """
    Check and monitor API rate limits for platform.

    Args:
        platform (str): Platform name.

    Returns:
        Dict[str, Any]: Rate limit status.
    """
    logger.info(f"Checking rate limits for {platform}")

    # Placeholder - would check actual rate limit headers/endpoints
    # Most platforms include rate limit info in API response headers

    return {
        "platform": platform,
        "limit": 200,
        "remaining": 150,
        "reset_at": (get_current_utc() + timedelta(hours=1)).isoformat()
    }


@shared_task(bind=True, max_retries=5)
def retry_failed_sync(self, sync_type: str, entity_id: int) -> Dict[str, Any]:
    """
    Retry failed sync operations with exponential backoff.

    Args:
        sync_type (str): Type of sync (profile or content).
        entity_id (int): Entity ID to retry.

    Returns:
        Dict[str, Any]: Retry result.
    """
    try:
        if sync_type == "profile":
            from app.core.database import get_db_session
            db = next(get_db_session())
            kol = db.query(KOL).filter(KOL.id == entity_id).first()
            if kol:
                return sync_kol_profile(entity_id, kol.platform)

        elif sync_type == "content":
            return sync_content_metrics(entity_id)

        else:
            raise ValueError(f"Unknown sync type: {sync_type}")

    except Exception as exc:
        logger.error(f"Retry failed for {sync_type} {entity_id}: {exc}")
        # Exponential backoff: 5min, 10min, 20min, 40min, 80min
        retry_delay = 300 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=retry_delay)
