"""Content monitoring service for post detection and campaign content matching."""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlmodel import Session, select, and_, or_
from fastapi import HTTPException, status
import logging
from dataclasses import dataclass
from enum import Enum

from app.models.kol import KOL
from app.models.post import Post
from app.models.post_metrics import PostMetrics
from app.models.campaign import Campaign
from app.models.brief import Brief
from app.models.social_handle import SocialHandle
from app.services.scraping_service import ScrapingService
from app.services.rate_limit_manager import RateLimitManager, RateLimitExceeded

logger = logging.getLogger(__name__)


class ContentMatchType(str, Enum):
    """Types of content matching."""
    HASHTAG = "hashtag"
    KEYWORD = "keyword"
    MENTION = "mention"
    URL = "url"
    MANUAL = "manual"


@dataclass
class ContentMatch:
    """Represents a content match result."""
    match_type: ContentMatchType
    matched_text: str
    confidence: float
    context: str
    campaign_id: Optional[int] = None
    brief_id: Optional[int] = None


@dataclass
class PostAnalysis:
    """Analysis result for a post."""
    post_id: int
    matches: List[ContentMatch]
    campaign_matches: List[int]  # Campaign IDs
    brief_matches: List[int]     # Brief IDs
    engagement_score: float
    content_quality_score: float
    brand_safety_score: float


class ContentMonitoringService:
    """Service for monitoring KOL content and detecting campaign-related posts."""
    
    def __init__(self, db: Session, platform_configs: Dict[str, Dict[str, Any]]):
        self.db = db
        self.scraping_service = ScrapingService(db, platform_configs)
        self.rate_limit_manager = RateLimitManager(db)
        
        # Content matching configuration
        self.hashtag_pattern = re.compile(r'#(\w+)', re.IGNORECASE)
        self.mention_pattern = re.compile(r'@(\w+)', re.IGNORECASE)
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
        # Minimum confidence thresholds
        self.min_hashtag_confidence = 0.8
        self.min_keyword_confidence = 0.6
        self.min_mention_confidence = 0.9
    
    async def detect_new_posts(
        self, 
        kol_id: int, 
        platforms: Optional[List[str]] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Detect new posts for a KOL and analyze them for campaign content."""
        # Validate KOL exists
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"KOL not found: {kol_id}"
            )
        
        # Get KOL's social handles
        social_handles = kol.social_handles
        if not social_handles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KOL has no social media handles configured"
            )
        
        # Filter platforms if specified
        available_platforms = [h.platform for h in social_handles]
        if platforms:
            platforms = [p for p in platforms if p in available_platforms]
            if not platforms:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="None of the specified platforms are available for this KOL"
                )
        else:
            platforms = available_platforms
        
        try:
            # Get cutoff time for new posts
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Scrape recent posts
            scraping_result = await self.scraping_service.scrape_kol_posts(
                kol_id=kol_id,
                platforms=platforms,
                limit=50,  # Get more posts to ensure we catch new ones
                since_date=cutoff_time
            )
            
            if not scraping_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to scrape posts",
                    "details": scraping_result
                }
            
            # Get existing posts to identify new ones
            existing_posts = self.db.exec(
                select(Post).where(
                    and_(
                        Post.kol_id == kol_id,
                        Post.posted_at >= cutoff_time
                    )
                )
            ).all()
            
            existing_post_ids = {p.platform_post_id for p in existing_posts}
            
            # Identify new posts
            new_posts = []
            all_scraped_posts = []
            
            for platform, platform_result in scraping_result.get("results", {}).items():
                if platform_result.get("success") and platform_result.get("posts"):
                    for post_data in platform_result["posts"]:
                        all_scraped_posts.append(post_data)
                        if post_data["platform_post_id"] not in existing_post_ids:
                            new_posts.append(post_data)
            
            # Analyze new posts for campaign content
            analyzed_posts = []
            campaign_matches = []
            
            for post_data in new_posts:
                # Create post record
                post = await self._create_post_record(kol_id, post_data)
                
                # Analyze content
                analysis = await self._analyze_post_content(post)
                analyzed_posts.append(analysis)
                
                # Link to campaigns if matches found
                if analysis.campaign_matches:
                    for campaign_id in analysis.campaign_matches:
                        await self._link_post_to_campaign(post.id, campaign_id)
                        campaign_matches.append({
                            "post_id": post.id,
                            "campaign_id": campaign_id,
                            "confidence": max(m.confidence for m in analysis.matches)
                        })
            
            return {
                "success": True,
                "kol_id": kol_id,
                "platforms": platforms,
                "hours_back": hours_back,
                "total_posts_found": len(all_scraped_posts),
                "new_posts_detected": len(new_posts),
                "campaign_matches": len(campaign_matches),
                "analyzed_posts": analyzed_posts,
                "campaign_links": campaign_matches,
                "detected_at": datetime.utcnow()
            }
            
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded for KOL {kol_id}: {e}")
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": e.retry_after,
                "kol_id": kol_id
            }
        except Exception as e:
            logger.error(f"Error detecting posts for KOL {kol_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "kol_id": kol_id
            }
    
    async def analyze_post_for_campaigns(self, post_id: int) -> Dict[str, Any]:
        """Analyze a specific post for campaign content matches."""
        post = self.db.get(Post, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post not found: {post_id}"
            )
        
        try:
            analysis = await self._analyze_post_content(post)
            
            # Update existing campaign links
            await self._update_post_campaign_links(post_id, analysis.campaign_matches)
            
            return {
                "success": True,
                "post_id": post_id,
                "analysis": {
                    "matches": [
                        {
                            "type": match.match_type,
                            "text": match.matched_text,
                            "confidence": match.confidence,
                            "context": match.context,
                            "campaign_id": match.campaign_id,
                            "brief_id": match.brief_id
                        }
                        for match in analysis.matches
                    ],
                    "campaign_matches": analysis.campaign_matches,
                    "brief_matches": analysis.brief_matches,
                    "engagement_score": analysis.engagement_score,
                    "content_quality_score": analysis.content_quality_score,
                    "brand_safety_score": analysis.brand_safety_score
                },
                "analyzed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing post {post_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "post_id": post_id
            }
    
    async def get_campaign_posts(
        self, 
        campaign_id: int,
        include_metrics: bool = True,
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get all posts linked to a campaign."""
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )
        
        try:
            # Build query
            statement = select(Post).where(Post.campaign_links.any(campaign_id))
            
            if days_back:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                statement = statement.where(Post.posted_at >= cutoff_date)
            
            statement = statement.order_by(Post.posted_at.desc())
            
            posts = self.db.exec(statement).all()
            
            # Format posts with metrics if requested
            formatted_posts = []
            total_engagement = 0
            total_reach = 0
            
            for post in posts:
                post_data = {
                    "id": post.id,
                    "kol_id": post.kol_id,
                    "platform": post.platform,
                    "platform_post_id": post.platform_post_id,
                    "content": post.content,
                    "posted_at": post.posted_at,
                    "post_type": post.post_type,
                    "media_urls": post.media_urls,
                    "hashtags": post.hashtags,
                    "mentions": post.mentions
                }
                
                if include_metrics:
                    # Get latest metrics
                    latest_metrics = self.db.exec(
                        select(PostMetrics).where(
                            PostMetrics.post_id == post.id
                        ).order_by(PostMetrics.collected_at.desc())
                    ).first()
                    
                    if latest_metrics:
                        post_data["metrics"] = {
                            "likes": latest_metrics.likes,
                            "comments": latest_metrics.comments,
                            "shares": latest_metrics.shares,
                            "views": latest_metrics.views,
                            "engagement_rate": float(latest_metrics.engagement_rate),
                            "reach": latest_metrics.reach,
                            "impressions": latest_metrics.impressions,
                            "collected_at": latest_metrics.collected_at
                        }
                        
                        total_engagement += latest_metrics.likes + latest_metrics.comments + latest_metrics.shares
                        if latest_metrics.reach:
                            total_reach += latest_metrics.reach
                
                formatted_posts.append(post_data)
            
            # Calculate campaign performance summary
            performance_summary = {
                "total_posts": len(posts),
                "total_engagement": total_engagement,
                "total_reach": total_reach,
                "avg_engagement_per_post": total_engagement / len(posts) if posts else 0,
                "platforms": list(set(p.platform for p in posts)),
                "date_range": {
                    "earliest": min(p.posted_at for p in posts) if posts else None,
                    "latest": max(p.posted_at for p in posts) if posts else None
                }
            }
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "posts": formatted_posts,
                "performance_summary": performance_summary,
                "retrieved_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign posts {campaign_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": campaign_id
            }
    
    async def monitor_campaign_content(self, campaign_id: int) -> Dict[str, Any]:
        """Monitor all KOLs in a campaign for new content."""
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )
        
        try:
            # Get all briefs for this campaign
            briefs = self.db.exec(
                select(Brief).where(Brief.campaign_id == campaign_id)
            ).all()
            
            if not briefs:
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "message": "No briefs found for campaign",
                    "results": []
                }
            
            # Monitor each KOL
            results = []
            total_new_posts = 0
            total_matches = 0
            
            for brief in briefs:
                try:
                    detection_result = await self.detect_new_posts(
                        kol_id=brief.kol_id,
                        hours_back=24  # Check last 24 hours
                    )
                    
                    if detection_result.get("success"):
                        total_new_posts += detection_result.get("new_posts_detected", 0)
                        total_matches += detection_result.get("campaign_matches", 0)
                    
                    results.append({
                        "kol_id": brief.kol_id,
                        "brief_id": brief.id,
                        **detection_result
                    })
                    
                except Exception as e:
                    logger.error(f"Error monitoring KOL {brief.kol_id} for campaign {campaign_id}: {e}")
                    results.append({
                        "kol_id": brief.kol_id,
                        "brief_id": brief.id,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "monitored_kols": len(briefs),
                "total_new_posts": total_new_posts,
                "total_campaign_matches": total_matches,
                "results": results,
                "monitored_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring campaign {campaign_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": campaign_id
            }
    
    async def _create_post_record(self, kol_id: int, post_data: Dict[str, Any]) -> Post:
        """Create a post record in the database."""
        post = Post(
            kol_id=kol_id,
            platform=post_data["platform"],
            platform_post_id=post_data["platform_post_id"],
            content=post_data.get("content", ""),
            posted_at=post_data["posted_at"],
            post_type=post_data.get("post_type", "post"),
            media_urls=post_data.get("media_urls", []),
            hashtags=post_data.get("hashtags", []),
            mentions=post_data.get("mentions", []),
            platform_data=post_data.get("platform_data", {}),
            campaign_links=[]
        )
        
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        
        # Create initial metrics if available
        if "metrics" in post_data:
            metrics_data = post_data["metrics"]
            post_metrics = PostMetrics(
                post_id=post.id,
                likes=metrics_data.get("likes", 0),
                comments=metrics_data.get("comments", 0),
                shares=metrics_data.get("shares", 0),
                views=metrics_data.get("views"),
                engagement_rate=metrics_data.get("engagement_rate", 0.0),
                reach=metrics_data.get("reach"),
                impressions=metrics_data.get("impressions"),
                collected_at=datetime.utcnow()
            )
            
            self.db.add(post_metrics)
            self.db.commit()
        
        return post
    
    async def _analyze_post_content(self, post: Post) -> PostAnalysis:
        """Analyze post content for campaign matches."""
        matches = []
        campaign_matches = set()
        brief_matches = set()
        
        # Get active campaigns and briefs for this KOL
        active_campaigns = self._get_active_campaigns_for_kol(post.kol_id)
        
        content = post.content.lower() if post.content else ""
        hashtags = [h.lower() for h in post.hashtags] if post.hashtags else []
        mentions = [m.lower() for m in post.mentions] if post.mentions else []
        
        for campaign in active_campaigns:
            # Get campaign brief for this KOL
            brief = self.db.exec(
                select(Brief).where(
                    and_(
                        Brief.campaign_id == campaign.id,
                        Brief.kol_id == post.kol_id
                    )
                )
            ).first()
            
            if not brief:
                continue
            
            # Extract campaign keywords and hashtags from brief
            campaign_keywords = self._extract_campaign_keywords(campaign, brief)
            campaign_hashtags = self._extract_campaign_hashtags(campaign, brief)
            
            # Check hashtag matches
            for hashtag in hashtags:
                for campaign_hashtag in campaign_hashtags:
                    if hashtag == campaign_hashtag.lower():
                        matches.append(ContentMatch(
                            match_type=ContentMatchType.HASHTAG,
                            matched_text=hashtag,
                            confidence=self.min_hashtag_confidence,
                            context=f"Hashtag match in post",
                            campaign_id=campaign.id,
                            brief_id=brief.id
                        ))
                        campaign_matches.add(campaign.id)
                        brief_matches.add(brief.id)
            
            # Check keyword matches
            for keyword in campaign_keywords:
                if keyword.lower() in content:
                    confidence = self._calculate_keyword_confidence(keyword, content)
                    if confidence >= self.min_keyword_confidence:
                        matches.append(ContentMatch(
                            match_type=ContentMatchType.KEYWORD,
                            matched_text=keyword,
                            confidence=confidence,
                            context=f"Keyword found in content",
                            campaign_id=campaign.id,
                            brief_id=brief.id
                        ))
                        campaign_matches.add(campaign.id)
                        brief_matches.add(brief.id)
            
            # Check mention matches (brand accounts, etc.)
            campaign_mentions = self._extract_campaign_mentions(campaign, brief)
            for mention in mentions:
                for campaign_mention in campaign_mentions:
                    if mention == campaign_mention.lower():
                        matches.append(ContentMatch(
                            match_type=ContentMatchType.MENTION,
                            matched_text=mention,
                            confidence=self.min_mention_confidence,
                            context=f"Brand mention in post",
                            campaign_id=campaign.id,
                            brief_id=brief.id
                        ))
                        campaign_matches.add(campaign.id)
                        brief_matches.add(brief.id)
        
        # Calculate scores
        engagement_score = self._calculate_engagement_score(post)
        content_quality_score = self._calculate_content_quality_score(post)
        brand_safety_score = self._calculate_brand_safety_score(post)
        
        return PostAnalysis(
            post_id=post.id,
            matches=matches,
            campaign_matches=list(campaign_matches),
            brief_matches=list(brief_matches),
            engagement_score=engagement_score,
            content_quality_score=content_quality_score,
            brand_safety_score=brand_safety_score
        )
    
    def _get_active_campaigns_for_kol(self, kol_id: int) -> List[Campaign]:
        """Get active campaigns that include this KOL."""
        today = datetime.utcnow().date()
        
        # Get campaigns where this KOL has a brief
        campaigns = self.db.exec(
            select(Campaign).join(Brief).where(
                and_(
                    Brief.kol_id == kol_id,
                    Campaign.status.in_(["active", "running"]),
                    Campaign.start_date <= today,
                    or_(
                        Campaign.end_date.is_(None),
                        Campaign.end_date >= today
                    )
                )
            )
        ).all()
        
        return list(campaigns)
    
    def _extract_campaign_keywords(self, campaign: Campaign, brief: Brief) -> List[str]:
        """Extract keywords from campaign and brief content."""
        keywords = []
        
        # Extract from campaign name and description
        if campaign.name:
            keywords.extend(campaign.name.split())
        
        if campaign.description:
            # Simple keyword extraction - in production, use NLP
            words = re.findall(r'\b\w+\b', campaign.description.lower())
            keywords.extend([w for w in words if len(w) > 3])
        
        # Extract from brief content
        if brief.content:
            words = re.findall(r'\b\w+\b', brief.content.lower())
            keywords.extend([w for w in words if len(w) > 3])
        
        # Remove duplicates and common words
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        keywords = list(set([k for k in keywords if k not in common_words]))
        
        return keywords
    
    def _extract_campaign_hashtags(self, campaign: Campaign, brief: Brief) -> List[str]:
        """Extract hashtags from campaign and brief content."""
        hashtags = []
        
        # Extract from campaign description
        if campaign.description:
            hashtags.extend(self.hashtag_pattern.findall(campaign.description))
        
        # Extract from brief content
        if brief.content:
            hashtags.extend(self.hashtag_pattern.findall(brief.content))
        
        return list(set(hashtags))
    
    def _extract_campaign_mentions(self, campaign: Campaign, brief: Brief) -> List[str]:
        """Extract mentions from campaign and brief content."""
        mentions = []
        
        # Extract from campaign description
        if campaign.description:
            mentions.extend(self.mention_pattern.findall(campaign.description))
        
        # Extract from brief content
        if brief.content:
            mentions.extend(self.mention_pattern.findall(brief.content))
        
        return list(set(mentions))
    
    def _calculate_keyword_confidence(self, keyword: str, content: str) -> float:
        """Calculate confidence score for keyword match."""
        # Simple confidence calculation - in production, use more sophisticated NLP
        word_count = len(content.split())
        keyword_occurrences = content.lower().count(keyword.lower())
        
        if word_count == 0:
            return 0.0
        
        # Base confidence on frequency and context
        frequency_score = min(keyword_occurrences / word_count * 10, 1.0)
        
        # Boost confidence if keyword appears in important positions
        if keyword.lower() in content[:100].lower():  # First 100 chars
            frequency_score *= 1.2
        
        return min(frequency_score, 1.0)
    
    def _calculate_engagement_score(self, post: Post) -> float:
        """Calculate engagement score for a post."""
        # Get latest metrics
        latest_metrics = self.db.exec(
            select(PostMetrics).where(
                PostMetrics.post_id == post.id
            ).order_by(PostMetrics.collected_at.desc())
        ).first()
        
        if not latest_metrics:
            return 0.0
        
        # Simple engagement score calculation
        total_engagement = latest_metrics.likes + latest_metrics.comments + latest_metrics.shares
        
        if latest_metrics.reach and latest_metrics.reach > 0:
            engagement_rate = total_engagement / latest_metrics.reach
        else:
            engagement_rate = float(latest_metrics.engagement_rate)
        
        # Normalize to 0-1 scale (assuming 10% is excellent engagement)
        return min(engagement_rate / 0.1, 1.0)
    
    def _calculate_content_quality_score(self, post: Post) -> float:
        """Calculate content quality score."""
        score = 0.5  # Base score
        
        if post.content:
            # Length factor
            content_length = len(post.content)
            if 50 <= content_length <= 500:  # Optimal length
                score += 0.2
            elif content_length > 500:
                score += 0.1
            
            # Media factor
            if post.media_urls and len(post.media_urls) > 0:
                score += 0.2
            
            # Hashtag factor
            if post.hashtags and 1 <= len(post.hashtags) <= 10:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_brand_safety_score(self, post: Post) -> float:
        """Calculate brand safety score."""
        # Simple brand safety check - in production, use AI moderation
        if not post.content:
            return 0.8  # Neutral score for no content
        
        content_lower = post.content.lower()
        
        # Check for potentially unsafe content
        unsafe_keywords = ['hate', 'violence', 'drugs', 'alcohol', 'gambling', 'adult']
        unsafe_count = sum(1 for keyword in unsafe_keywords if keyword in content_lower)
        
        if unsafe_count == 0:
            return 1.0  # Safe
        elif unsafe_count <= 2:
            return 0.7  # Moderate risk
        else:
            return 0.3  # High risk
    
    async def _link_post_to_campaign(self, post_id: int, campaign_id: int) -> None:
        """Link a post to a campaign."""
        post = self.db.get(Post, post_id)
        if post and campaign_id not in (post.campaign_links or []):
            if post.campaign_links is None:
                post.campaign_links = []
            post.campaign_links.append(campaign_id)
            self.db.add(post)
            self.db.commit()
    
    async def _update_post_campaign_links(self, post_id: int, campaign_ids: List[int]) -> None:
        """Update campaign links for a post."""
        post = self.db.get(Post, post_id)
        if post:
            post.campaign_links = campaign_ids
            self.db.add(post)
            self.db.commit()