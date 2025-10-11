"""Smart distribution algorithm for large-scale KOL scraping operations."""
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, or_, func
from dataclasses import dataclass
from enum import Enum
import logging

from app.models.scraping_schedule import ScrapingSchedule, ScrapingInterval
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.brief import Brief
from app.models.kol_metrics import KOLMetrics

logger = logging.getLogger(__name__)


class DistributionStrategy(str, Enum):
    """Distribution strategies for KOL scraping."""
    EVEN = "even"  # Distribute evenly across 24 hours
    PRIORITY_FIRST = "priority_first"  # High priority KOLs first
    CAMPAIGN_AWARE = "campaign_aware"  # Active campaign KOLs prioritized
    LOAD_BALANCED = "load_balanced"  # Balance across worker capacity


@dataclass
class DistributionSlot:
    """Represents a time slot for scraping distribution."""
    start_time: datetime
    end_time: datetime
    capacity: int
    assigned_kols: List[int]
    priority_weight: float
    
    @property
    def available_capacity(self) -> int:
        return max(0, self.capacity - len(self.assigned_kols))
    
    @property
    def utilization(self) -> float:
        if self.capacity == 0:
            return 0.0
        return len(self.assigned_kols) / self.capacity


@dataclass
class KOLPriority:
    """KOL with calculated priority score."""
    kol_id: int
    priority_score: float
    campaign_active: bool
    last_scraped: Optional[datetime]
    scraping_frequency: ScrapingInterval
    consecutive_failures: int


class SmartDistributionAlgorithm:
    """Smart distribution algorithm for scheduling KOL scraping at scale."""
    
    def __init__(self, db: Session):
        self.db = db
        # Configuration
        self.slots_per_day = 24  # Hourly slots
        self.max_kols_per_slot = 5000  # Max KOLs per hour
        self.worker_capacity = 50  # KOLs per worker per minute
        self.max_workers = 20  # Maximum concurrent workers
        self.priority_boost_active_campaign = 3.0
        self.priority_boost_overdue = 2.0
        self.priority_penalty_failures = 0.5
    
    def distribute_kols(
        self,
        strategy: DistributionStrategy = DistributionStrategy.CAMPAIGN_AWARE,
        target_date: Optional[datetime] = None,
        max_kols: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Distribute KOLs across time slots for optimal scraping.
        
        Args:
            strategy: Distribution strategy to use
            target_date: Date to distribute for (defaults to tomorrow)
            max_kols: Maximum number of KOLs to distribute
            
        Returns:
            Distribution plan with time slots and assigned KOLs
        """
        if target_date is None:
            target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        try:
            # Get KOLs that need scraping
            kols_to_scrape = self._get_kols_for_distribution(target_date, max_kols)
            
            if not kols_to_scrape:
                return {
                    "success": True,
                    "total_kols": 0,
                    "slots": [],
                    "message": "No KOLs need scraping"
                }
            
            # Calculate priority scores
            prioritized_kols = self._calculate_priorities(kols_to_scrape)
            
            # Create time slots
            time_slots = self._create_time_slots(target_date, len(prioritized_kols))
            
            # Distribute KOLs based on strategy
            if strategy == DistributionStrategy.EVEN:
                distribution = self._distribute_evenly(prioritized_kols, time_slots)
            elif strategy == DistributionStrategy.PRIORITY_FIRST:
                distribution = self._distribute_priority_first(prioritized_kols, time_slots)
            elif strategy == DistributionStrategy.CAMPAIGN_AWARE:
                distribution = self._distribute_campaign_aware(prioritized_kols, time_slots)
            elif strategy == DistributionStrategy.LOAD_BALANCED:
                distribution = self._distribute_load_balanced(prioritized_kols, time_slots)
            else:
                raise ValueError(f"Unknown distribution strategy: {strategy}")
            
            # Update schedules in database
            updated_schedules = self._update_schedules(distribution, target_date)
            
            # Generate statistics
            stats = self._generate_statistics(distribution, prioritized_kols)
            
            return {
                "success": True,
                "strategy": strategy,
                "target_date": target_date.isoformat(),
                "total_kols": len(prioritized_kols),
                "updated_schedules": updated_schedules,
                "slots": [
                    {
                        "start_time": slot.start_time.isoformat(),
                        "end_time": slot.end_time.isoformat(),
                        "assigned_kols": len(slot.assigned_kols),
                        "capacity": slot.capacity,
                        "utilization": slot.utilization,
                        "kol_ids": slot.assigned_kols
                    }
                    for slot in distribution
                ],
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Error in smart distribution: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy,
                "target_date": target_date.isoformat() if target_date else None
            }
    
    def _get_kols_for_distribution(
        self, 
        target_date: datetime, 
        max_kols: Optional[int]
    ) -> List[ScrapingSchedule]:
        """Get KOL schedules that need distribution."""
        # Get active schedules that are due or overdue
        cutoff_time = target_date + timedelta(hours=24)  # End of target day
        
        statement = select(ScrapingSchedule).where(
            and_(
                ScrapingSchedule.is_active == True,
                ScrapingSchedule.next_scrape_at <= cutoff_time,
                ScrapingSchedule.consecutive_failures < ScrapingSchedule.max_failures
            )
        ).order_by(ScrapingSchedule.next_scrape_at.asc())
        
        if max_kols:
            statement = statement.limit(max_kols)
        
        return list(self.db.exec(statement).all())
    
    def _calculate_priorities(self, schedules: List[ScrapingSchedule]) -> List[KOLPriority]:
        """Calculate priority scores for KOLs."""
        prioritized_kols = []
        
        # Get active campaigns for priority boost
        active_campaigns = self._get_active_campaigns()
        active_campaign_kols = set()
        
        for campaign in active_campaigns:
            briefs = self.db.exec(
                select(Brief).where(Brief.campaign_id == campaign.id)
            ).all()
            active_campaign_kols.update(brief.kol_id for brief in briefs)
        
        for schedule in schedules:
            # Base priority from schedule
            priority_score = float(schedule.priority)
            
            # Boost for active campaigns
            campaign_active = schedule.kol_id in active_campaign_kols
            if campaign_active:
                priority_score += self.priority_boost_active_campaign
            
            # Boost for overdue scraping
            if schedule.next_scrape_at < datetime.utcnow():
                hours_overdue = (datetime.utcnow() - schedule.next_scrape_at).total_seconds() / 3600
                priority_score += min(hours_overdue / 24, 1.0) * self.priority_boost_overdue
            
            # Penalty for consecutive failures
            if schedule.consecutive_failures > 0:
                priority_score -= schedule.consecutive_failures * self.priority_penalty_failures
            
            # Get last scraped time
            last_metrics = self.db.exec(
                select(KOLMetrics).where(
                    KOLMetrics.kol_id == schedule.kol_id
                ).order_by(KOLMetrics.scraped_at.desc()).limit(1)
            ).first()
            
            last_scraped = last_metrics.scraped_at if last_metrics else None
            
            prioritized_kols.append(KOLPriority(
                kol_id=schedule.kol_id,
                priority_score=max(0.1, priority_score),  # Minimum priority
                campaign_active=campaign_active,
                last_scraped=last_scraped,
                scraping_frequency=schedule.interval,
                consecutive_failures=schedule.consecutive_failures
            ))
        
        # Sort by priority score (highest first)
        return sorted(prioritized_kols, key=lambda x: x.priority_score, reverse=True)
    
    def _get_active_campaigns(self) -> List[Campaign]:
        """Get currently active campaigns."""
        today = datetime.utcnow().date()
        return list(self.db.exec(
            select(Campaign).where(
                and_(
                    Campaign.status.in_(["active", "running"]),
                    Campaign.start_date <= today,
                    or_(
                        Campaign.end_date.is_(None),
                        Campaign.end_date >= today
                    )
                )
            )
        ).all())
    
    def _create_time_slots(self, target_date: datetime, total_kols: int) -> List[DistributionSlot]:
        """Create time slots for the target date."""
        slots = []
        
        # Calculate optimal capacity per slot
        base_capacity = min(
            self.max_kols_per_slot,
            math.ceil(total_kols / self.slots_per_day)
        )
        
        for hour in range(24):
            start_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            # Adjust capacity based on time of day
            # Higher capacity during business hours (9 AM - 6 PM UTC)
            if 9 <= hour <= 18:
                capacity = int(base_capacity * 1.2)  # 20% boost
            elif 22 <= hour or hour <= 6:
                capacity = int(base_capacity * 0.8)  # 20% reduction for night hours
            else:
                capacity = base_capacity
            
            # Priority weight based on time (higher during off-peak hours)
            if 2 <= hour <= 6:
                priority_weight = 1.3  # Night hours - less API traffic
            elif 9 <= hour <= 17:
                priority_weight = 0.8  # Business hours - more API traffic
            else:
                priority_weight = 1.0
            
            slots.append(DistributionSlot(
                start_time=start_time,
                end_time=end_time,
                capacity=capacity,
                assigned_kols=[],
                priority_weight=priority_weight
            ))
        
        return slots
    
    def _distribute_evenly(
        self, 
        kols: List[KOLPriority], 
        slots: List[DistributionSlot]
    ) -> List[DistributionSlot]:
        """Distribute KOLs evenly across all time slots."""
        kols_per_slot = len(kols) // len(slots)
        remainder = len(kols) % len(slots)
        
        kol_index = 0
        for i, slot in enumerate(slots):
            # Add extra KOL to first 'remainder' slots
            slot_size = kols_per_slot + (1 if i < remainder else 0)
            
            for _ in range(min(slot_size, slot.capacity)):
                if kol_index < len(kols):
                    slot.assigned_kols.append(kols[kol_index].kol_id)
                    kol_index += 1
        
        return slots
    
    def _distribute_priority_first(
        self, 
        kols: List[KOLPriority], 
        slots: List[DistributionSlot]
    ) -> List[DistributionSlot]:
        """Distribute highest priority KOLs first."""
        kol_index = 0
        
        # Fill slots in order, prioritizing earlier time slots
        for slot in slots:
            while slot.available_capacity > 0 and kol_index < len(kols):
                slot.assigned_kols.append(kols[kol_index].kol_id)
                kol_index += 1
        
        return slots
    
    def _distribute_campaign_aware(
        self, 
        kols: List[KOLPriority], 
        slots: List[DistributionSlot]
    ) -> List[DistributionSlot]:
        """Distribute with campaign awareness - active campaign KOLs get priority slots."""
        # Separate campaign and non-campaign KOLs
        campaign_kols = [k for k in kols if k.campaign_active]
        regular_kols = [k for k in kols if not k.campaign_active]
        
        # Sort slots by priority weight (best slots first)
        sorted_slots = sorted(slots, key=lambda x: x.priority_weight, reverse=True)
        
        # Assign campaign KOLs to best slots first
        kol_index = 0
        for slot in sorted_slots:
            while slot.available_capacity > 0 and kol_index < len(campaign_kols):
                slot.assigned_kols.append(campaign_kols[kol_index].kol_id)
                kol_index += 1
        
        # Fill remaining capacity with regular KOLs
        kol_index = 0
        for slot in sorted_slots:
            while slot.available_capacity > 0 and kol_index < len(regular_kols):
                slot.assigned_kols.append(regular_kols[kol_index].kol_id)
                kol_index += 1
        
        return slots
    
    def _distribute_load_balanced(
        self, 
        kols: List[KOLPriority], 
        slots: List[DistributionSlot]
    ) -> List[DistributionSlot]:
        """Distribute with load balancing across worker capacity."""
        # Calculate worker load for each slot
        for slot in slots:
            # Estimate processing time based on KOL complexity
            estimated_minutes = len(slot.assigned_kols) / self.worker_capacity
            workers_needed = math.ceil(estimated_minutes / 60)  # Workers needed for 1 hour
            slot.capacity = min(slot.capacity, workers_needed * self.worker_capacity)
        
        # Use round-robin assignment to balance load
        slot_index = 0
        for kol in kols:
            # Find slot with available capacity
            attempts = 0
            while attempts < len(slots):
                current_slot = slots[slot_index % len(slots)]
                if current_slot.available_capacity > 0:
                    current_slot.assigned_kols.append(kol.kol_id)
                    break
                slot_index += 1
                attempts += 1
            
            slot_index += 1
        
        return slots
    
    def _update_schedules(
        self, 
        distribution: List[DistributionSlot], 
        target_date: datetime
    ) -> int:
        """Update scraping schedules with new distribution times."""
        updated_count = 0
        
        for slot in distribution:
            for kol_id in slot.assigned_kols:
                schedule = self.db.exec(
                    select(ScrapingSchedule).where(ScrapingSchedule.kol_id == kol_id)
                ).first()
                
                if schedule:
                    # Set next scrape time to random time within the slot
                    import random
                    slot_duration = (slot.end_time - slot.start_time).total_seconds()
                    random_offset = random.uniform(0, slot_duration)
                    
                    schedule.next_scrape_at = slot.start_time + timedelta(seconds=random_offset)
                    schedule.updated_at = datetime.utcnow()
                    
                    self.db.add(schedule)
                    updated_count += 1
        
        self.db.commit()
        return updated_count
    
    def _generate_statistics(
        self, 
        distribution: List[DistributionSlot], 
        kols: List[KOLPriority]
    ) -> Dict[str, Any]:
        """Generate distribution statistics."""
        total_assigned = sum(len(slot.assigned_kols) for slot in distribution)
        campaign_kols = sum(1 for k in kols if k.campaign_active)
        
        slot_utilizations = [slot.utilization for slot in distribution]
        avg_utilization = sum(slot_utilizations) / len(slot_utilizations) if slot_utilizations else 0
        
        return {
            "total_kols": len(kols),
            "total_assigned": total_assigned,
            "unassigned": len(kols) - total_assigned,
            "campaign_kols": campaign_kols,
            "regular_kols": len(kols) - campaign_kols,
            "average_slot_utilization": avg_utilization,
            "peak_utilization": max(slot_utilizations) if slot_utilizations else 0,
            "min_utilization": min(slot_utilizations) if slot_utilizations else 0,
            "slots_used": sum(1 for slot in distribution if slot.assigned_kols),
            "total_slots": len(distribution)
        }
    
    def get_distribution_preview(
        self,
        strategy: DistributionStrategy = DistributionStrategy.CAMPAIGN_AWARE,
        target_date: Optional[datetime] = None,
        max_kols: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get a preview of distribution without updating schedules."""
        if target_date is None:
            target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        try:
            # Get KOLs that need scraping
            kols_to_scrape = self._get_kols_for_distribution(target_date, max_kols)
            
            if not kols_to_scrape:
                return {
                    "success": True,
                    "total_kols": 0,
                    "preview": "No KOLs need scraping"
                }
            
            # Calculate priority scores
            prioritized_kols = self._calculate_priorities(kols_to_scrape)
            
            # Create time slots
            time_slots = self._create_time_slots(target_date, len(prioritized_kols))
            
            # Generate preview statistics
            campaign_kols = sum(1 for k in prioritized_kols if k.campaign_active)
            overdue_kols = sum(1 for k in prioritized_kols if k.last_scraped and 
                             k.last_scraped < datetime.utcnow() - timedelta(days=1))
            
            return {
                "success": True,
                "strategy": strategy,
                "target_date": target_date.isoformat(),
                "total_kols": len(prioritized_kols),
                "campaign_kols": campaign_kols,
                "regular_kols": len(prioritized_kols) - campaign_kols,
                "overdue_kols": overdue_kols,
                "total_capacity": sum(slot.capacity for slot in time_slots),
                "estimated_duration_hours": 24,
                "slots_available": len(time_slots),
                "avg_kols_per_slot": len(prioritized_kols) // len(time_slots) if time_slots else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating distribution preview: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy,
                "target_date": target_date.isoformat() if target_date else None
            }