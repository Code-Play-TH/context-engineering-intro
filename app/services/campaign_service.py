"""Campaign management service."""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlmodel import Session, select, func, or_
from fastapi import HTTPException, status
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_kol import CampaignKOL
from app.models.campaign_kpi import CampaignKPI
from app.models.deliverable import Deliverable


class CampaignService:
    """Service for campaign management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(
        self,
        name: str,
        objectives: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        total_budget: Optional[Decimal] = None,
        currency: str = "USD",
        target_audience: Optional[dict] = None,
        brief_deadline: Optional[date] = None,
        content_deadline: Optional[date] = None,
        posting_start_date: Optional[date] = None,
        posting_end_date: Optional[date] = None,
        report_due_date: Optional[date] = None,
        created_by: int = None
    ) -> Campaign:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name
            objectives: Campaign objectives
            start_date: Campaign start date
            end_date: Campaign end date
            total_budget: Total campaign budget
            currency: Budget currency
            target_audience: Target audience details
            brief_deadline: Brief submission deadline
            content_deadline: Content creation deadline
            posting_start_date: Content posting start date
            posting_end_date: Content posting end date
            report_due_date: Final report due date
            created_by: User ID who created the campaign
            
        Returns:
            Created Campaign object
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate required fields
        if not name or not name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign name is required"
            )
        
        # Validate date logic
        if start_date and end_date:
            if start_date >= end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign end date must be after start date"
                )
        
        if brief_deadline and start_date:
            if brief_deadline >= start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Brief deadline must be before campaign start date"
                )
        
        if content_deadline and start_date:
            if content_deadline >= start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content deadline must be before campaign start date"
                )
        
        if posting_start_date and posting_end_date:
            if posting_start_date >= posting_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Posting end date must be after posting start date"
                )
        
        # Validate budget
        if total_budget is not None and total_budget < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Budget cannot be negative"
            )
        
        # Create campaign
        campaign = Campaign(
            name=name.strip(),
            objectives=objectives,
            start_date=start_date,
            end_date=end_date,
            total_budget=total_budget,
            currency=currency,
            target_audience=target_audience,
            brief_deadline=brief_deadline,
            content_deadline=content_deadline,
            posting_start_date=posting_start_date,
            posting_end_date=posting_end_date,
            report_due_date=report_due_date,
            created_by=created_by
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """
        Get campaign by ID with relationships.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign object or None if not found
        """
        return self.db.get(Campaign, campaign_id)
    
    def list_campaigns(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        start_date_from: Optional[date] = None,
        start_date_to: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Campaign], int]:
        """
        List campaigns with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search query for campaign name or objectives
            status: Filter by status
            created_by: Filter by creator
            start_date_from: Filter campaigns starting from this date
            start_date_to: Filter campaigns starting before this date
            sort_by: Field to sort by
            sort_order: Sort order (asc, desc)
            
        Returns:
            Tuple of (campaigns list, total count)
        """
        # Base query
        statement = select(Campaign)
        
        # Apply search
        if search:
            statement = statement.where(
                or_(
                    Campaign.name.ilike(f"%{search}%"),
                    Campaign.objectives.ilike(f"%{search}%")
                )
            )
        
        # Apply filters
        if status:
            statement = statement.where(Campaign.status == status)
        if created_by:
            statement = statement.where(Campaign.created_by == created_by)
        if start_date_from:
            statement = statement.where(Campaign.start_date >= start_date_from)
        if start_date_to:
            statement = statement.where(Campaign.start_date <= start_date_to)
        
        # Get total count with same filters
        count_statement = select(func.count(Campaign.id))
        if search:
            count_statement = count_statement.where(
                or_(
                    Campaign.name.ilike(f"%{search}%"),
                    Campaign.objectives.ilike(f"%{search}%")
                )
            )
        if status:
            count_statement = count_statement.where(Campaign.status == status)
        if created_by:
            count_statement = count_statement.where(Campaign.created_by == created_by)
        if start_date_from:
            count_statement = count_statement.where(Campaign.start_date >= start_date_from)
        if start_date_to:
            count_statement = count_statement.where(Campaign.start_date <= start_date_to)
        
        total = self.db.exec(count_statement).one()
        
        # Apply sorting
        sort_column = getattr(Campaign, sort_by, Campaign.created_at)
        if sort_order.lower() == "asc":
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        campaigns = self.db.exec(statement).all()
        
        return list(campaigns), total
    
    def update_campaign(
        self,
        campaign_id: int,
        name: Optional[str] = None,
        objectives: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        total_budget: Optional[Decimal] = None,
        currency: Optional[str] = None,
        target_audience: Optional[dict] = None,
        brief_deadline: Optional[date] = None,
        content_deadline: Optional[date] = None,
        posting_start_date: Optional[date] = None,
        posting_end_date: Optional[date] = None,
        report_due_date: Optional[date] = None,
        status: Optional[str] = None
    ) -> Campaign:
        """
        Update campaign information.
        
        Args:
            campaign_id: Campaign ID
            name: New campaign name
            objectives: New objectives
            start_date: New start date
            end_date: New end date
            total_budget: New budget
            currency: New currency
            target_audience: New target audience
            brief_deadline: New brief deadline
            content_deadline: New content deadline
            posting_start_date: New posting start date
            posting_end_date: New posting end date
            report_due_date: New report due date
            status: New status
            
        Returns:
            Updated Campaign object
            
        Raises:
            HTTPException: If campaign not found or validation fails
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update fields
        if name is not None:
            if not name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign name cannot be empty"
                )
            campaign.name = name.strip()
        
        if objectives is not None:
            campaign.objectives = objectives
        if start_date is not None:
            campaign.start_date = start_date
        if end_date is not None:
            campaign.end_date = end_date
        if total_budget is not None:
            if total_budget < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Budget cannot be negative"
                )
            campaign.total_budget = total_budget
        if currency is not None:
            campaign.currency = currency
        if target_audience is not None:
            campaign.target_audience = target_audience
        if brief_deadline is not None:
            campaign.brief_deadline = brief_deadline
        if content_deadline is not None:
            campaign.content_deadline = content_deadline
        if posting_start_date is not None:
            campaign.posting_start_date = posting_start_date
        if posting_end_date is not None:
            campaign.posting_end_date = posting_end_date
        if report_due_date is not None:
            campaign.report_due_date = report_due_date
        if status is not None:
            campaign.status = status
        
        # Validate date logic after updates
        if campaign.start_date and campaign.end_date:
            if campaign.start_date >= campaign.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign end date must be after start date"
                )
        
        if campaign.brief_deadline and campaign.start_date:
            if campaign.brief_deadline >= campaign.start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Brief deadline must be before campaign start date"
                )
        
        if campaign.content_deadline and campaign.start_date:
            if campaign.content_deadline >= campaign.start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content deadline must be before campaign start date"
                )
        
        if campaign.posting_start_date and campaign.posting_end_date:
            if campaign.posting_start_date >= campaign.posting_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Posting end date must be after posting start date"
                )
        
        campaign.updated_at = datetime.utcnow()
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def delete_campaign(self, campaign_id: int) -> Campaign:
        """
        Soft delete campaign by setting status to cancelled.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Deleted Campaign object
            
        Raises:
            HTTPException: If campaign not found or cannot be deleted
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Check if campaign can be deleted
        if campaign.status == CampaignStatus.ACTIVE:
            # Check if there are active KOLs
            active_kols = self.db.exec(
                select(func.count(CampaignKOL.id)).where(
                    CampaignKOL.campaign_id == campaign_id,
                    CampaignKOL.status.in_(["active", "contracted"])
                )
            ).one()
            
            if active_kols > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete campaign with {active_kols} active KOLs"
                )
        
        campaign.status = CampaignStatus.CANCELLED
        campaign.updated_at = datetime.utcnow()
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def change_status(self, campaign_id: int, new_status: str, user_id: int) -> Campaign:
        """
        Change campaign status with validation.
        
        Args:
            campaign_id: Campaign ID
            new_status: New status
            user_id: User making the change
            
        Returns:
            Updated Campaign object
            
        Raises:
            HTTPException: If campaign not found or status change not allowed
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Define allowed status transitions
        allowed_transitions = {
            CampaignStatus.DRAFT: [CampaignStatus.PENDING_APPROVAL, CampaignStatus.CANCELLED],
            CampaignStatus.PENDING_APPROVAL: [CampaignStatus.ACTIVE, CampaignStatus.DRAFT, CampaignStatus.CANCELLED],
            CampaignStatus.ACTIVE: [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED],
            CampaignStatus.COMPLETED: [],  # Cannot change from completed
            CampaignStatus.CANCELLED: [CampaignStatus.DRAFT]  # Can reactivate cancelled campaigns
        }
        
        current_status = CampaignStatus(campaign.status)
        new_status_enum = CampaignStatus(new_status)
        
        if new_status_enum not in allowed_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from {current_status.value} to {new_status_enum.value}"
            )
        
        campaign.status = new_status_enum
        campaign.updated_at = datetime.utcnow()
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def get_campaign_summary(self, campaign_id: int) -> dict:
        """
        Get campaign summary with statistics.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with campaign summary
            
        Raises:
            HTTPException: If campaign not found
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get KOL statistics
        kol_stats = self.db.exec(
            select(
                func.count(CampaignKOL.id).label("total_kols"),
                func.count(CampaignKOL.id).filter(CampaignKOL.status == "active").label("active_kols"),
                func.count(CampaignKOL.id).filter(CampaignKOL.status == "completed").label("completed_kols")
            ).where(CampaignKOL.campaign_id == campaign_id)
        ).first()
        
        # Get deliverable statistics
        deliverable_stats = self.db.exec(
            select(
                func.count(Deliverable.id).label("total_deliverables"),
                func.count(Deliverable.id).filter(Deliverable.status == "completed").label("completed_deliverables"),
                func.count(Deliverable.id).filter(Deliverable.status == "overdue").label("overdue_deliverables")
            ).where(Deliverable.campaign_id == campaign_id)
        ).first()
        
        # Get KPI statistics
        kpi_stats = self.db.exec(
            select(
                func.count(CampaignKPI.id).label("total_kpis"),
                func.count(CampaignKPI.id).filter(CampaignKPI.is_achieved == True).label("achieved_kpis"),
                func.avg(CampaignKPI.achievement_percentage).label("avg_achievement")
            ).where(CampaignKPI.campaign_id == campaign_id)
        ).first()
        
        return {
            "campaign": campaign,
            "kol_stats": {
                "total": kol_stats.total_kols or 0,
                "active": kol_stats.active_kols or 0,
                "completed": kol_stats.completed_kols or 0
            },
            "deliverable_stats": {
                "total": deliverable_stats.total_deliverables or 0,
                "completed": deliverable_stats.completed_deliverables or 0,
                "overdue": deliverable_stats.overdue_deliverables or 0
            },
            "kpi_stats": {
                "total": kpi_stats.total_kpis or 0,
                "achieved": kpi_stats.achieved_kpis or 0,
                "avg_achievement": float(kpi_stats.avg_achievement or 0)
            }
        }
    
    def add_kpi(
        self,
        campaign_id: int,
        kpi_type: str,
        target_value: Decimal,
        unit: str,
        description: Optional[str] = None,
        priority: str = "medium"
    ) -> CampaignKPI:
        """
        Add KPI to campaign.
        
        Args:
            campaign_id: Campaign ID
            kpi_type: Type of KPI
            target_value: Target value for the KPI
            unit: Unit of measurement
            description: Optional description
            priority: Priority level
            
        Returns:
            Created CampaignKPI object
            
        Raises:
            HTTPException: If campaign not found or validation fails
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Validate target value
        if target_value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target value must be positive"
            )
        
        # Check for duplicate KPI type
        existing_kpi = self.db.exec(
            select(CampaignKPI).where(
                CampaignKPI.campaign_id == campaign_id,
                CampaignKPI.kpi_type == kpi_type
            )
        ).first()
        
        if existing_kpi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"KPI of type '{kpi_type}' already exists for this campaign"
            )
        
        kpi = CampaignKPI(
            campaign_id=campaign_id,
            kpi_type=kpi_type,
            target_value=target_value,
            unit=unit,
            description=description,
            priority=priority
        )
        
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        
        return kpi
    
    def update_kpi(
        self,
        kpi_id: int,
        target_value: Optional[Decimal] = None,
        actual_value: Optional[Decimal] = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None
    ) -> CampaignKPI:
        """
        Update KPI information.
        
        Args:
            kpi_id: KPI ID
            target_value: New target value
            actual_value: New actual value
            unit: New unit
            description: New description
            priority: New priority
            
        Returns:
            Updated CampaignKPI object
            
        Raises:
            HTTPException: If KPI not found or validation fails
        """
        kpi = self.db.get(CampaignKPI, kpi_id)
        if not kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI not found"
            )
        
        # Update fields
        if target_value is not None:
            if target_value <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target value must be positive"
                )
            kpi.target_value = target_value
        
        if actual_value is not None:
            if actual_value < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Actual value cannot be negative"
                )
            kpi.actual_value = actual_value
        
        if unit is not None:
            kpi.unit = unit
        if description is not None:
            kpi.description = description
        if priority is not None:
            kpi.priority = priority
        
        # Update achievement status
        kpi.update_achievement()
        
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        
        return kpi
    
    def delete_kpi(self, kpi_id: int) -> None:
        """
        Delete KPI.
        
        Args:
            kpi_id: KPI ID
            
        Raises:
            HTTPException: If KPI not found
        """
        kpi = self.db.get(CampaignKPI, kpi_id)
        if not kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI not found"
            )
        
        self.db.delete(kpi)
        self.db.commit()
    
    def add_deliverable(
        self,
        campaign_id: int,
        deliverable_type: str,
        quantity: int = 1,
        deadline: Optional[date] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        platform_specific_requirements: Optional[str] = None,
        hashtags: Optional[str] = None,
        mentions: Optional[str] = None,
        priority: str = "medium"
    ) -> Deliverable:
        """
        Add deliverable to campaign.
        
        Args:
            campaign_id: Campaign ID
            deliverable_type: Type of deliverable
            quantity: Number of deliverables required
            deadline: Deadline for completion
            title: Deliverable title
            description: Deliverable description
            platform_specific_requirements: Platform-specific requirements
            hashtags: Required hashtags
            mentions: Required mentions
            priority: Priority level
            
        Returns:
            Created Deliverable object
            
        Raises:
            HTTPException: If campaign not found or validation fails
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Validate quantity
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be positive"
            )
        
        # Validate deadline
        if deadline and campaign.end_date and deadline > campaign.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deliverable deadline cannot be after campaign end date"
            )
        
        deliverable = Deliverable(
            campaign_id=campaign_id,
            deliverable_type=deliverable_type,
            quantity=quantity,
            deadline=deadline,
            title=title,
            description=description,
            platform_specific_requirements=platform_specific_requirements,
            hashtags=hashtags,
            mentions=mentions,
            priority=priority
        )
        
        self.db.add(deliverable)
        self.db.commit()
        self.db.refresh(deliverable)
        
        return deliverable
    
    def update_deliverable(
        self,
        deliverable_id: int,
        quantity: Optional[int] = None,
        deadline: Optional[date] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        platform_specific_requirements: Optional[str] = None,
        hashtags: Optional[str] = None,
        mentions: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        submitted_count: Optional[int] = None,
        approved_count: Optional[int] = None,
        published_count: Optional[int] = None,
        reviewer_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None
    ) -> Deliverable:
        """
        Update deliverable information.
        
        Args:
            deliverable_id: Deliverable ID
            quantity: New quantity
            deadline: New deadline
            title: New title
            description: New description
            platform_specific_requirements: New platform requirements
            hashtags: New hashtags
            mentions: New mentions
            priority: New priority
            status: New status
            submitted_count: New submitted count
            approved_count: New approved count
            published_count: New published count
            reviewer_notes: New reviewer notes
            rejection_reason: New rejection reason
            
        Returns:
            Updated Deliverable object
            
        Raises:
            HTTPException: If deliverable not found or validation fails
        """
        deliverable = self.db.get(Deliverable, deliverable_id)
        if not deliverable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deliverable not found"
            )
        
        # Update fields
        if quantity is not None:
            if quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be positive"
                )
            deliverable.quantity = quantity
        
        if deadline is not None:
            deliverable.deadline = deadline
        if title is not None:
            deliverable.title = title
        if description is not None:
            deliverable.description = description
        if platform_specific_requirements is not None:
            deliverable.platform_specific_requirements = platform_specific_requirements
        if hashtags is not None:
            deliverable.hashtags = hashtags
        if mentions is not None:
            deliverable.mentions = mentions
        if priority is not None:
            deliverable.priority = priority
        if status is not None:
            deliverable.status = status
        if submitted_count is not None:
            deliverable.submitted_count = max(0, submitted_count)
        if approved_count is not None:
            deliverable.approved_count = max(0, approved_count)
        if published_count is not None:
            deliverable.published_count = max(0, published_count)
        if reviewer_notes is not None:
            deliverable.reviewer_notes = reviewer_notes
        if rejection_reason is not None:
            deliverable.rejection_reason = rejection_reason
        
        # Update progress
        deliverable.update_progress()
        
        self.db.add(deliverable)
        self.db.commit()
        self.db.refresh(deliverable)
        
        return deliverable
    
    def delete_deliverable(self, deliverable_id: int) -> None:
        """
        Delete deliverable.
        
        Args:
            deliverable_id: Deliverable ID
            
        Raises:
            HTTPException: If deliverable not found
        """
        deliverable = self.db.get(Deliverable, deliverable_id)
        if not deliverable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deliverable not found"
            )
        
        self.db.delete(deliverable)
        self.db.commit()
    
    def duplicate_campaign(self, campaign_id: int, new_name: Optional[str] = None) -> Campaign:
        """
        Duplicate campaign with all KPIs and deliverables.
        
        Args:
            campaign_id: Campaign ID to duplicate
            new_name: Optional new name for duplicated campaign
            
        Returns:
            Duplicated Campaign object
            
        Raises:
            HTTPException: If campaign not found
        """
        original_campaign = self.get_campaign(campaign_id)
        if not original_campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Create new campaign (exclude dates and status)
        duplicate_name = new_name or f"{original_campaign.name} (Copy)"
        
        new_campaign = Campaign(
            name=duplicate_name,
            objectives=original_campaign.objectives,
            total_budget=original_campaign.total_budget,
            currency=original_campaign.currency,
            target_audience=original_campaign.target_audience,
            status=CampaignStatus.DRAFT,  # Always start as draft
            created_by=original_campaign.created_by,
            kol_count=0  # Reset KOL count
        )
        
        self.db.add(new_campaign)
        self.db.commit()
        self.db.refresh(new_campaign)
        
        # Duplicate KPIs
        original_kpis = self.db.exec(
            select(CampaignKPI).where(CampaignKPI.campaign_id == campaign_id)
        ).all()
        
        for kpi in original_kpis:
            new_kpi = CampaignKPI(
                campaign_id=new_campaign.id,
                kpi_type=kpi.kpi_type,
                target_value=kpi.target_value,
                unit=kpi.unit,
                description=kpi.description,
                priority=kpi.priority
            )
            self.db.add(new_kpi)
        
        # Duplicate Deliverables
        original_deliverables = self.db.exec(
            select(Deliverable).where(Deliverable.campaign_id == campaign_id)
        ).all()
        
        for deliverable in original_deliverables:
            new_deliverable = Deliverable(
                campaign_id=new_campaign.id,
                deliverable_type=deliverable.deliverable_type,
                quantity=deliverable.quantity,
                title=deliverable.title,
                description=deliverable.description,
                platform_specific_requirements=deliverable.platform_specific_requirements,
                hashtags=deliverable.hashtags,
                mentions=deliverable.mentions,
                priority=deliverable.priority
                # Reset all progress fields to defaults
            )
            self.db.add(new_deliverable)
        
        self.db.commit()
        self.db.refresh(new_campaign)
        
        return new_campaign