"""Client Brief management service."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select, func, or_
from fastapi import HTTPException, status
from app.models.client_brief import ClientBrief, ClientBriefStatus


class ClientBriefService:
    """Service for client brief management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_brief(
        self,
        client_name: str,
        campaign_objective: str,
        target_audience: Optional[dict] = None,
        budget: Optional[float] = None,
        currency: str = "USD",
        brand_guidelines: Optional[str] = None,
        content_requirements: Optional[str] = None,
        campaign_start_date: Optional[datetime] = None,
        campaign_end_date: Optional[datetime] = None,
        content_deadline: Optional[datetime] = None,
        platform_requirements: Optional[dict] = None,
        kol_requirements: Optional[dict] = None,
        deliverable_requirements: Optional[dict] = None,
        created_by: int = None
    ) -> ClientBrief:
        """
        Create a new client brief.
        
        Args:
            client_name: Name of the client
            campaign_objective: Main objective of the campaign
            target_audience: Target audience details
            budget: Campaign budget
            currency: Budget currency
            brand_guidelines: Brand guidelines and requirements
            content_requirements: Content creation requirements
            campaign_start_date: Desired campaign start date
            campaign_end_date: Desired campaign end date
            content_deadline: Content submission deadline
            platform_requirements: Platform-specific requirements
            kol_requirements: KOL selection requirements
            deliverable_requirements: Deliverable specifications
            created_by: User ID who created the brief
            
        Returns:
            Created ClientBrief object
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate required fields
        if not client_name or not client_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client name is required"
            )
        
        if not campaign_objective or not campaign_objective.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign objective is required"
            )
        
        # Validate date logic
        if campaign_start_date and campaign_end_date:
            if campaign_start_date >= campaign_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign end date must be after start date"
                )
        
        if content_deadline and campaign_start_date:
            if content_deadline >= campaign_start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content deadline must be before campaign start date"
                )
        
        # Create brief
        brief = ClientBrief(
            client_name=client_name.strip(),
            campaign_objective=campaign_objective.strip(),
            target_audience=target_audience,
            budget=budget,
            currency=currency,
            brand_guidelines=brand_guidelines,
            content_requirements=content_requirements,
            campaign_start_date=campaign_start_date,
            campaign_end_date=campaign_end_date,
            content_deadline=content_deadline,
            platform_requirements=platform_requirements,
            kol_requirements=kol_requirements,
            deliverable_requirements=deliverable_requirements,
            created_by=created_by
        )
        
        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        
        return brief
    
    def get_brief(self, brief_id: int) -> Optional[ClientBrief]:
        """
        Get client brief by ID.
        
        Args:
            brief_id: Brief ID
            
        Returns:
            ClientBrief object or None if not found
        """
        return self.db.get(ClientBrief, brief_id)
    
    def list_briefs(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        client_name: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[ClientBrief], int]:
        """
        List client briefs with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search query for client name or objective
            client_name: Filter by client name
            status: Filter by status
            created_by: Filter by creator
            sort_by: Field to sort by
            sort_order: Sort order (asc, desc)
            
        Returns:
            Tuple of (briefs list, total count)
        """
        # Base query
        statement = select(ClientBrief)
        
        # Apply search
        if search:
            statement = statement.where(
                or_(
                    ClientBrief.client_name.ilike(f"%{search}%"),
                    ClientBrief.campaign_objective.ilike(f"%{search}%")
                )
            )
        
        # Apply filters
        if client_name:
            statement = statement.where(ClientBrief.client_name.ilike(f"%{client_name}%"))
        if status:
            statement = statement.where(ClientBrief.status == status)
        if created_by:
            statement = statement.where(ClientBrief.created_by == created_by)
        
        # Get total count with same filters
        count_statement = select(func.count(ClientBrief.id))
        if search:
            count_statement = count_statement.where(
                or_(
                    ClientBrief.client_name.ilike(f"%{search}%"),
                    ClientBrief.campaign_objective.ilike(f"%{search}%")
                )
            )
        if client_name:
            count_statement = count_statement.where(ClientBrief.client_name.ilike(f"%{client_name}%"))
        if status:
            count_statement = count_statement.where(ClientBrief.status == status)
        if created_by:
            count_statement = count_statement.where(ClientBrief.created_by == created_by)
        
        total = self.db.exec(count_statement).one()
        
        # Apply sorting
        sort_column = getattr(ClientBrief, sort_by, ClientBrief.created_at)
        if sort_order.lower() == "asc":
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        briefs = self.db.exec(statement).all()
        
        return list(briefs), total
    
    def update_brief(
        self,
        brief_id: int,
        client_name: Optional[str] = None,
        campaign_objective: Optional[str] = None,
        target_audience: Optional[dict] = None,
        budget: Optional[float] = None,
        currency: Optional[str] = None,
        brand_guidelines: Optional[str] = None,
        content_requirements: Optional[str] = None,
        campaign_start_date: Optional[datetime] = None,
        campaign_end_date: Optional[datetime] = None,
        content_deadline: Optional[datetime] = None,
        platform_requirements: Optional[dict] = None,
        kol_requirements: Optional[dict] = None,
        deliverable_requirements: Optional[dict] = None,
        status: Optional[str] = None
    ) -> ClientBrief:
        """
        Update client brief information.
        
        Args:
            brief_id: Brief ID
            client_name: New client name
            campaign_objective: New campaign objective
            target_audience: New target audience
            budget: New budget
            currency: New currency
            brand_guidelines: New brand guidelines
            content_requirements: New content requirements
            campaign_start_date: New campaign start date
            campaign_end_date: New campaign end date
            content_deadline: New content deadline
            platform_requirements: New platform requirements
            kol_requirements: New KOL requirements
            deliverable_requirements: New deliverable requirements
            status: New status
            
        Returns:
            Updated ClientBrief object
            
        Raises:
            HTTPException: If brief not found or validation fails
        """
        brief = self.get_brief(brief_id)
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client brief not found"
            )
        
        # Update fields
        if client_name is not None:
            if not client_name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client name cannot be empty"
                )
            brief.client_name = client_name.strip()
        
        if campaign_objective is not None:
            if not campaign_objective.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign objective cannot be empty"
                )
            brief.campaign_objective = campaign_objective.strip()
        
        if target_audience is not None:
            brief.target_audience = target_audience
        if budget is not None:
            brief.budget = budget
        if currency is not None:
            brief.currency = currency
        if brand_guidelines is not None:
            brief.brand_guidelines = brand_guidelines
        if content_requirements is not None:
            brief.content_requirements = content_requirements
        if campaign_start_date is not None:
            brief.campaign_start_date = campaign_start_date
        if campaign_end_date is not None:
            brief.campaign_end_date = campaign_end_date
        if content_deadline is not None:
            brief.content_deadline = content_deadline
        if platform_requirements is not None:
            brief.platform_requirements = platform_requirements
        if kol_requirements is not None:
            brief.kol_requirements = kol_requirements
        if deliverable_requirements is not None:
            brief.deliverable_requirements = deliverable_requirements
        if status is not None:
            brief.status = status
        
        # Validate date logic after updates
        if brief.campaign_start_date and brief.campaign_end_date:
            if brief.campaign_start_date >= brief.campaign_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Campaign end date must be after start date"
                )
        
        if brief.content_deadline and brief.campaign_start_date:
            if brief.content_deadline >= brief.campaign_start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content deadline must be before campaign start date"
                )
        
        brief.updated_at = datetime.utcnow()
        
        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        
        return brief
    
    def approve_brief(self, brief_id: int, approved_by: int) -> ClientBrief:
        """
        Approve a client brief.
        
        Args:
            brief_id: Brief ID
            approved_by: User ID who approved the brief
            
        Returns:
            Updated ClientBrief object
            
        Raises:
            HTTPException: If brief not found or cannot be approved
        """
        brief = self.get_brief(brief_id)
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client brief not found"
            )
        
        if brief.status not in [ClientBriefStatus.SUBMITTED, ClientBriefStatus.REVISION_REQUESTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brief must be submitted or revision requested to be approved"
            )
        
        brief.status = ClientBriefStatus.APPROVED
        brief.approved_by = approved_by
        brief.approved_at = datetime.utcnow()
        brief.updated_at = datetime.utcnow()
        
        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        
        return brief
    
    def reject_brief(self, brief_id: int, rejection_reason: str) -> ClientBrief:
        """
        Reject a client brief.
        
        Args:
            brief_id: Brief ID
            rejection_reason: Reason for rejection
            
        Returns:
            Updated ClientBrief object
            
        Raises:
            HTTPException: If brief not found or cannot be rejected
        """
        brief = self.get_brief(brief_id)
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client brief not found"
            )
        
        if brief.status != ClientBriefStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only submitted briefs can be rejected"
            )
        
        brief.status = ClientBriefStatus.REJECTED
        brief.rejection_reason = rejection_reason
        brief.updated_at = datetime.utcnow()
        
        self.db.add(brief)
        self.db.commit()
        self.db.refresh(brief)
        
        return brief