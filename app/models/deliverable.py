"""Deliverable model."""
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class DeliverableType(str, Enum):
    """Deliverable type enumeration."""
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"
    TIKTOK_VIDEO = "tiktok_video"
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_SHORT = "youtube_short"
    TWITTER_POST = "twitter_post"
    FACEBOOK_POST = "facebook_post"
    BLOG_POST = "blog_post"
    LIVE_STREAM = "live_stream"
    PRODUCT_REVIEW = "product_review"
    UNBOXING_VIDEO = "unboxing_video"
    TUTORIAL = "tutorial"
    BRAND_MENTION = "brand_mention"


class DeliverableStatus(str, Enum):
    """Deliverable status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Deliverable(SQLModel, table=True):
    """Deliverable model for campaign requirements."""
    
    __tablename__ = "deliverables"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.id", index=True)
    deliverable_type: DeliverableType = Field(index=True)
    quantity: int = Field(default=1, ge=1)
    deadline: Optional[date] = Field(default=None, index=True)
    status: DeliverableStatus = Field(default=DeliverableStatus.PENDING, index=True)
    
    # Content specifications
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    platform_specific_requirements: Optional[str] = Field(default=None)
    hashtags: Optional[str] = Field(default=None)
    mentions: Optional[str] = Field(default=None)
    
    # Progress tracking
    submitted_count: int = Field(default=0)
    approved_count: int = Field(default=0)
    published_count: int = Field(default=0)
    
    # Timeline tracking
    submitted_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Review process
    reviewer_notes: Optional[str] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)
    
    # Metadata
    priority: str = Field(default="medium", max_length=20)  # low, medium, high, critical
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    campaign: "Campaign" = Relationship(back_populates="deliverables")
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.quantity == 0:
            return 0.0
        return (self.completed_count / self.quantity) * 100
    
    @property
    def is_overdue(self) -> bool:
        """Check if deliverable is overdue."""
        if not self.deadline:
            return False
        return date.today() > self.deadline and self.status not in [
            DeliverableStatus.COMPLETED, 
            DeliverableStatus.CANCELLED
        ]
    
    def update_progress(self) -> None:
        """Update progress based on current counts."""
        if self.approved_count >= self.quantity:
            self.status = DeliverableStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        elif self.submitted_count > 0:
            self.status = DeliverableStatus.SUBMITTED
        elif self.status == DeliverableStatus.PENDING:
            self.status = DeliverableStatus.IN_PROGRESS
        
        self.updated_at = datetime.utcnow()