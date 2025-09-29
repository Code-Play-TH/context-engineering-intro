"""
Content Monitoring Service

Main service for detecting and monitoring KOL content across social media platforms.
Implements the content detection algorithm from the PRP with AI-powered analysis.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.models.content import ContentPost, ContentStats, VerificationStatus
from app.schemas.content_monitoring import (
    ContentMatchResult, PlatformPost, SocialPlatform,
    AnalysisType, ContentDetectionRequest
)
from app.services.social_media.factory import SocialMediaServiceFactory
from app.services.content_monitoring.ai_analyzer import AIContentAnalyzer
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ContentMonitorService:
    """
    Main content monitoring service that handles:
    - Content detection across platforms
    - AI-powered content analysis
    - Campaign matching and verification
    - Performance tracking scheduling
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_analyzer = AIContentAnalyzer()
        self.social_media_factory = SocialMediaServiceFactory()
        self.confidence_threshold = settings.CONTENT_DETECTION_CONFIDENCE_THRESHOLD

    async def detect_new_content(
        self,
        kol: KOL,
        campaign: Campaign,
        platforms: Optional[List[SocialPlatform]] = None
    ) -> List[ContentPost]:
        """
        Detect new content for a KOL in a specific campaign.

        Args:
            kol: KOL to monitor
            campaign: Campaign to match content against
            platforms: List of platforms to check (optional)

        Returns:
            List of detected content posts
        """
        logger.info(f"Starting content detection for KOL {kol.id} in campaign {campaign.id}")

        detected_posts = []

        # Get platforms to check
        if not platforms:
            platforms = list(kol.social_media_accounts.keys())

        for platform_name in platforms:
            account_data = kol.social_media_accounts.get(platform_name)
            if not account_data:
                continue

            try:
                platform_posts = await self._check_platform_content(
                    platform_name, account_data, campaign, kol
                )
                detected_posts.extend(platform_posts)

            except Exception as e:
                logger.error(f"Failed to check {platform_name} for KOL {kol.id}: {e}")
                await self._record_platform_error(kol.id, platform_name, str(e))
                continue

        # Batch save all detected posts
        if detected_posts:
            for post in detected_posts:
                self.db.add(post)
            await self.db.commit()
            logger.info(f"Detected {len(detected_posts)} new posts for KOL {kol.id}")

        return detected_posts

    async def _check_platform_content(
        self,
        platform_name: str,
        account_data: Dict[str, Any],
        campaign: Campaign,
        kol: KOL
    ) -> List[ContentPost]:
        """
        Check content for a specific platform.

        Args:
            platform_name: Name of the social media platform
            account_data: Account information for the platform
            campaign: Campaign to match against
            kol: KOL being monitored

        Returns:
            List of detected content posts
        """
        platform = SocialPlatform(platform_name.lower())
        service = self.social_media_factory.get_service(platform)

        if not service:
            logger.warning(f"No service available for platform: {platform_name}")
            return []

        # Get recent posts from the platform
        handle = account_data.get("handle")
        if not handle:
            logger.warning(f"No handle found for {platform_name} for KOL {kol.id}")
            return []

        try:
            recent_posts = await service.get_recent_posts(
                handle=handle,
                since=campaign.start_date,
                limit=50
            )
        except Exception as e:
            logger.error(f"Failed to fetch posts from {platform_name}: {e}")
            return []

        detected_posts = []

        for post in recent_posts:
            # Check if we already have this post
            existing_post = await self._check_existing_post(post.id, platform_name)
            if existing_post:
                continue

            # Analyze content match with campaign
            match_result = await self._analyze_content_match(post, campaign)

            if match_result.is_match:
                content_post = await self._create_content_post(
                    post, kol, campaign, platform_name, match_result
                )
                detected_posts.append(content_post)

                # Schedule stats collection
                await self._schedule_stats_collection(content_post)

                # Send notification for high-confidence matches
                if match_result.confidence > 0.8:
                    await self._send_content_detected_notification(content_post, campaign)

        return detected_posts

    async def _analyze_content_match(
        self,
        post: PlatformPost,
        campaign: Campaign
    ) -> ContentMatchResult:
        """
        Multi-layer content analysis for campaign verification.

        Args:
            post: Social media post to analyze
            campaign: Campaign to match against

        Returns:
            Content match result with confidence score
        """
        confidence = 0.0
        matched_criteria = []
        analysis_details = {}

        # Layer 1: Keyword/Hashtag matching (40% weight)
        keyword_score = await self._check_keyword_match(post, campaign)
        confidence += keyword_score * 0.4
        analysis_details["keyword_score"] = keyword_score

        if keyword_score > 0.5:
            matched_criteria.append("keywords")

        # Layer 2: Brand mention detection (30% weight)
        brand_score = await self._check_brand_mentions(post, campaign)
        confidence += brand_score * 0.3
        analysis_details["brand_score"] = brand_score

        if brand_score > 0.5:
            matched_criteria.append("brand_mentions")

        # Layer 3: AI-powered content analysis (20% weight)
        ai_score = await self._ai_content_analysis(post, campaign)
        confidence += ai_score * 0.2
        analysis_details["ai_score"] = ai_score

        if ai_score > 0.6:
            matched_criteria.append("ai_content_analysis")

        # Layer 4: Timing and context (10% weight)
        timing_score = self._check_timing_relevance(post, campaign)
        confidence += timing_score * 0.1
        analysis_details["timing_score"] = timing_score

        if timing_score > 0.5:
            matched_criteria.append("timing")

        # Minimum threshold for detection
        is_match = confidence >= self.confidence_threshold and len(matched_criteria) >= 2

        return ContentMatchResult(
            is_match=is_match,
            confidence=min(1.0, confidence),
            matched_criteria=matched_criteria,
            analysis_details=analysis_details
        )

    async def _check_keyword_match(
        self,
        post: PlatformPost,
        campaign: Campaign
    ) -> float:
        """
        Check for campaign keywords and hashtags.

        Args:
            post: Social media post to check
            campaign: Campaign with keyword requirements

        Returns:
            Keyword match score (0.0 to 1.0)
        """
        content_lower = post.content.lower()
        hashtags_lower = [tag.lower() for tag in post.hashtags]

        # Get campaign keywords (these would be in campaign model)
        required_keywords = getattr(campaign, 'required_keywords', []) or []
        optional_keywords = getattr(campaign, 'optional_keywords', []) or []
        required_hashtags = getattr(campaign, 'required_hashtags', []) or []

        score = 0.0

        # Required keywords (must have at least 70%)
        if required_keywords:
            found_required = sum(1 for kw in required_keywords if kw.lower() in content_lower)
            required_ratio = found_required / len(required_keywords)
            if required_ratio < 0.7:
                return 0.0  # Fail if not enough required keywords
            score += 0.5

        # Required hashtags (must have at least 50%)
        if required_hashtags:
            found_hashtags = sum(1 for tag in required_hashtags if tag.lower() in hashtags_lower)
            hashtag_ratio = found_hashtags / len(required_hashtags)
            if hashtag_ratio < 0.5:
                return 0.0
            score += 0.3

        # Optional keywords (bonus points)
        if optional_keywords:
            found_optional = sum(1 for kw in optional_keywords if kw.lower() in content_lower)
            optional_ratio = found_optional / len(optional_keywords)
            score += optional_ratio * 0.2

        return min(1.0, score)

    async def _check_brand_mentions(
        self,
        post: PlatformPost,
        campaign: Campaign
    ) -> float:
        """
        Check for brand mentions in the content.

        Args:
            post: Social media post to check
            campaign: Campaign with brand information

        Returns:
            Brand mention score (0.0 to 1.0)
        """
        content_lower = post.content.lower()
        mentions_lower = [mention.lower() for mention in post.mentions]

        # Get brand information (these would be in campaign model)
        brand_names = getattr(campaign, 'brand_names', []) or []
        brand_handles = getattr(campaign, 'brand_handles', []) or []

        score = 0.0

        # Check for brand name mentions in content
        for brand in brand_names:
            if brand.lower() in content_lower:
                score += 0.3

        # Check for brand handle mentions
        for handle in brand_handles:
            if handle.lower() in mentions_lower:
                score += 0.4

        # Check for product names or campaign-specific terms
        product_names = getattr(campaign, 'product_names', []) or []
        for product in product_names:
            if product.lower() in content_lower:
                score += 0.2

        return min(1.0, score)

    async def _ai_content_analysis(
        self,
        post: PlatformPost,
        campaign: Campaign
    ) -> float:
        """
        Use AI to analyze content relevance to campaign.

        Args:
            post: Social media post to analyze
            campaign: Campaign to match against

        Returns:
            AI analysis score (0.0 to 1.0)
        """
        try:
            # Use AI analyzer for content relevance
            analysis_result = await self.ai_analyzer.analyze_content(
                content_text=post.content,
                analysis_types=[
                    AnalysisType.SENTIMENT,
                    AnalysisType.TOPICS,
                    AnalysisType.QUALITY,
                    AnalysisType.ENGAGEMENT_PREDICTION
                ]
            )

            # Campaign brief content (would be stored in campaign)
            brief_content = getattr(campaign, 'brief_content', '') or ''
            target_keywords = getattr(campaign, 'target_keywords', []) or []

            # Simple relevance scoring based on topic overlap
            post_topics = analysis_result.get('topics', [])
            sentiment_score = analysis_result.get('sentiment_score', 0)
            quality_score = analysis_result.get('quality_score', 0)

            relevance_score = 0.0

            # Topic relevance
            if post_topics and target_keywords:
                topic_overlap = len(set(post_topics) & set(target_keywords))
                relevance_score += min(topic_overlap / len(target_keywords), 0.5)

            # Sentiment alignment (positive campaigns prefer positive content)
            if sentiment_score > 0.1:  # Positive sentiment
                relevance_score += 0.2

            # Quality factor
            relevance_score += quality_score * 0.3

            return min(1.0, relevance_score)

        except Exception as e:
            logger.error(f"AI content analysis failed: {e}")
            return 0.0

    def _check_timing_relevance(
        self,
        post: PlatformPost,
        campaign: Campaign
    ) -> float:
        """
        Check timing relevance of the post to campaign.

        Args:
            post: Social media post to check
            campaign: Campaign with timing requirements

        Returns:
            Timing relevance score (0.0 to 1.0)
        """
        # Check if post is within campaign period
        if not (campaign.start_date <= post.created_at <= campaign.end_date):
            return 0.0

        # Score based on how close to campaign milestones
        campaign_duration = (campaign.end_date - campaign.start_date).days
        days_since_start = (post.created_at - campaign.start_date).days

        # Higher score for posts closer to campaign start (when activity is expected)
        if days_since_start <= 7:
            return 1.0
        elif days_since_start <= 14:
            return 0.8
        elif days_since_start <= campaign_duration * 0.5:
            return 0.6
        else:
            return 0.4

    async def _create_content_post(
        self,
        post: PlatformPost,
        kol: KOL,
        campaign: Campaign,
        platform_name: str,
        match_result: ContentMatchResult
    ) -> ContentPost:
        """
        Create a new ContentPost entity from detected content.

        Args:
            post: Platform post data
            kol: KOL who created the content
            campaign: Related campaign
            platform_name: Social media platform
            match_result: Content match analysis result

        Returns:
            New ContentPost entity
        """
        content_post = ContentPost(
            kol_id=kol.id,
            campaign_id=campaign.id,
            platform=platform_name,
            platform_post_id=post.id,
            url=post.url,
            content=post.content,
            hashtags=post.hashtags,
            mentions=post.mentions,
            posted_at=post.created_at,
            detected_at=datetime.utcnow(),
            verification_status=VerificationStatus.PENDING,
            confidence_score=match_result.confidence,
            match_criteria=match_result.matched_criteria,
            analysis_details=match_result.analysis_details
        )

        return content_post

    async def _check_existing_post(
        self,
        platform_post_id: str,
        platform: str
    ) -> Optional[ContentPost]:
        """
        Check if we already have this post in our database.

        Args:
            platform_post_id: ID of the post on the platform
            platform: Social media platform name

        Returns:
            Existing ContentPost if found, None otherwise
        """
        stmt = select(ContentPost).where(
            and_(
                ContentPost.platform_post_id == platform_post_id,
                ContentPost.platform == platform
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _schedule_stats_collection(self, content_post: ContentPost) -> None:
        """
        Schedule automated statistics collection for the content post.

        Args:
            content_post: Content post to schedule stats collection for
        """
        from app.tasks.content_monitoring_tasks import collect_content_stats

        # Schedule collection at multiple intervals
        collection_times = [
            datetime.utcnow() + timedelta(hours=24),   # 24 hours
            datetime.utcnow() + timedelta(days=3),     # 3 days
            datetime.utcnow() + timedelta(days=5),     # 5 days
            datetime.utcnow() + timedelta(days=7),     # 7 days
        ]

        for collection_time in collection_times:
            try:
                collect_content_stats.apply_async(
                    args=[content_post.id],
                    eta=collection_time
                )
                logger.info(f"Scheduled stats collection for post {content_post.id} at {collection_time}")
            except Exception as e:
                logger.error(f"Failed to schedule stats collection: {e}")

    async def _send_content_detected_notification(
        self,
        content_post: ContentPost,
        campaign: Campaign
    ) -> None:
        """
        Send notification for newly detected content.

        Args:
            content_post: Detected content post
            campaign: Related campaign
        """
        try:
            # This would integrate with the communication service
            logger.info(f"High-confidence content detected: Post {content_post.id} for campaign {campaign.id}")
            # TODO: Implement actual notification sending
        except Exception as e:
            logger.error(f"Failed to send content detection notification: {e}")

    async def _record_platform_error(
        self,
        kol_id: int,
        platform: str,
        error: str
    ) -> None:
        """
        Record platform monitoring error for analysis.

        Args:
            kol_id: ID of the KOL
            platform: Platform that failed
            error: Error message
        """
        logger.error(f"Platform error for KOL {kol_id} on {platform}: {error}")
        # TODO: Store in error tracking table for analysis

    async def verify_content_manually(
        self,
        content_post_id: int,
        verification_status: VerificationStatus,
        notes: Optional[str] = None
    ) -> ContentPost:
        """
        Manually verify detected content.

        Args:
            content_post_id: ID of the content post
            verification_status: New verification status
            notes: Optional verification notes

        Returns:
            Updated content post
        """
        stmt = select(ContentPost).where(ContentPost.id == content_post_id)
        result = await self.db.execute(stmt)
        content_post = result.scalar_one_or_none()

        if not content_post:
            raise ValueError(f"Content post {content_post_id} not found")

        content_post.verification_status = verification_status
        content_post.verified_at = datetime.utcnow()

        if notes:
            content_post.verification_notes = notes

        await self.db.commit()
        logger.info(f"Content post {content_post_id} verified as {verification_status}")

        return content_post

    async def get_campaign_content_summary(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Get content detection summary for a campaign.

        Args:
            campaign_id: ID of the campaign

        Returns:
            Content summary statistics
        """
        stmt = select(ContentPost).where(ContentPost.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        content_posts = result.scalars().all()

        if not content_posts:
            return {
                "total_posts": 0,
                "verified_posts": 0,
                "pending_posts": 0,
                "rejected_posts": 0,
                "platforms": {},
                "average_confidence": 0.0
            }

        # Calculate statistics
        verified_count = sum(1 for post in content_posts
                           if post.verification_status == VerificationStatus.VERIFIED)
        pending_count = sum(1 for post in content_posts
                          if post.verification_status == VerificationStatus.PENDING)
        rejected_count = sum(1 for post in content_posts
                           if post.verification_status == VerificationStatus.REJECTED)

        # Platform breakdown
        platform_counts = {}
        for post in content_posts:
            platform_counts[post.platform] = platform_counts.get(post.platform, 0) + 1

        # Average confidence
        confidences = [post.confidence_score for post in content_posts if post.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "total_posts": len(content_posts),
            "verified_posts": verified_count,
            "pending_posts": pending_count,
            "rejected_posts": rejected_count,
            "platforms": platform_counts,
            "average_confidence": avg_confidence
        }