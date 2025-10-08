"""Campaign management service."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select, func
from fastapi import HTTPException, status
from app.models.campaign import Campaign
from app.models.campaign_kpi import CampaignKPI
from app.models.deliverable import Deliverable


class CampaignService:
    """Service for campaign management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(
        self,
        name: str,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        total_budget: Optional[float] = None,
        currency: str = "USD",
        objectives: Optional[str] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        kpis: List[Dict[str, Any]] = [],
        deliverables: List[Dict[str, Any]] = []
    ) -> Campaign:
        """Create a new campaign."""
        # Validate dates
        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        # Validate budget
        if total_budget is not None and total_budget < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Budget must be positive"
            )
        
        # Create campaign
        campaign = Campaign(
            name=name,
            start_date=start_date,
            end_date=end_date,
            total_budget=total_budget,
            currency=currency,
            objectives=objectives,
            target_audience=target_audience,
            created_by=user_id
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Create KPIs
        for kpi_data in kpis:
            kpi = CampaignKPI(campaign_id=campaign.id, **kpi_data)
            self.db.add(kpi)
        
        # Create deliverables
        for deliverable_data in deliverables:
            deliverable = Deliverable(campaign_id=campaign.id, **deliverable_data)
            self.db.add(deliverable)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID."""
        return self.db.get(Campaign, campaign_id)
    
    def list_campaigns(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> tuple[List[Campaign], int]:
        """List campaigns with pagination and filters."""
        statement = select(Campaign)
        
        # Apply filters
        if status:
            statement = statement.where(Campaign.status == status)
        if created_by:
            statement = statement.where(Campaign.created_by == created_by)
        
        # Get total count
        count_statement = select(func.count()).select_from(Campaign)
        if status:
            count_statement = count_statement.where(Campaign.status == status)
        if created_by:
            count_statement = count_statement.where(Campaign.created_by == created_by)
        total = self.db.exec(count_statement).one()
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        campaigns = self.db.exec(statement).all()
        
        return list(campaigns), total
    
    def update_campaign(
        self,
        campaign_id: int,
        name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        total_budget: Optional[float] = None,
        currency: Optional[str] = None,
        objectives: Optional[str] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None
    ) -> Campaign:
        """Update campaign information."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update fields
        if name is not None:
            campaign.name = name
        if start_date is not None:
            campaign.start_date = start_date
        if end_date is not None:
            campaign.end_date = end_date
        if total_budget is not None:
            if total_budget < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Budget must be positive"
                )
            campaign.total_budget = total_budget
        if currency is not None:
            campaign.currency = currency
        if objectives is not None:
            campaign.objectives = objectives
        if target_audience is not None:
            campaign.target_audience = target_audience
        if status is not None:
            campaign.status = status
        
        # Validate dates
        if campaign.start_date and campaign.end_date and campaign.end_date < campaign.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        campaign.updated_at = datetime.utcnow()
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def delete_campaign(self, campaign_id: int) -> None:
        """Delete campaign (soft delete)."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        if campaign.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active campaign"
            )
        
        campaign.status = "cancelled"
        campaign.updated_at = datetime.utcnow()
        
        self.db.add(campaign)
        self.db.commit()
    
    def change_status(self, campaign_id: int, new_status: str) -> Campaign:
        """Change campaign status."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Define allowed transitions
        allowed_transitions = {
            "draft": ["pending_approval", "cancelled"],
            "pending_approval": ["active", "draft", "cancelled"],
            "active": ["completed", "cancelled"],
            "completed": [],
            "cancelled": []
        }
        
        if new_status not in allowed_transitions.get(campaign.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {campaign.status} to {new_status}"
            )
        
        campaign.status = new_status
        campaign.updated_at = datetime.utcnow()
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def add_kpi(self, campaign_id: int, kpi_type: str, target_value: float, unit: str) -> CampaignKPI:
        """Add KPI to campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        kpi = CampaignKPI(
            campaign_id=campaign_id,
            kpi_type=kpi_type,
            target_value=target_value,
            unit=unit
        )
        
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        
        return kpi
    
    def add_deliverable(
        self,
        campaign_id: int,
        deliverable_type: str,
        quantity: int,
        deadline: Optional[date] = None
    ) -> Deliverable:
        """Add deliverable to campaign."""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        deliverable = Deliverable(
            campaign_id=campaign_id,
            deliverable_type=deliverable_type,
            quantity=quantity,
            deadline=deadline
        )
        
        self.db.add(deliverable)
        self.db.commit()
        self.db.refresh(deliverable)
        
        return deliverable
    
    def duplicate_campaign(self, campaign_id: int) -> Campaign:
        """Duplicate campaign."""
        original = self.get_campaign(campaign_id)
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Create duplicate
        duplicate = Campaign(
            name=f"{original.name} (Copy)",
            status="draft",
            total_budget=original.total_budget,
            currency=original.currency,
            objectives=original.objectives,
            target_audience=original.target_audience,
            created_by=original.created_by
        )
        
        self.db.add(duplicate)
        self.db.commit()
        self.db.refresh(duplicate)
        
        # Copy KPIs
        for kpi in original.kpis:
            new_kpi = CampaignKPI(
                campaign_id=duplicate.id,
                kpi_type=kpi.kpi_type,
                target_value=kpi.target_value,
                unit=kpi.unit
            )
            self.db.add(new_kpi)
        
        # Copy deliverables
        for deliverable in original.deliverables:
            new_deliverable = Deliverable(
                campaign_id=duplicate.id,
                deliverable_type=deliverable.deliverable_type,
                quantity=deliverable.quantity
            )
            self.db.add(new_deliverable)
        
        self.db.commit()
        self.db.refresh(duplicate)
        
        return duplicate
