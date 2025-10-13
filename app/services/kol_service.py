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
        # Validate KOL data
        kol_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'location': location,
            'niche': niche,
            'tags': tags,
            'notes': notes,
            'social_handles': social_handles
        }
        kol_data = self.validate_kol_data(kol_data)
        
        # Create KOL
        kol = KOL(
            name=kol_data['name'],
            email=kol_data.get('email'),
            phone=kol_data.get('phone'),
            location=kol_data.get('location'),
            niche=kol_data.get('niche', []),
            tags=kol_data.get('tags', []),
            notes=kol_data.get('notes')
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
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
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
            sort_by: Field to sort by (name, created_at, updated_at)
            sort_order: Sort order (asc, desc)
            
        Returns:
            Tuple of (KOLs list, total count)
        """
        from sqlmodel import distinct
        
        # Base query - use distinct to avoid duplicates when joining social handles
        statement = select(KOL).distinct()
        
        # Apply search including social handles
        if search:
            # Join with social handles for search
            statement = statement.join(SocialHandle, KOL.id == SocialHandle.kol_id, isouter=True)
            statement = statement.where(
                or_(
                    KOL.name.ilike(f"%{search}%"),
                    KOL.email.ilike(f"%{search}%"),
                    SocialHandle.handle.ilike(f"%{search}%")
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
        
        # Get total count with same filters
        count_statement = select(func.count(distinct(KOL.id)))
        if search:
            count_statement = count_statement.select_from(
                KOL.join(SocialHandle, KOL.id == SocialHandle.kol_id, isouter=True)
            )
            count_statement = count_statement.where(
                or_(
                    KOL.name.ilike(f"%{search}%"),
                    KOL.email.ilike(f"%{search}%"),
                    SocialHandle.handle.ilike(f"%{search}%")
                )
            )
        else:
            count_statement = count_statement.select_from(KOL)
            
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
        
        # Apply sorting
        sort_column = getattr(KOL, sort_by, KOL.created_at)
        if sort_order.lower() == "asc":
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())
        
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
            HTTPException: If KOL not found or has active campaigns
        """
        # Validate deletion is allowed
        self.validate_kol_deletion(kol_id)
        
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
    def update_social_handle(
        self,
        handle_id: int,
        platform: Optional[str] = None,
        handle: Optional[str] = None,
        url: Optional[str] = None,
        follower_count: Optional[int] = None,
        is_verified: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> SocialHandle:
        """
        Update social media handle.
        
        Args:
            handle_id: Social handle ID
            platform: New platform
            handle: New handle/username
            url: New profile URL
            follower_count: New follower count
            is_verified: New verification status
            is_active: New active status
            
        Returns:
            Updated social handle object
            
        Raises:
            HTTPException: If handle not found
        """
        social_handle = self.db.get(SocialHandle, handle_id)
        if not social_handle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social handle not found"
            )
        
        # Update fields
        if platform is not None:
            social_handle.platform = platform
        if handle is not None:
            social_handle.handle = handle
        if url is not None:
            social_handle.url = url
        if follower_count is not None:
            social_handle.follower_count = follower_count
        if is_verified is not None:
            social_handle.is_verified = is_verified
        if is_active is not None:
            social_handle.is_active = is_active
        
        social_handle.last_enriched_at = datetime.utcnow()
        
        self.db.add(social_handle)
        self.db.commit()
        self.db.refresh(social_handle)
        
        # Recalculate tier if follower count changed
        if follower_count is not None:
            self.calculate_tier(social_handle.kol_id)
        
        return social_handle
    
    def delete_social_handle(self, handle_id: int) -> None:
        """
        Delete social media handle.
        
        Args:
            handle_id: Social handle ID
            
        Raises:
            HTTPException: If handle not found or KOL would have no handles
        """
        social_handle = self.db.get(SocialHandle, handle_id)
        if not social_handle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social handle not found"
            )
        
        # Check if this is the last handle for the KOL
        remaining_handles = self.db.exec(
            select(func.count(SocialHandle.id)).where(
                SocialHandle.kol_id == social_handle.kol_id,
                SocialHandle.id != handle_id
            )
        ).one()
        
        if remaining_handles == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last social handle. KOL must have at least one social media handle."
            )
        
        self.db.delete(social_handle)
        self.db.commit()
        
        # Recalculate tier
        self.calculate_tier(social_handle.kol_id)
    
    def find_duplicates(self, kol_id: int) -> List[dict]:
        """
        Find potential duplicate KOLs based on email, social handles, and name similarity.
        
        Args:
            kol_id: KOL ID to check for duplicates
            
        Returns:
            List of potential duplicate KOLs with match reasons
            
        Raises:
            HTTPException: If KOL not found
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        duplicates = {}  # Use dict to track match reasons
        
        # Check for exact email match
        if kol.email:
            email_duplicates = self.db.exec(
                select(KOL).where(
                    KOL.email == kol.email,
                    KOL.id != kol_id,
                    KOL.status == "active"
                )
            ).all()
            
            for dup in email_duplicates:
                if dup.id not in duplicates:
                    duplicates[dup.id] = {
                        'kol': dup,
                        'match_reasons': [],
                        'confidence': 0
                    }
                duplicates[dup.id]['match_reasons'].append('Exact email match')
                duplicates[dup.id]['confidence'] += 90
        
        # Check for exact social handle match
        kol_handles = self.db.exec(
            select(SocialHandle).where(
                SocialHandle.kol_id == kol_id,
                SocialHandle.is_active == True
            )
        ).all()
        
        for handle in kol_handles:
            handle_duplicates = self.db.exec(
                select(KOL).join(SocialHandle).where(
                    SocialHandle.platform == handle.platform,
                    SocialHandle.handle == handle.handle,
                    SocialHandle.kol_id != kol_id,
                    SocialHandle.is_active == True,
                    KOL.status == "active"
                )
            ).all()
            
            for dup in handle_duplicates:
                if dup.id not in duplicates:
                    duplicates[dup.id] = {
                        'kol': dup,
                        'match_reasons': [],
                        'confidence': 0
                    }
                duplicates[dup.id]['match_reasons'].append(f'Same {handle.platform} handle: @{handle.handle}')
                duplicates[dup.id]['confidence'] += 95
        
        # Check for name similarity (basic)
        name_duplicates = self._find_similar_names(kol.name, kol_id)
        for dup in name_duplicates:
            if dup.id not in duplicates:
                duplicates[dup.id] = {
                    'kol': dup,
                    'match_reasons': [],
                    'confidence': 0
                }
            duplicates[dup.id]['match_reasons'].append('Similar name')
            duplicates[dup.id]['confidence'] += 60
        
        # Convert to list and sort by confidence
        result = []
        for dup_data in duplicates.values():
            # Cap confidence at 100
            dup_data['confidence'] = min(dup_data['confidence'], 100)
            result.append(dup_data)
        
        # Sort by confidence (highest first)
        result.sort(key=lambda x: x['confidence'], reverse=True)
        
        return result
    
    def _find_similar_names(self, name: str, exclude_id: int) -> List[KOL]:
        """
        Find KOLs with similar names using basic string matching.
        
        Args:
            name: Name to compare against
            exclude_id: KOL ID to exclude from results
            
        Returns:
            List of KOLs with similar names
        """
        # Simple similarity check - exact match after normalization
        normalized_name = name.lower().strip()
        
        # Remove common prefixes/suffixes
        normalized_name = normalized_name.replace('official', '').replace('real', '').strip()
        
        similar_kols = self.db.exec(
            select(KOL).where(
                KOL.id != exclude_id,
                KOL.status == "active"
            )
        ).all()
        
        matches = []
        for kol in similar_kols:
            kol_normalized = kol.name.lower().strip()
            kol_normalized = kol_normalized.replace('official', '').replace('real', '').strip()
            
            # Check for exact match after normalization
            if kol_normalized == normalized_name:
                matches.append(kol)
            # Check for very similar names (one is substring of another)
            elif (len(normalized_name) > 3 and normalized_name in kol_normalized) or \
                 (len(kol_normalized) > 3 and kol_normalized in normalized_name):
                matches.append(kol)
        
        return matches
    
    def scan_all_duplicates(self) -> dict:
        """
        Scan all active KOLs for potential duplicates.
        
        Returns:
            Dictionary with duplicate statistics and top duplicates
        """
        all_kols = self.db.exec(
            select(KOL).where(KOL.status == "active")
        ).all()
        
        duplicate_pairs = []
        processed_ids = set()
        
        for kol in all_kols:
            if kol.id in processed_ids:
                continue
                
            duplicates = self.find_duplicates(kol.id)
            if duplicates:
                for dup_data in duplicates:
                    if dup_data['confidence'] >= 80:  # High confidence duplicates only
                        duplicate_pairs.append({
                            'primary_kol': {
                                'id': kol.id,
                                'name': kol.name,
                                'email': kol.email
                            },
                            'duplicate_kol': {
                                'id': dup_data['kol'].id,
                                'name': dup_data['kol'].name,
                                'email': dup_data['kol'].email
                            },
                            'confidence': dup_data['confidence'],
                            'match_reasons': dup_data['match_reasons']
                        })
                        processed_ids.add(dup_data['kol'].id)
            
            processed_ids.add(kol.id)
        
        return {
            'total_kols_scanned': len(all_kols),
            'duplicate_pairs_found': len(duplicate_pairs),
            'duplicate_pairs': duplicate_pairs[:20]  # Top 20 for performance
        }
    
    def merge_kols(self, primary_kol_id: int, duplicate_kol_id: int, merge_data: dict = None) -> KOL:
        """
        Merge duplicate KOL into primary KOL.
        
        Args:
            primary_kol_id: ID of KOL to keep
            duplicate_kol_id: ID of KOL to merge and deactivate
            merge_data: Optional data to update primary KOL with
            
        Returns:
            Updated primary KOL
            
        Raises:
            HTTPException: If KOLs not found or merge not allowed
        """
        primary_kol = self.get_kol(primary_kol_id)
        duplicate_kol = self.get_kol(duplicate_kol_id)
        
        if not primary_kol or not duplicate_kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both KOLs not found"
            )
        
        if primary_kol_id == duplicate_kol_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot merge KOL with itself"
            )
        
        # Merge social handles (avoid duplicates)
        duplicate_handles = self.db.exec(
            select(SocialHandle).where(
                SocialHandle.kol_id == duplicate_kol_id,
                SocialHandle.is_active == True
            )
        ).all()
        
        primary_handles = self.db.exec(
            select(SocialHandle).where(
                SocialHandle.kol_id == primary_kol_id,
                SocialHandle.is_active == True
            )
        ).all()
        
        primary_platforms = {h.platform for h in primary_handles}
        
        for handle in duplicate_handles:
            if handle.platform not in primary_platforms:
                # Transfer handle to primary KOL
                handle.kol_id = primary_kol_id
                self.db.add(handle)
            else:
                # Deactivate duplicate handle
                handle.is_active = False
                self.db.add(handle)
        
        # Merge missing data from duplicate to primary
        if not primary_kol.email and duplicate_kol.email:
            primary_kol.email = duplicate_kol.email
        
        if not primary_kol.phone and duplicate_kol.phone:
            primary_kol.phone = duplicate_kol.phone
        
        if not primary_kol.location and duplicate_kol.location:
            primary_kol.location = duplicate_kol.location
        
        # Merge niches and tags
        if duplicate_kol.niche:
            primary_kol.niche = list(set(primary_kol.niche + duplicate_kol.niche))
        
        if duplicate_kol.tags:
            primary_kol.tags = list(set(primary_kol.tags + duplicate_kol.tags))
        
        # Apply any additional merge data
        if merge_data:
            for key, value in merge_data.items():
                if hasattr(primary_kol, key) and value is not None:
                    setattr(primary_kol, key, value)
        
        primary_kol.updated_at = datetime.utcnow()
        
        # Deactivate duplicate KOL
        duplicate_kol.status = "merged"
        duplicate_kol.notes = f"Merged into KOL #{primary_kol_id} on {datetime.utcnow().strftime('%Y-%m-%d')}"
        duplicate_kol.updated_at = datetime.utcnow()
        
        self.db.add(primary_kol)
        self.db.add(duplicate_kol)
        self.db.commit()
        
        # Recalculate tier for primary KOL
        self.calculate_tier(primary_kol_id)
        
        self.db.refresh(primary_kol)
        return primary_kol

    def validate_kol_deletion(self, kol_id: int) -> bool:
        """
        Validate if KOL can be deleted (no active campaigns).
        
        Args:
            kol_id: KOL ID to validate
            
        Returns:
            True if KOL can be deleted
            
        Raises:
            HTTPException: If KOL has active campaigns
        """
        kol = self.get_kol(kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KOL not found"
            )
        
        if kol.status == "inactive":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KOL is already inactive"
            )
        
        # Check for active campaigns (when campaign system is implemented)
        try:
            from app.models.campaign_kol import CampaignKOL
            active_campaigns = self.db.exec(
                select(func.count(CampaignKOL.id)).where(
                    CampaignKOL.kol_id == kol_id,
                    CampaignKOL.status.in_(["shortlisted", "assigned", "accepted"])
                )
            ).one()
            
            if active_campaigns > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete KOL with {active_campaigns} active campaigns. Please remove from campaigns first."
                )
        except ImportError:
            # Campaign system not yet implemented, skip check
            pass
        
        return True
    
    def validate_kol_data(self, kol_data: dict) -> dict:
        """
        Validate KOL data before creation or update.
        
        Args:
            kol_data: KOL data dictionary
            
        Returns:
            Validated and cleaned KOL data
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate required fields
        if not kol_data.get('name') or not kol_data['name'].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KOL name is required"
            )
        
        # Clean and validate name
        kol_data['name'] = kol_data['name'].strip()
        if len(kol_data['name']) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KOL name too long (max 255 characters)"
            )
        
        # Validate email uniqueness if provided
        if kol_data.get('email'):
            existing_kol = self.db.exec(
                select(KOL).where(
                    KOL.email == kol_data['email'],
                    KOL.status == "active"
                )
            ).first()
            
            # Allow update of same KOL
            if existing_kol and existing_kol.id != kol_data.get('id'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already exists for another active KOL"
                )
        
        # Validate social handles if provided
        if kol_data.get('social_handles'):
            self._validate_social_handles(kol_data['social_handles'])
        
        # Clean arrays
        if kol_data.get('niche'):
            kol_data['niche'] = [n.strip() for n in kol_data['niche'] if n.strip()]
        if kol_data.get('tags'):
            kol_data['tags'] = [t.strip() for t in kol_data['tags'] if t.strip()]
        
        return kol_data
    
    def _validate_social_handles(self, social_handles: List[dict]) -> None:
        """
        Validate social media handles.
        
        Args:
            social_handles: List of social handle dictionaries
            
        Raises:
            HTTPException: If validation fails
        """
        if not social_handles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one social media handle is required"
            )
        
        platforms_seen = set()
        for handle_data in social_handles:
            platform = handle_data.get('platform')
            handle = handle_data.get('handle')
            
            if not platform or not handle:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Platform and handle are required for all social media handles"
                )
            
            # Check for duplicate platforms
            if platform in platforms_seen:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate platform '{platform}' in social handles"
                )
            platforms_seen.add(platform)
            
            # Check for existing handle on same platform
            existing_handle = self.db.exec(
                select(SocialHandle).where(
                    SocialHandle.platform == platform,
                    SocialHandle.handle == handle.lstrip('@'),
                    SocialHandle.is_active == True
                )
            ).first()
            
            if existing_handle:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Handle '@{handle}' already exists on {platform}"
                )