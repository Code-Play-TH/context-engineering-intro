"""Post model for tracking KOL social media posts."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class PostType(str, Enum):
    """Types of social media posts."""
    POST = "post"
    STORY = "story"
    VIDEO = "video"
    REEL = "reel"
    TWEET = "tweet"
    YOUTUBE_VIDEO = "youtube_video"
    TIKTOK_VIDEO = "tiktok_video"


class SocialPlatform(str, Enum):
    """Social media platforms."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


class Post(SQLModel, table=True):
    """Model for tracking KOL social media posts."""
    __tablename__ = "posts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kols.id", index=True)
    campaign_id: Optional[int] = Field(foreign_key="campaigns.id", index=True, default=None)
    platform: SocialPlatform
    post_id: str = Field(index=True)  # Platform-specific post ID
    post_url: str
    post_type: PostType
    caption: Optional[str] = Field(default=None)
    hashtags: List[str] = Field(default_factory=list, sa_column_kwargs={"type_": "JSON"})
    mentions: List[str] = Field(default_factory=list, sa_column_kwargs={"type_": "JSON"})
    posted_at: datetime = Field(index=True)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    is_campaign_content: bool = Field(default=False, index=True)
    campaign_keywords_matched: List[str] = Field(default_factory=list, sa_column_kwargs={"type_": "JSON"})
    
    # Initial metrics (captured at detection)
    initial_likes: int = Field(default=0)
    initial_comments: int = Field(default=0)
    initial_shares: int = Field(default=0)
    initial_views: Optional[int] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    kol: Optional["KOL"] = Relationship(back_populates="posts")
    campaign: Optional["Campaign"] = Relationship(back_populates="posts")
    metrics: List["PostMetrics"] = Relationship(back_populates="post")
    
    def calculate_initial_engagement_rate(self, follower_count: int) -> float:
        """Calculate initial engagement rate based on likes and comments."""
        if follower_count == 0:
            return 0.0
        
        total_engagement = self.initial_likes + self.initial_comments
        return (total_engagement / follower_count) * 100
    
    def extract_hashtags_from_caption(self) -> List[str]:
        """Extract hashtags from caption."""
        if not self.caption:
            return []
        
        import re
        hashtags = re.findall(r'#(\w+)', self.caption)
        return [tag.lower() for tag in hashtags]
    
    def extract_mentions_from_caption(self) -> List[str]:
        """Extract mentions from caption."""
        if not self.caption:
            return []
        
        import re
        mentions = re.findall(r'@(\w+)', self.caption)
        return [mention.lower() for mention in mentions]
    
    def check_campaign_match(self, campaign_keywords: List[str], campaign_hashtags: List[str]) -> bool:
        """Check if post matches campaign keywords or hashtags."""
        if not campaign_keywords and not campaign_hashtags:
            return False
        
        # Check hashtags
        post_hashtags = [tag.lower() for tag in self.hashtags]
        campaign_hashtags_lower = [tag.lower() for tag in campaign_hashtags]
        
        hashtag_match = any(tag in post_hashtags for tag in campaign_hashtags_lower)
        
        # Check keywords in caption
        keyword_match = False
        if self.caption and campaign_keywords:
            caption_lower = self.caption.lower()
            keyword_match = any(keyword.lower() in caption_lower for keyword in campaign_keywords)
        
        if hashtag_match or keyword_match:
            self.is_campaign_content = True
            self.campaign_keywords_matched = [
                keyword for keyword in campaign_keywords 
                if keyword.lower() in (self.caption or "").lower()
            ]
            return True
        
        return False