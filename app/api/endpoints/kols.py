"""
KOL Management API Endpoints

Provides comprehensive API endpoints for managing Key Opinion Leaders (KOLs):
- CRUD operations for KOL profiles
- Search and filtering capabilities
- Performance tracking and analytics
- Social media account management
- Collaboration management
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.kols import KOL, KOLSocialAccounts, KOLPerformanceMetrics
from app.models.collaboration import Collaboration
from app.models.campaigns import Campaign
from app.schemas.kols import (
    KOLCreate, KOLUpdate, KOLResponse, KOLListResponse,
    KOLSearchFilters, KOLPerformanceResponse, KOLSocialAccountCreate,
    KOLSocialAccountUpdate, KOLCollaborationHistory
)
from app.services.social_media.factory import social_media_factory
from app.tasks.social_media import collect_kol_profile_data
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kols", tags=["KOLs"])


@router.post("/", response_model=KOLResponse, status_code=status.HTTP_201_CREATED)
async def create_kol(
    kol_data: KOLCreate,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> KOLResponse:
    """
    Create a new KOL profile.

    Args:
        kol_data: KOL creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created KOL profile
    """
    try:
        # Check if KOL with email already exists
        existing_query = select(KOL).where(KOL.email == kol_data.email)
        existing_result = await db.execute(existing_query)
        existing_kol = existing_result.scalar_one_or_none()

        if existing_kol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KOL with this email already exists"
            )

        # Create KOL instance
        kol = KOL(
            name=kol_data.name,
            email=kol_data.email,
            phone=kol_data.phone,
            primary_platform=kol_data.primary_platform,
            bio=kol_data.bio,
            location=kol_data.location,
            languages=kol_data.languages,
            categories=kol_data.categories,
            follower_counts=kol_data.follower_counts or {},
            engagement_rates=kol_data.engagement_rates or {},
            pricing=kol_data.pricing or {},
            status="pending_verification",
            created_by=current_user.id
        )

        db.add(kol)
        await db.commit()
        await db.refresh(kol)

        # Schedule profile data collection if social accounts provided
        if kol_data.social_accounts:
            for account in kol_data.social_accounts:
                # Create social account record
                social_account = KOLSocialAccounts(
                    kol_id=kol.id,
                    platform=account.platform,
                    username=account.username,
                    profile_url=account.profile_url,
                    follower_count=account.follower_count,
                    is_verified=account.is_verified,
                    is_primary=account.is_primary
                )
                db.add(social_account)

            await db.commit()

            # Schedule background task to collect profile data
            platforms = [acc.platform for acc in kol_data.social_accounts]
            collect_kol_profile_data.delay(kol.id, platforms)

        logger.info(f"KOL created successfully: {kol.id}")
        return KOLResponse.model_validate(kol)

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create KOL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create KOL profile"
        )


@router.get("/", response_model=KOLListResponse)
async def list_kols(
    pagination: PaginationParams = Depends(),
    filters: KOLSearchFilters = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> KOLListResponse:
    """
    List KOLs with filtering and pagination.

    Args:
        pagination: Pagination parameters
        filters: Search and filter parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of KOLs
    """
    try:
        # Build base query
        query = select(KOL)

        # Apply filters
        if filters.status:
            query = query.where(KOL.status.in_(filters.status))

        if filters.categories:
            query = query.where(KOL.categories.op("&&")(filters.categories))

        if filters.primary_platform:
            query = query.where(KOL.primary_platform.in_(filters.primary_platform))

        if filters.location:
            query = query.where(KOL.location.ilike(f"%{filters.location}%"))

        if filters.languages:
            query = query.where(KOL.languages.op("&&")(filters.languages))

        if filters.min_followers:
            # Filter by follower count on primary platform
            query = query.where(
                func.coalesce(
                    KOL.follower_counts[KOL.primary_platform].astext.cast(Integer), 0
                ) >= filters.min_followers
            )

        if filters.max_followers:
            query = query.where(
                func.coalesce(
                    KOL.follower_counts[KOL.primary_platform].astext.cast(Integer), 0
                ) <= filters.max_followers
            )

        if filters.min_engagement_rate:
            query = query.where(
                func.coalesce(
                    KOL.engagement_rates[KOL.primary_platform].astext.cast(Float), 0
                ) >= filters.min_engagement_rate
            )

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    KOL.name.ilike(search_term),
                    KOL.email.ilike(search_term),
                    KOL.bio.ilike(search_term)
                )
            )

        # Apply sorting
        if filters.sort_by:
            if filters.sort_by == "name":
                order_column = KOL.name
            elif filters.sort_by == "created_at":
                order_column = KOL.created_at
            elif filters.sort_by == "followers":
                order_column = KOL.follower_counts[KOL.primary_platform].astext.cast(Integer)
            else:
                order_column = KOL.created_at

            if filters.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(KOL.created_at.desc())

        # Execute paginated query
        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return KOLListResponse(
            kols=[KOLResponse.model_validate(kol) for kol in result.items],
            total=result.total,
            page=result.page,
            limit=result.limit,
            pages=result.pages
        )

    except Exception as e:
        logger.error(f"Failed to list KOLs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KOLs"
        )


@router.get("/{kol_id}", response_model=KOLResponse)
async def get_kol(
    kol_id: int = Path(..., description="KOL ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> KOLResponse:
    """
    Get specific KOL by ID.

    Args:
        kol_id: KOL identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        KOL profile details
    """
    try:
        query = select(KOL).where(KOL.id == kol_id)
        result = await db.execute(query)
        kol = result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        return KOLResponse.model_validate(kol)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get KOL {kol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KOL"
        )


@router.put("/{kol_id}", response_model=KOLResponse)
async def update_kol(
    kol_id: int = Path(..., description="KOL ID"),
    kol_data: KOLUpdate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> KOLResponse:
    """
    Update KOL profile.

    Args:
        kol_id: KOL identifier
        kol_data: Updated KOL data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated KOL profile
    """
    try:
        query = select(KOL).where(KOL.id == kol_id)
        result = await db.execute(query)
        kol = result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Update fields
        update_data = kol_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "follower_counts" and value:
                # Merge with existing follower counts
                kol.follower_counts = {**kol.follower_counts, **value}
            elif field == "engagement_rates" and value:
                # Merge with existing engagement rates
                kol.engagement_rates = {**kol.engagement_rates, **value}
            elif field == "pricing" and value:
                # Merge with existing pricing
                kol.pricing = {**kol.pricing, **value}
            else:
                setattr(kol, field, value)

        kol.updated_at = datetime.utcnow()
        kol.updated_by = current_user.id

        await db.commit()
        await db.refresh(kol)

        logger.info(f"KOL updated successfully: {kol.id}")
        return KOLResponse.model_validate(kol)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update KOL {kol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update KOL"
        )


@router.delete("/{kol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kol(
    kol_id: int = Path(..., description="KOL ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Delete KOL profile (soft delete).

    Args:
        kol_id: KOL identifier
        db: Database session
        current_user: Current authenticated user
    """
    try:
        query = select(KOL).where(KOL.id == kol_id)
        result = await db.execute(query)
        kol = result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Check for active collaborations
        active_collab_query = select(Collaboration).where(
            and_(
                Collaboration.kol_id == kol_id,
                Collaboration.status.in_(["pending", "approved", "active"])
            )
        )
        active_collab_result = await db.execute(active_collab_query)
        active_collaborations = active_collab_result.scalars().all()

        if active_collaborations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete KOL with active collaborations"
            )

        # Soft delete
        kol.status = "deleted"
        kol.updated_at = datetime.utcnow()
        kol.updated_by = current_user.id

        await db.commit()

        logger.info(f"KOL deleted successfully: {kol.id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete KOL {kol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete KOL"
        )


@router.get("/{kol_id}/performance", response_model=KOLPerformanceResponse)
async def get_kol_performance(
    kol_id: int = Path(..., description="KOL ID"),
    days: int = Query(30, description="Number of days for performance data"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> KOLPerformanceResponse:
    """
    Get KOL performance metrics and analytics.

    Args:
        kol_id: KOL identifier
        days: Number of days for performance analysis
        db: Database session
        current_user: Current authenticated user

    Returns:
        KOL performance analytics
    """
    try:
        # Check if KOL exists
        kol_query = select(KOL).where(KOL.id == kol_id)
        kol_result = await db.execute(kol_query)
        kol = kol_result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Get performance metrics
        metrics_query = select(KOLPerformanceMetrics).where(
            KOLPerformanceMetrics.kol_id == kol_id
        )
        metrics_result = await db.execute(metrics_query)
        metrics = metrics_result.scalar_one_or_none()

        # Get collaboration history
        date_cutoff = datetime.utcnow() - timedelta(days=days)
        collab_query = select(Collaboration).where(
            and_(
                Collaboration.kol_id == kol_id,
                Collaboration.created_at >= date_cutoff
            )
        ).order_by(Collaboration.created_at.desc())

        collab_result = await db.execute(collab_query)
        collaborations = collab_result.scalars().all()

        # Calculate performance statistics
        total_campaigns = len(collaborations)
        successful_campaigns = len([c for c in collaborations if c.status == "completed"])
        avg_engagement = metrics.avg_engagement_rate if metrics else 0
        avg_reach = metrics.avg_reach if metrics else 0

        return KOLPerformanceResponse(
            kol_id=kol_id,
            avg_engagement_rate=avg_engagement,
            avg_reach=avg_reach,
            total_campaigns=total_campaigns,
            successful_campaigns=successful_campaigns,
            reliability_score=metrics.reliability_score if metrics else 0,
            collaboration_history=[
                KOLCollaborationHistory.model_validate(collab)
                for collab in collaborations
            ],
            last_updated=metrics.last_updated if metrics else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get KOL performance {kol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KOL performance data"
        )


@router.post("/{kol_id}/social-accounts", response_model=Dict[str, Any])
async def add_social_account(
    kol_id: int = Path(..., description="KOL ID"),
    account_data: KOLSocialAccountCreate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Add social media account to KOL profile.

    Args:
        kol_id: KOL identifier
        account_data: Social account data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success response with account details
    """
    try:
        # Check if KOL exists
        kol_query = select(KOL).where(KOL.id == kol_id)
        kol_result = await db.execute(kol_query)
        kol = kol_result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Check if account already exists
        existing_query = select(KOLSocialAccounts).where(
            and_(
                KOLSocialAccounts.kol_id == kol_id,
                KOLSocialAccounts.platform == account_data.platform,
                KOLSocialAccounts.username == account_data.username
            )
        )
        existing_result = await db.execute(existing_query)
        existing_account = existing_result.scalar_one_or_none()

        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Social account already exists"
            )

        # Create social account
        social_account = KOLSocialAccounts(
            kol_id=kol_id,
            platform=account_data.platform,
            username=account_data.username,
            profile_url=account_data.profile_url,
            follower_count=account_data.follower_count,
            is_verified=account_data.is_verified,
            is_primary=account_data.is_primary
        )

        db.add(social_account)
        await db.commit()
        await db.refresh(social_account)

        # Schedule profile data collection
        collect_kol_profile_data.delay(kol_id, [account_data.platform])

        logger.info(f"Social account added for KOL {kol_id}: {account_data.platform}")
        return {
            "success": True,
            "message": "Social account added successfully",
            "account_id": social_account.id
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to add social account for KOL {kol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add social account"
        )


@router.put("/{kol_id}/social-accounts/{account_id}")
async def update_social_account(
    kol_id: int = Path(..., description="KOL ID"),
    account_id: int = Path(..., description="Social Account ID"),
    account_data: KOLSocialAccountUpdate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update social media account for KOL.

    Args:
        kol_id: KOL identifier
        account_id: Social account identifier
        account_data: Updated social account data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success response
    """
    try:
        # Check if social account exists
        account_query = select(KOLSocialAccounts).where(
            and_(
                KOLSocialAccounts.id == account_id,
                KOLSocialAccounts.kol_id == kol_id
            )
        )
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found"
            )

        # Update fields
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        account.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Social account updated for KOL {kol_id}: {account_id}")
        return {
            "success": True,
            "message": "Social account updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update social account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update social account"
        )


@router.delete("/{kol_id}/social-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_account(
    kol_id: int = Path(..., description="KOL ID"),
    account_id: int = Path(..., description="Social Account ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Delete social media account from KOL profile.

    Args:
        kol_id: KOL identifier
        account_id: Social account identifier
        db: Database session
        current_user: Current authenticated user
    """
    try:
        # Check if social account exists
        account_query = select(KOLSocialAccounts).where(
            and_(
                KOLSocialAccounts.id == account_id,
                KOLSocialAccounts.kol_id == kol_id
            )
        )
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found"
            )

        await db.delete(account)
        await db.commit()

        logger.info(f"Social account deleted for KOL {kol_id}: {account_id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete social account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete social account"
        )


@router.post("/{kol_id}/refresh-data", response_model=Dict[str, Any])
async def refresh_kol_data(
    kol_id: int = Path(..., description="KOL ID"),
    platforms: List[str] = Query(None, description="Platforms to refresh (optional)"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh KOL profile data from social media platforms.

    Args:
        kol_id: KOL identifier
        platforms: Specific platforms to refresh (optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Task scheduling confirmation
    """
    try:
        # Check if KOL exists
        kol_query = select(KOL).where(KOL.id == kol_id)
        kol_result = await db.execute(kol_query)
        kol = kol_result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Get KOL's social accounts
        if not platforms:
            accounts_query = select(KOLSocialAccounts.platform).where(
                KOLSocialAccounts.kol_id == kol_id
            ).distinct()
            accounts_result = await db.execute(accounts_query)
            platforms = [platform for platform, in accounts_result.fetchall()]

        if not platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No social accounts found for KOL"
            )

        # Schedule data collection task
        task = collect_kol_profile_data.delay(kol_id, platforms)

        logger.info(f"Data refresh scheduled for KOL {kol_id}: {platforms}")
        return {
            "success": True,
            "message": "Data refresh scheduled successfully",
            "task_id": task.id,
            "platforms": platforms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh KOL data {kol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule data refresh"
        )


@router.post("/search", response_model=KOLListResponse)
async def search_kols(
    search_filters: KOLSearchFilters,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> KOLListResponse:
    """
    Advanced KOL search with complex filtering.

    Args:
        search_filters: Advanced search and filter parameters
        pagination: Pagination parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated search results
    """
    try:
        # This is essentially the same as list_kols but with POST for complex search
        # Build base query
        query = select(KOL)

        # Apply all filters from search_filters
        if search_filters.status:
            query = query.where(KOL.status.in_(search_filters.status))

        if search_filters.categories:
            query = query.where(KOL.categories.op("&&")(search_filters.categories))

        if search_filters.primary_platform:
            query = query.where(KOL.primary_platform.in_(search_filters.primary_platform))

        if search_filters.location:
            query = query.where(KOL.location.ilike(f"%{search_filters.location}%"))

        if search_filters.languages:
            query = query.where(KOL.languages.op("&&")(search_filters.languages))

        if search_filters.min_followers:
            query = query.where(
                func.coalesce(
                    KOL.follower_counts[KOL.primary_platform].astext.cast(Integer), 0
                ) >= search_filters.min_followers
            )

        if search_filters.max_followers:
            query = query.where(
                func.coalesce(
                    KOL.follower_counts[KOL.primary_platform].astext.cast(Integer), 0
                ) <= search_filters.max_followers
            )

        if search_filters.min_engagement_rate:
            query = query.where(
                func.coalesce(
                    KOL.engagement_rates[KOL.primary_platform].astext.cast(Float), 0
                ) >= search_filters.min_engagement_rate
            )

        if search_filters.search:
            search_term = f"%{search_filters.search}%"
            query = query.where(
                or_(
                    KOL.name.ilike(search_term),
                    KOL.email.ilike(search_term),
                    KOL.bio.ilike(search_term)
                )
            )

        # Apply sorting
        if search_filters.sort_by:
            if search_filters.sort_by == "name":
                order_column = KOL.name
            elif search_filters.sort_by == "created_at":
                order_column = KOL.created_at
            elif search_filters.sort_by == "followers":
                order_column = KOL.follower_counts[KOL.primary_platform].astext.cast(Integer)
            else:
                order_column = KOL.created_at

            if search_filters.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(KOL.created_at.desc())

        # Execute paginated query
        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return KOLListResponse(
            kols=[KOLResponse.model_validate(kol) for kol in result.items],
            total=result.total,
            page=result.page,
            limit=result.limit,
            pages=result.pages
        )

    except Exception as e:
        logger.error(f"Failed to search KOLs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search KOLs"
        )


@router.post("/bulk-update", response_model=Dict[str, Any])
async def bulk_update_kols(
    update_data: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Bulk update multiple KOL profiles.

    Args:
        update_data: List of KOL updates with id and update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Bulk update results
    """
    results = {
        "success_count": 0,
        "failed_count": 0,
        "failed_kols": [],
        "updated_kols": []
    }

    try:
        for update_item in update_data:
            kol_id = update_item.get("id")
            update_fields = update_item.get("updates", {})

            if not kol_id:
                results["failed_count"] += 1
                results["failed_kols"].append({
                    "error": "Missing KOL ID",
                    "data": update_item
                })
                continue

            try:
                # Get KOL
                query = select(KOL).where(KOL.id == kol_id)
                result = await db.execute(query)
                kol = result.scalar_one_or_none()

                if not kol:
                    results["failed_count"] += 1
                    results["failed_kols"].append({
                        "kol_id": kol_id,
                        "error": "KOL not found"
                    })
                    continue

                # Apply updates
                for field, value in update_fields.items():
                    if hasattr(kol, field):
                        if field in ["follower_counts", "engagement_rates", "pricing"] and value:
                            # Merge dictionaries
                            current_value = getattr(kol, field) or {}
                            merged_value = {**current_value, **value}
                            setattr(kol, field, merged_value)
                        else:
                            setattr(kol, field, value)

                kol.updated_at = datetime.utcnow()
                kol.updated_by = current_user.id

                results["success_count"] += 1
                results["updated_kols"].append(kol_id)

            except Exception as e:
                results["failed_count"] += 1
                results["failed_kols"].append({
                    "kol_id": kol_id,
                    "error": str(e)
                })

        await db.commit()

        logger.info(f"Bulk update completed: {results['success_count']} success, {results['failed_count']} failed")
        return results

    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk update operation failed"
        )


@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_kols_analytics_summary(
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get KOL analytics summary and statistics.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        KOL analytics summary
    """
    try:
        # Total KOL counts by status
        status_query = select(
            KOL.status,
            func.count(KOL.id).label('count')
        ).group_by(KOL.status)
        status_result = await db.execute(status_query)
        status_counts = {row.status: row.count for row in status_result}

        # Platform distribution
        platform_query = select(
            KOL.primary_platform,
            func.count(KOL.id).label('count')
        ).group_by(KOL.primary_platform)
        platform_result = await db.execute(platform_query)
        platform_distribution = {row.primary_platform: row.count for row in platform_result}

        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_query = select(func.count(KOL.id)).where(KOL.created_at >= thirty_days_ago)
        recent_result = await db.execute(recent_query)
        recent_registrations = recent_result.scalar() or 0

        # Top categories
        categories_query = select(KOL.categories).where(KOL.categories.isnot(None))
        categories_result = await db.execute(categories_query)
        all_categories = []
        for row in categories_result:
            if row.categories:
                all_categories.extend(row.categories)

        category_counts = {}
        for category in all_categories:
            category_counts[category] = category_counts.get(category, 0) + 1

        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Average metrics
        metrics_query = select(
            func.avg(func.cast(KOL.follower_counts[KOL.primary_platform].astext, Integer)).label('avg_followers'),
            func.avg(func.cast(KOL.engagement_rates[KOL.primary_platform].astext, Float)).label('avg_engagement')
        ).where(
            and_(
                KOL.follower_counts.isnot(None),
                KOL.engagement_rates.isnot(None)
            )
        )
        metrics_result = await db.execute(metrics_query)
        metrics_row = metrics_result.first()

        return {
            "total_kols": sum(status_counts.values()),
            "status_distribution": status_counts,
            "platform_distribution": platform_distribution,
            "recent_registrations": recent_registrations,
            "top_categories": dict(top_categories),
            "average_metrics": {
                "followers": int(metrics_row.avg_followers) if metrics_row.avg_followers else 0,
                "engagement_rate": round(float(metrics_row.avg_engagement), 2) if metrics_row.avg_engagement else 0.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get KOL analytics summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )


@router.post("/export", response_model=Dict[str, Any])
async def export_kols_data(
    export_filters: Optional[Dict[str, Any]] = None,
    format: str = Query("json", description="Export format: json, csv"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export KOL data in various formats.

    Args:
        export_filters: Optional filters for data export
        format: Export format (json, csv)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Export task information
    """
    try:
        # Build query based on filters
        query = select(KOL)

        if export_filters:
            if export_filters.get("status"):
                query = query.where(KOL.status.in_(export_filters["status"]))

            if export_filters.get("categories"):
                query = query.where(KOL.categories.op("&&")(export_filters["categories"]))

            if export_filters.get("date_range"):
                date_range = export_filters["date_range"]
                if date_range.get("start"):
                    query = query.where(KOL.created_at >= datetime.fromisoformat(date_range["start"]))
                if date_range.get("end"):
                    query = query.where(KOL.created_at <= datetime.fromisoformat(date_range["end"]))

        # Get KOL count for the export
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_kols = count_result.scalar() or 0

        # For now, return export information
        # In a production system, this would schedule a background task
        export_id = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"KOL data export requested: {total_kols} KOLs, format: {format}")

        return {
            "export_id": export_id,
            "status": "scheduled",
            "total_kols": total_kols,
            "format": format,
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "download_url": f"/api/v1/kols/exports/{export_id}/download"
        }

    except Exception as e:
        logger.error(f"Failed to export KOL data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule data export"
        )