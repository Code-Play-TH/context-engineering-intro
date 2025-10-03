"""
Search service for KOLs and Campaigns.

This module provides advanced search functionality with multiple filters,
sorting, and pagination.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.kol import KOL
from app.models.campaign import Campaign
from app.utils.filter_utils import (
    QueryBuilder,
    FilterBuilder,
    FilterOperator,
    SortOrder,
    apply_search
)
import logging

logger = logging.getLogger(__name__)


class KOLSearchService:
    """
    Service for searching and filtering KOLs.

    Supports:
    - Full-text search
    - Platform filtering
    - Follower count ranges
    - Engagement rate ranges
    - Verification status
    - Niche/category filtering
    - Multiple social platforms
    """

    def __init__(self, db: Session):
        """
        Initialize search service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def search_kols(
        self,
        # Search
        search_term: Optional[str] = None,

        # Filters
        platforms: Optional[List[str]] = None,
        min_followers: Optional[int] = None,
        max_followers: Optional[int] = None,
        min_engagement_rate: Optional[float] = None,
        max_engagement_rate: Optional[float] = None,
        verified_only: Optional[bool] = None,
        niches: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        min_posts: Optional[int] = None,

        # Sorting
        sort_by: str = "followers_count",
        sort_order: str = "desc",

        # Pagination
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Search KOLs with advanced filters.

        Args:
            search_term (Optional[str]): Search term for name/bio/tags.
            platforms (Optional[List[str]]): Filter by social media platforms.
            min_followers (Optional[int]): Minimum follower count.
            max_followers (Optional[int]): Maximum follower count.
            min_engagement_rate (Optional[float]): Minimum engagement rate.
            max_engagement_rate (Optional[float]): Maximum engagement rate.
            verified_only (Optional[bool]): Only verified KOLs.
            niches (Optional[List[str]]): Filter by niche/category.
            locations (Optional[List[str]]): Filter by location.
            min_posts (Optional[int]): Minimum number of posts.
            sort_by (str): Field to sort by.
            sort_order (str): Sort order (asc/desc).
            page (int): Page number.
            per_page (int): Items per page.

        Returns:
            Dict[str, Any]: Search results with pagination metadata.
        """
        # Start with base query
        builder = QueryBuilder(KOL, self.db.query(KOL))

        # Apply full-text search
        if search_term:
            builder.search(
                search_term,
                ["name", "bio", "tags", "niche", "location"]
            )

        # Platform filter
        if platforms:
            builder.filter_in("platform", platforms)

        # Follower count range
        if min_followers or max_followers:
            builder.filter_range(
                "followers_count",
                min_value=min_followers,
                max_value=max_followers
            )

        # Engagement rate range
        if min_engagement_rate or max_engagement_rate:
            builder.filter_range(
                "engagement_rate",
                min_value=min_engagement_rate,
                max_value=max_engagement_rate
            )

        # Verified filter
        if verified_only is not None:
            builder.filter_equals("verified", verified_only)

        # Niche filter
        if niches:
            builder.filter_in("niche", niches)

        # Location filter
        if locations:
            builder.filter_in("location", locations)

        # Minimum posts
        if min_posts:
            builder.filter_range("posts_count", min_value=min_posts)

        # Apply sorting
        builder.sort(sort_by, sort_order)

        # Execute with pagination
        return builder.paginate(page, per_page)

    def quick_search(self, search_term: str, limit: int = 10) -> List[KOL]:
        """
        Quick search for autocomplete/suggestions.

        Args:
            search_term (str): Search term.
            limit (int): Maximum results to return.

        Returns:
            List[KOL]: Matching KOLs.
        """
        query = self.db.query(KOL)

        # Search in name, username, tags
        query = apply_search(query, KOL, search_term, ["name", "username", "tags"])

        # Limit results
        return query.limit(limit).all()

    def get_popular_kols(
        self,
        platform: Optional[str] = None,
        niche: Optional[str] = None,
        limit: int = 10
    ) -> List[KOL]:
        """
        Get popular KOLs (by follower count and engagement).

        Args:
            platform (Optional[str]): Filter by platform.
            niche (Optional[str]): Filter by niche.
            limit (int): Maximum results.

        Returns:
            List[KOL]: Popular KOLs.
        """
        query = self.db.query(KOL)

        # Apply filters
        if platform:
            query = query.filter(KOL.platform == platform)

        if niche:
            query = query.filter(KOL.niche == niche)

        # Sort by a popularity score (weighted followers + engagement)
        query = query.order_by(
            (KOL.followers_count * 0.7 + KOL.engagement_rate * 1000 * 0.3).desc()
        )

        return query.limit(limit).all()

    def get_trending_kols(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[KOL]:
        """
        Get trending KOLs (highest growth in recent period).

        Note: This requires historical data tracking.

        Args:
            days (int): Number of days to look back.
            limit (int): Maximum results.

        Returns:
            List[KOL]: Trending KOLs.
        """
        # TODO: Implement with historical follower tracking
        # For now, return recent high-engagement KOLs
        query = self.db.query(KOL)
        query = query.filter(KOL.engagement_rate > 3.0)
        query = query.order_by(KOL.engagement_rate.desc())

        return query.limit(limit).all()

    def get_filter_options(self) -> Dict[str, List[Any]]:
        """
        Get available filter options (for UI dropdowns).

        Returns:
            Dict[str, List[Any]]: Available filter values.
        """
        # Get distinct platforms
        platforms = self.db.query(KOL.platform).distinct().all()
        platforms = [p[0] for p in platforms if p[0]]

        # Get distinct niches
        niches = self.db.query(KOL.niche).distinct().all()
        niches = [n[0] for n in niches if n[0]]

        # Get distinct locations
        locations = self.db.query(KOL.location).distinct().all()
        locations = [l[0] for l in locations if l[0]]

        # Get follower count ranges (for suggestions)
        follower_ranges = [
            {"label": "Micro (1K-10K)", "min": 1000, "max": 10000},
            {"label": "Mid-tier (10K-100K)", "min": 10000, "max": 100000},
            {"label": "Macro (100K-1M)", "min": 100000, "max": 1000000},
            {"label": "Mega (1M+)", "min": 1000000, "max": None},
        ]

        return {
            "platforms": sorted(platforms),
            "niches": sorted(niches),
            "locations": sorted(locations),
            "follower_ranges": follower_ranges
        }


class CampaignSearchService:
    """
    Service for searching and filtering campaigns.
    """

    def __init__(self, db: Session):
        """
        Initialize campaign search service.

        Args:
            db (Session): Database session.
        """
        self.db = db

    def search_campaigns(
        self,
        # Search
        search_term: Optional[str] = None,

        # Filters
        status: Optional[List[str]] = None,
        start_date_from: Optional[Any] = None,
        start_date_to: Optional[Any] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None,
        created_by: Optional[int] = None,

        # Sorting
        sort_by: str = "created_at",
        sort_order: str = "desc",

        # Pagination
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Search campaigns with filters.

        Args:
            search_term (Optional[str]): Search in name/description.
            status (Optional[List[str]]): Filter by status.
            start_date_from (Optional[Any]): Campaign start date from.
            start_date_to (Optional[Any]): Campaign start date to.
            min_budget (Optional[float]): Minimum budget.
            max_budget (Optional[float]): Maximum budget.
            created_by (Optional[int]): Filter by creator.
            sort_by (str): Field to sort by.
            sort_order (str): Sort order.
            page (int): Page number.
            per_page (int): Items per page.

        Returns:
            Dict[str, Any]: Search results with pagination.
        """
        builder = QueryBuilder(Campaign, self.db.query(Campaign))

        # Search
        if search_term:
            builder.search(search_term, ["name", "description"])

        # Status filter
        if status:
            builder.filter_in("status", status)

        # Date range
        if start_date_from or start_date_to:
            builder.filter_date_range(
                "start_date",
                start_date=start_date_from,
                end_date=start_date_to
            )

        # Budget range
        if min_budget or max_budget:
            builder.filter_range("budget", min_value=min_budget, max_value=max_budget)

        # Creator filter
        if created_by:
            builder.filter_equals("created_by", created_by)

        # Sort
        builder.sort(sort_by, sort_order)

        # Paginate
        return builder.paginate(page, per_page)

    def get_active_campaigns(self, limit: int = 10) -> List[Campaign]:
        """
        Get active campaigns.

        Args:
            limit (int): Maximum results.

        Returns:
            List[Campaign]: Active campaigns.
        """
        return self.db.query(Campaign)\
            .filter(Campaign.status == "active")\
            .order_by(Campaign.start_date.desc())\
            .limit(limit)\
            .all()

    def get_recent_campaigns(self, limit: int = 10) -> List[Campaign]:
        """
        Get recently created campaigns.

        Args:
            limit (int): Maximum results.

        Returns:
            List[Campaign]: Recent campaigns.
        """
        return self.db.query(Campaign)\
            .order_by(Campaign.created_at.desc())\
            .limit(limit)\
            .all()


def get_kol_search_service(db: Session) -> KOLSearchService:
    """
    Dependency for FastAPI to inject KOLSearchService.

    Args:
        db (Session): Database session.

    Returns:
        KOLSearchService: Search service instance.
    """
    return KOLSearchService(db)


def get_campaign_search_service(db: Session) -> CampaignSearchService:
    """
    Dependency for FastAPI to inject CampaignSearchService.

    Args:
        db (Session): Database session.

    Returns:
        CampaignSearchService: Search service instance.
    """
    return CampaignSearchService(db)
