"""
Campaign Management API Endpoints

Provides comprehensive API endpoints for campaign management:
- CRUD operations for campaigns
- Campaign brief generation and management
- KOL collaboration management
- Campaign workflow and status tracking
- Content management and approval workflows
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
from app.models.campaign import Campaign
from app.models.campaign_content import CampaignBrief, CampaignContent
from app.models.collaboration import Collaboration
from app.models.kol import KOL
from app.schemas.campaigns import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignListResponse,
    CampaignSearchFilters, CampaignBriefCreate, CampaignBriefUpdate,
    CampaignBriefResponse, CollaborationCreate, CollaborationUpdate,
    CollaborationResponse, CampaignContentCreate, CampaignContentResponse,
    CampaignAnalytics, CampaignWorkflowAction
)
from app.tasks.campaigns import generate_campaign_brief, monitor_campaign_performance
from app.tasks.communication import send_campaign_messages
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CampaignResponse:
    """
    Create a new campaign.

    Args:
        campaign_data: Campaign creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created campaign details
    """
    try:
        # Create campaign instance
        campaign = Campaign(
            name=campaign_data.name,
            description=campaign_data.description,
            objectives=campaign_data.objectives,
            target_audience=campaign_data.target_audience,
            budget=campaign_data.budget,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            platforms=campaign_data.platforms,
            content_requirements=campaign_data.content_requirements,
            deliverables=campaign_data.deliverables,
            guidelines=campaign_data.guidelines,
            target_reach=campaign_data.target_reach,
            target_engagement_rate=campaign_data.target_engagement_rate,
            compensation_model=campaign_data.compensation_model,
            status="draft",
            created_by=current_user.id
        )

        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)

        logger.info(f"Campaign created successfully: {campaign.id}")
        return CampaignResponse.model_validate(campaign)

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    pagination: PaginationParams = Depends(),
    filters: CampaignSearchFilters = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CampaignListResponse:
    """
    List campaigns with filtering and pagination.

    Args:
        pagination: Pagination parameters
        filters: Search and filter parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of campaigns
    """
    try:
        # Build base query
        query = select(Campaign)

        # Apply filters
        if filters.status:
            query = query.where(Campaign.status.in_(filters.status))

        if filters.platforms:
            query = query.where(Campaign.platforms.op("&&")(filters.platforms))

        if filters.budget_min:
            query = query.where(Campaign.budget >= filters.budget_min)

        if filters.budget_max:
            query = query.where(Campaign.budget <= filters.budget_max)

        if filters.start_date:
            query = query.where(Campaign.start_date >= filters.start_date)

        if filters.end_date:
            query = query.where(Campaign.end_date <= filters.end_date)

        if filters.created_by:
            query = query.where(Campaign.created_by == filters.created_by)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Campaign.name.ilike(search_term),
                    Campaign.description.ilike(search_term)
                )
            )

        # Apply sorting
        if filters.sort_by:
            if filters.sort_by == "name":
                order_column = Campaign.name
            elif filters.sort_by == "budget":
                order_column = Campaign.budget
            elif filters.sort_by == "start_date":
                order_column = Campaign.start_date
            else:
                order_column = Campaign.created_at

            if filters.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(Campaign.created_at.desc())

        # Execute paginated query
        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return CampaignListResponse(
            campaigns=[CampaignResponse.model_validate(campaign) for campaign in result.items],
            total=result.total,
            page=result.page,
            limit=result.limit,
            pages=result.pages
        )

    except Exception as e:
        logger.error(f"Failed to list campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaigns"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CampaignResponse:
    """
    Get specific campaign by ID.

    Args:
        campaign_id: Campaign identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Campaign details
    """
    try:
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        return CampaignResponse.model_validate(campaign)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign"
        )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    campaign_data: CampaignUpdate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CampaignResponse:
    """
    Update campaign details.

    Args:
        campaign_id: Campaign identifier
        campaign_data: Updated campaign data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated campaign details
    """
    try:
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Update fields
        update_data = campaign_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["content_requirements", "deliverables", "guidelines"] and value:
                # Merge with existing data
                current_value = getattr(campaign, field) or {}
                merged_value = {**current_value, **value}
                setattr(campaign, field, merged_value)
            else:
                setattr(campaign, field, value)

        campaign.updated_at = datetime.utcnow()
        campaign.updated_by = current_user.id

        await db.commit()
        await db.refresh(campaign)

        logger.info(f"Campaign updated successfully: {campaign.id}")
        return CampaignResponse.model_validate(campaign)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign"
        )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Delete campaign (soft delete).

    Args:
        campaign_id: Campaign identifier
        db: Database session
        current_user: Current authenticated user
    """
    try:
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Check if campaign can be deleted
        if campaign.status in ["active", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active or completed campaigns"
            )

        # Soft delete
        campaign.status = "deleted"
        campaign.updated_at = datetime.utcnow()
        campaign.updated_by = current_user.id

        await db.commit()

        logger.info(f"Campaign deleted successfully: {campaign.id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        )


@router.post("/{campaign_id}/briefs", response_model=Dict[str, Any])
async def generate_brief(
    campaign_id: int = Path(..., description="Campaign ID"),
    brief_data: CampaignBriefCreate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate campaign brief using AI and templates.

    Args:
        campaign_id: Campaign identifier
        brief_data: Brief generation parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Brief generation task information
    """
    try:
        # Check if campaign exists
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Prepare brief template
        brief_template = {
            "campaign_id": campaign_id,
            "template_type": brief_data.template_type,
            "customization": brief_data.customization,
            "auto_send": brief_data.auto_send,
            "target_kols": brief_data.target_kols
        }

        # Schedule brief generation task
        task = generate_campaign_brief.delay(campaign_id, brief_template)

        logger.info(f"Brief generation scheduled for campaign {campaign_id}")
        return {
            "success": True,
            "message": "Brief generation scheduled successfully",
            "task_id": task.id,
            "campaign_id": campaign_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate brief for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate campaign brief"
        )


@router.get("/{campaign_id}/briefs", response_model=List[CampaignBriefResponse])
async def list_campaign_briefs(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[CampaignBriefResponse]:
    """
    List campaign briefs.

    Args:
        campaign_id: Campaign identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of campaign briefs
    """
    try:
        query = select(CampaignBrief).where(CampaignBrief.campaign_id == campaign_id)
        result = await db.execute(query)
        briefs = result.scalars().all()

        return [CampaignBriefResponse.model_validate(brief) for brief in briefs]

    except Exception as e:
        logger.error(f"Failed to list briefs for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign briefs"
        )


@router.post("/{campaign_id}/collaborations", response_model=CollaborationResponse)
async def create_collaboration(
    campaign_id: int = Path(..., description="Campaign ID"),
    collab_data: CollaborationCreate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CollaborationResponse:
    """
    Create KOL collaboration for campaign.

    Args:
        campaign_id: Campaign identifier
        collab_data: Collaboration creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created collaboration details
    """
    try:
        # Verify campaign exists
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Verify KOL exists
        kol_query = select(KOL).where(KOL.id == collab_data.kol_id)
        kol_result = await db.execute(kol_query)
        kol = kol_result.scalar_one_or_none()

        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )

        # Check for existing collaboration
        existing_query = select(Collaboration).where(
            and_(
                Collaboration.campaign_id == campaign_id,
                Collaboration.kol_id == collab_data.kol_id
            )
        )
        existing_result = await db.execute(existing_query)
        existing_collab = existing_result.scalar_one_or_none()

        if existing_collab:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collaboration already exists"
            )

        # Create collaboration
        collaboration = Collaboration(
            campaign_id=campaign_id,
            kol_id=collab_data.kol_id,
            compensation_amount=collab_data.compensation_amount,
            compensation_type=collab_data.compensation_type,
            deliverables=collab_data.deliverables,
            timeline=collab_data.timeline,
            status="pending",
            created_by=current_user.id
        )

        db.add(collaboration)
        await db.commit()
        await db.refresh(collaboration)

        # Send notification to KOL
        send_campaign_messages.delay(
            campaign_id,
            1,  # Default template ID
            [collab_data.kol_id]
        )

        logger.info(f"Collaboration created: campaign {campaign_id}, KOL {collab_data.kol_id}")
        return CollaborationResponse.model_validate(collaboration)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create collaboration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collaboration"
        )


@router.get("/{campaign_id}/collaborations", response_model=List[CollaborationResponse])
async def list_campaign_collaborations(
    campaign_id: int = Path(..., description="Campaign ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> List[CollaborationResponse]:
    """
    List campaign collaborations.

    Args:
        campaign_id: Campaign identifier
        status_filter: Optional status filter
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of campaign collaborations
    """
    try:
        query = select(Collaboration).where(Collaboration.campaign_id == campaign_id)

        if status_filter:
            query = query.where(Collaboration.status == status_filter)

        result = await db.execute(query)
        collaborations = result.scalars().all()

        return [CollaborationResponse.model_validate(collab) for collab in collaborations]

    except Exception as e:
        logger.error(f"Failed to list collaborations for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collaborations"
        )


@router.put("/collaborations/{collaboration_id}")
async def update_collaboration(
    collaboration_id: int = Path(..., description="Collaboration ID"),
    collab_data: CollaborationUpdate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CollaborationResponse:
    """
    Update collaboration details.

    Args:
        collaboration_id: Collaboration identifier
        collab_data: Updated collaboration data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated collaboration details
    """
    try:
        query = select(Collaboration).where(Collaboration.id == collaboration_id)
        result = await db.execute(query)
        collaboration = result.scalar_one_or_none()

        if not collaboration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collaboration not found"
            )

        # Update fields
        update_data = collab_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(collaboration, field, value)

        collaboration.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(collaboration)

        logger.info(f"Collaboration updated: {collaboration_id}")
        return CollaborationResponse.model_validate(collaboration)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update collaboration {collaboration_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update collaboration"
        )


@router.post("/{campaign_id}/content", response_model=CampaignContentResponse)
async def create_campaign_content(
    campaign_id: int = Path(..., description="Campaign ID"),
    content_data: CampaignContentCreate = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CampaignContentResponse:
    """
    Create campaign content entry.

    Args:
        campaign_id: Campaign identifier
        content_data: Content creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created content details
    """
    try:
        # Verify campaign exists
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Create content record
        content = CampaignContent(
            campaign_id=campaign_id,
            kol_id=content_data.kol_id,
            platform=content_data.platform,
            content_type=content_data.content_type,
            title=content_data.title,
            description=content_data.description,
            content_url=content_data.content_url,
            media_urls=content_data.media_urls,
            hashtags=content_data.hashtags,
            mentions=content_data.mentions,
            scheduled_publish_date=content_data.scheduled_publish_date,
            status="pending_approval"
        )

        db.add(content)
        await db.commit()
        await db.refresh(content)

        logger.info(f"Campaign content created: {content.id}")
        return CampaignContentResponse.model_validate(content)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create campaign content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign content"
        )


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> CampaignAnalytics:
    """
    Get campaign analytics and performance metrics.

    Args:
        campaign_id: Campaign identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Campaign analytics data
    """
    try:
        # Verify campaign exists
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Get collaboration stats
        collab_query = select(
            func.count(Collaboration.id).label('total_collaborations'),
            func.count(func.nullif(Collaboration.status == 'completed', False)).label('completed_collaborations')
        ).where(Collaboration.campaign_id == campaign_id)
        collab_result = await db.execute(collab_query)
        collab_stats = collab_result.first()

        # Get content stats
        content_query = select(
            func.count(CampaignContent.id).label('total_content'),
            func.count(func.nullif(CampaignContent.status == 'published', False)).label('published_content'),
            func.sum(CampaignContent.engagement_rate).label('total_engagement'),
            func.sum(CampaignContent.reach).label('total_reach')
        ).where(CampaignContent.campaign_id == campaign_id)
        content_result = await db.execute(content_query)
        content_stats = content_result.first()

        # Calculate metrics
        avg_engagement = 0
        if content_stats.published_content and content_stats.total_engagement:
            avg_engagement = content_stats.total_engagement / content_stats.published_content

        return CampaignAnalytics(
            campaign_id=campaign_id,
            total_collaborations=collab_stats.total_collaborations or 0,
            completed_collaborations=collab_stats.completed_collaborations or 0,
            total_content=content_stats.total_content or 0,
            published_content=content_stats.published_content or 0,
            total_reach=content_stats.total_reach or 0,
            avg_engagement_rate=round(avg_engagement, 2),
            budget_spent=0,  # Would calculate from actual spending
            roi=0,  # Would calculate from performance data
            generated_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign analytics {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign analytics"
        )


@router.post("/{campaign_id}/workflow", response_model=Dict[str, Any])
async def execute_workflow_action(
    campaign_id: int = Path(..., description="Campaign ID"),
    action: CampaignWorkflowAction = None,
    db: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute campaign workflow action.

    Args:
        campaign_id: Campaign identifier
        action: Workflow action to execute
        db: Database session
        current_user: Current authenticated user

    Returns:
        Workflow execution result
    """
    try:
        # Get campaign
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        # Execute workflow action
        if action.action == "launch":
            if campaign.status != "draft":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign must be in draft status to launch"
                )
            campaign.status = "active"
            campaign.actual_start_date = datetime.utcnow()

            # Schedule performance monitoring
            monitor_campaign_performance.delay(campaign_id)

        elif action.action == "pause":
            if campaign.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign must be active to pause"
                )
            campaign.status = "paused"

        elif action.action == "complete":
            if campaign.status not in ["active", "paused"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign must be active or paused to complete"
                )
            campaign.status = "completed"
            campaign.actual_end_date = datetime.utcnow()

        elif action.action == "approve":
            if campaign.status != "pending_approval":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign must be pending approval"
                )
            campaign.status = "approved"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown workflow action: {action.action}"
            )

        campaign.updated_at = datetime.utcnow()
        campaign.updated_by = current_user.id

        await db.commit()

        logger.info(f"Campaign workflow action executed: {campaign_id} - {action.action}")
        return {
            "success": True,
            "action": action.action,
            "campaign_id": campaign_id,
            "new_status": campaign.status,
            "executed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to execute workflow action for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow action"
        )