"""Scraping schedule model for managing KOL social media scraping intervals."""
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class ScrapingInterval(str, Enum):
    """Scraping interval options."""
    HOURLY = "hourly"
    EVERY_6_HOURS = "every_6_hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ScrapingSchedule(SQLModel, table=True):
    """Model for managing KOL scraping schedules."""
    __tablename__ = "scraping_schedules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kols.id", index=True)
    interval: ScrapingInterval = Field(default=ScrapingInterval.DAILY)
    custom_cron: Optional[str] = Field(default=None)  # For custom intervals
    priority: int = Field(default=5, ge=1, le=10)  # 1-10, higher = more important
    is_active: bool = Field(default=True, index=True)
    last_scraped_at: Optional[datetime] = Field(default=None)
    next_scrape_at: datetime = Field(index=True)
    consecutive_failures: int = Field(default=0)
    max_failures: int = Field(default=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    kol: Optional["KOL"] = Relationship(back_populates="scraping_schedule")
    
    def calculate_next_scrape_time(self) -> datetime:
        """Calculate next scrape time based on interval."""
        now = datetime.utcnow()
        
        if self.interval == ScrapingInterval.HOURLY:
            return now + timedelta(hours=1)
        elif self.interval == ScrapingInterval.EVERY_6_HOURS:
            return now + timedelta(hours=6)
        elif self.interval == ScrapingInterval.DAILY:
            return now + timedelta(days=1)
        elif self.interval == ScrapingInterval.WEEKLY:
            return now + timedelta(weeks=1)
        elif self.interval == ScrapingInterval.CUSTOM and self.custom_cron:
            # For now, default to daily if custom cron is not implemented
            return now + timedelta(days=1)
        else:
            return now + timedelta(days=1)
    
    def should_scrape_now(self) -> bool:
        """Check if this KOL should be scraped now."""
        if not self.is_active:
            return False
        
        if self.consecutive_failures >= self.max_failures:
            return False
            
        return datetime.utcnow() >= self.next_scrape_at
    
    def record_success(self) -> None:
        """Record successful scraping."""
        self.last_scraped_at = datetime.utcnow()
        self.next_scrape_at = self.calculate_next_scrape_time()
        self.consecutive_failures = 0
        self.updated_at = datetime.utcnow()
    
    def record_failure(self) -> None:
        """Record failed scraping attempt."""
        self.consecutive_failures += 1
        self.updated_at = datetime.utcnow()
        
        # If too many failures, increase next scrape time
        if self.consecutive_failures >= 3:
            delay_hours = min(self.consecutive_failures * 2, 24)  # Max 24 hour delay
            self.next_scrape_at = datetime.utcnow() + timedelta(hours=delay_hours)
        else:
            self.next_scrape_at = self.calculate_next_scrape_time()