"""KOL management service."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select, func, or_
from fastapi import HTTPException, status
from app.models.kol import KOL
from app.models.social_handle import SocialHandle


class KOLService:
    """Service for KOL management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_kol(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        niche: List[str] = [],
        tags: List[str] = [],
        notes: Optional[str] = None,
        social_handles: List[dict] = []
    ) -> KOL:
        """
        Create a new KOL.
        
        Args:
            name: KOL name
            email: KOL email
            phone: KOL phone
            location: KOL location
            niche: List of niches
            tags: List of tags
            notes: Additional notes
            social_handles: List of social media handles
            
        Returns:
            Created KOL object
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate at least one social handle
        if not social_handles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one social media handle is required"
            )
        
        # Create KOL
        kol = KOL(
            name=name,
            email=email,
            phone=phone,
            location=location,
            niche=niche,
            tags=tags,
            notes=notes
        )
        
        self.db.add(kol)
        self.db.commit()
        self.db.refresh(kol)
        
        # Create social handles
        for handle_data in social_handles:
            handle = SocialHandle(
                kol_id=kol.id,
                **handle_data
            )
            self.db.add(handle)
        
        self.db.commit()
        
        # Calculate tier
        self.calculate_tier(kol.id)
        
        self.db.refresh(kol)
        return kol
    
    def get_kol(self, kol_id: int) -> Optional[KOL]:
        """
        Get KOL by ID with social handles.
        
        Args:
            kol_id: KOL ID
            
        Returns:
            KOL object or None if not found
        """
        return self.db.get(KOL, kol_id)
    
    def list_kols(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        niche: Optional[str] = None,
        location: Optional[str] = None,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> tuple[List[KOL], int]:
        """
        List KOLs with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search query for name, email, or social handle
            niche: Filter by niche
            location: Filter by location
            tier: Filter by tier
            status: Filter by status
            tags: Filter by tags
            
        Returns:
            Tuple of (KOLs list, total count)
        """
        statement = select(KOL)
        
        # Apply search
        if search:
            statement = statement.where(
                or_(
                    KOL.name.ilike(f"%{search}%"),
                    KOL.email.ilike(f"%{search}%")
                )
            )
        
        # Apply filters
        if niche:
            statement = statement.where(KOL.niche.contains([niche]))
        if location:
            statement = statement.where(KOL.location.ilike(f"%{location}%"))
        if tier:
            statement = statement.where(KOL.tier == tier)
        if status:
            statement = statement.where(KOL.status == status)
        if tags:
            for tag in tags:
                statement = statement.where(KOL.tags.contains([tag]))
        
        # Get total count
        count_statement = select(func.count()).select_from(KOL)
        if search:
            count_statement = count_statement.where(
                or_(
                    KOL.name.ilike(f"%{search}%"),
                    KOL.email.ilike(f"%{search}%")
                )
            )
        if niche:
            count_statement = count_statement.where(KOL.niche.contains([niche]))
        if location:
            count_statement = count_statement.where(KOL.location.ilike(f"%{location}%"))
        if tier:
            count_statement = count_statement.where(KOL.tier == tier)
        if status:
            count_statement = count_statement.where(KOL.status == status)
        if tags:
            for tag in tags:
                count_statement = count_statement.where(KOL.tags.contains([tag]))
        
        total = self.db.exec(count_statement).one()
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        kols = self.db.exec(statement).all()
        
        return list(kols), total
    
    def update_kol(
        self,
        kol_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        niche: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        status: Optional[str] = None
    ) -> KOL:
        """
        Update KOL information.
        
        Args:
            kol_id: KOL ID
            name: New name
            email: New email
            phone: New phone
            location: New location
            niche: New niche list
            tags: New tags list
            notes: New notes
            status: New status
            
        Returns:
            Updated KOL object
            
        Raises:
            HTTPException: If KOL not found
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        # Update fields
        if name is not None:
            kol.name = name
        if email is not None:
            kol.email = email
        if phone is not None:
            kol.phone = phone
        if location is not None:
            kol.location = location
        if niche is not None:
            kol.niche = niche
        if tags is not None:
            kol.tags = tags
        if notes is not None:
            kol.notes = notes
        if status is not None:
            kol.status = status
        
        kol.updated_at = datetime.utcnow()
        
        self.db.add(kol)
        self.db.commit()
        self.db.refresh(kol)
        
        return kol
    
    def soft_delete_kol(self, kol_id: int) -> KOL:
        """
        Soft delete KOL by setting status to inactive.
        
        Args:
            kol_id: KOL ID
            
        Returns:
            Deleted KOL object
            
        Raises:
            HTTPException: If KOL not found
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        kol.status = "inactive"
        kol.updated_at = datetime.utcnow()
        
        self.db.add(kol)
        self.db.commit()
        self.db.refresh(kol)
        
        return kol
    
    def add_social_handle(
        self,
        kol_id: int,
        platform: str,
        handle: str,
        url: Optional[str] = None,
        follower_count: Optional[int] = None,
        is_verified: bool = False
    ) -> SocialHandle:
        """
        Add social media handle to KOL.
        
        Args:
            kol_id: KOL ID
            platform: Platform name
            handle: Handle/username
            url: Profile URL
            follower_count: Number of followers
            is_verified: Whether account is verified
            
        Returns:
            Created social handle object
            
        Raises:
            HTTPException: If KOL not found
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        social_handle = SocialHandle(
            kol_id=kol_id,
            platform=platform,
            handle=handle,
            url=url,
            follower_count=follower_count,
            is_verified=is_verified
        )
        
        self.db.add(social_handle)
        self.db.commit()
        self.db.refresh(social_handle)
        
        # Recalculate tier
        self.calculate_tier(kol_id)
        
        return social_handle
    
    def calculate_tier(self, kol_id: int) -> None:
        """
        Calculate and update KOL tier based on follower count.
        
        Tiers:
        - nano: < 10K followers
        - micro: 10K - 100K followers
        - mid: 100K - 500K followers
        - macro: 500K - 1M followers
        - mega: > 1M followers
        
        Args:
            kol_id: KOL ID
        """
        kol = self.get_kol(kol_id)
        if not kol:
            return
        
        # Get max follower count across all platforms
        statement = select(func.max(SocialHandle.follower_count)).where(
            SocialHandle.kol_id == kol_id,
            SocialHandle.is_active == True
        )
        max_followers = self.db.exec(statement).one()
        
        if max_followers is None:
            kol.tier = None
        elif max_followers < 10000:
            kol.tier = "nano"
        elif max_followers < 100000:
            kol.tier = "micro"
        elif max_followers < 500000:
            kol.tier = "mid"
        elif max_followers < 1000000:
            kol.tier = "macro"
        else:
            kol.tier = "mega"
        
        self.db.add(kol)
        self.db.commit()
    
    def add_tag(self, kol_id: int, tag: str) -> KOL:
        """
        Add tag to KOL.
        
        Args:
            kol_id: KOL ID
            tag: Tag to add
            
        Returns:
            Updated KOL object
            
        Raises:
            HTTPException: If KOL not found
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        if tag not in kol.tags:
            kol.tags.append(tag)
            kol.updated_at = datetime.utcnow()
            self.db.add(kol)
            self.db.commit()
            self.db.refresh(kol)
        
        return kol
    
    def remove_tag(self, kol_id: int, tag: str) -> KOL:
        """
        Remove tag from KOL.
        
        Args:
            kol_id: KOL ID
            tag: Tag to remove
            
        Returns:
            Updated KOL object
            
        Raises:
            HTTPException: If KOL not found
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        if tag in kol.tags:
            kol.tags.remove(tag)
            kol.updated_at = datetime.utcnow()
            self.db.add(kol)
            self.db.commit()
            self.db.refresh(kol)
        
        return kol
