"""Scraping service that integrates rate limit management with social media scrapers."""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session
import logging

from app.services.scrapers import ScraperFactory, ScraperManager, SocialMetrics, PostData
from datetime import timedelta
from app.services.rate_limit_manager import RateLimitManager, RateLimitExceeded
from app.models.kol import KOL
from app.models.kol_metrics import KOLMetrics
from app.models.post import Post
from app.models.social_handle import SocialHandle

logger = logging.getLogger(__name__)


class ScrapingService:
    """Service that coordinates scraping with rate limit management."""
    
    def __init__(self, db: Session, platform_configs: Dict[str, Dict[str, Any]]):
        self.db = db
        self.rate_limit_manager = RateLimitManager(db)
        self.scraper_manager = ScraperManager(platform_configs)
    
    async def scrape_kol_metrics(
        self, 
        kol_id: int, 
        platforms: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Scrape metrics for a KOL across specified platforms."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise ValueError(f"KOL not found: {kol_id}")
        
        # Get KOL's social handles
        social_handles = kol.social_handles
        if not social_handles:
            logger.warning(f"No social handles found for KOL {kol_id}")
            return {"error": "No social handles configured"}
        
        # Filter platforms if specified
        if platforms:
            social_handles = [h for h in social_handles if h.platform in platforms]
        
        results = {}
        errors = []
        
        for handle in social_handles:
            platform = handle.platform
            username = handle.handle
            
            try:
                # Check if we should scrape (rate limits, recent data, etc.)
                if not force_refresh and not await self._should_scrape(kol_id, platform):
                    logger.info(f"Skipping {platform} scraping for KOL {kol_id} (recent data available)")
                    continue
                
                # Get scraper for platform
                scraper = self.scraper_manager.get_scraper(platform)
                if not scraper:
                    errors.append(f"No scraper available for platform: {platform}")
                    continue
                
                # Scrape with rate limit management
                metrics = await self._scrape_with_rate_limits(
                    scraper, platform, username, "get_user_metrics"
                )
                
                if metrics:
                    # Store metrics in database
                    kol_metrics = await self._store_kol_metrics(kol_id, platform, metrics)
                    results[platform] = {
                        "success": True,
                        "metrics": metrics,
                        "stored_id": kol_metrics.id if kol_metrics else None
                    }
                else:
                    errors.append(f"Failed to get metrics for {platform}")
                
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded for {platform}: {e}")
                errors.append(f"Rate limit exceeded for {platform}: {e.retry_after}s")
                
            except Exception as e:
                logger.error(f"Error scraping {platform} for KOL {kol_id}: {e}")
                errors.append(f"Error scraping {platform}: {str(e)}")
        
        # Update KOL's last scraped timestamp
        if results:
            kol.last_scraped_at = datetime.utcnow()
            self.db.add(kol)
            self.db.commit()
        
        return {
            "kol_id": kol_id,
            "scraped_at": datetime.utcnow(),
            "results": results,
            "errors": errors,
            "platforms_scraped": len(results),
            "total_platforms": len(social_handles)
        }
    
    async def scrape_kol_posts(
        self, 
        kol_id: int, 
        platforms: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Scrape recent posts for a KOL."""
        kol = self.db.get(KOL, kol_id)
        if not kol:
            raise ValueError(f"KOL not found: {kol_id}")
        
        social_handles = kol.social_handles
        if platforms:
            social_handles = [h for h in social_handles if h.platform in platforms]
        
        results = {}
        errors = []
        
        for handle in social_handles:
            platform = handle.platform
            username = handle.handle
            
            try:
                scraper = self.scraper_manager.get_scraper(platform)
                if not scraper:
                    errors.append(f"No scraper available for platform: {platform}")
                    continue
                
                # Scrape posts with rate limit management
                posts = await self._scrape_with_rate_limits(
                    scraper, platform, username, "get_recent_posts", limit=limit
                )
                
                if posts:
                    # Store new posts in database
                    stored_posts = await self._store_posts(kol_id, platform, posts)
                    results[platform] = {
                        "success": True,
                        "posts_found": len(posts),
                        "posts_stored": len(stored_posts)
                    }
                else:
                    errors.append(f"No posts found for {platform}")
                
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded for {platform}: {e}")
                errors.append(f"Rate limit exceeded for {platform}: {e.retry_after}s")
                
            except Exception as e:
                logger.error(f"Error scraping posts from {platform} for KOL {kol_id}: {e}")
                errors.append(f"Error scraping {platform} posts: {str(e)}")
        
        # Update KOL's last post check timestamp
        if results:
            kol.last_post_check_at = datetime.utcnow()
            self.db.add(kol)
            self.db.commit()
        
        return {
            "kol_id": kol_id,
            "scraped_at": datetime.utcnow(),
            "results": results,
            "errors": errors,
            "platforms_scraped": len(results)
        }
    
    async def batch_scrape_kols(
        self, 
        kol_ids: List[int], 
        platforms: Optional[List[str]] = None,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Scrape metrics for multiple KOLs with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_single_kol(kol_id: int):
            async with semaphore:
                return await self.scrape_kol_metrics(kol_id, platforms)
        
        # Execute scraping tasks
        tasks = [scrape_single_kol(kol_id) for kol_id in kol_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = []
        failed = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({
                    "kol_id": kol_ids[i],
                    "error": str(result)
                })
            else:
                if result.get("results"):
                    successful.append(result)
                else:
                    failed.append(result)
        
        return {
            "batch_scraped_at": datetime.utcnow(),
            "total_kols": len(kol_ids),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(kol_ids) * 100,
            "results": successful,
            "errors": failed
        }
    
    async def get_scraping_status(self) -> Dict[str, Any]:
        """Get current scraping system status."""
        # Get rate limit status
        rate_limits = await self.rate_limit_manager.get_all_rate_limits()
        
        # Get scraper health
        scraper_health = await self.scraper_manager.health_check_all()
        
        # Get queue status
        queue_status = await self.rate_limit_manager.get_queue_status()
        
        return {
            "timestamp": datetime.utcnow(),
            "rate_limits": rate_limits,
            "scraper_health": scraper_health,
            "queue_status": queue_status,
            "available_platforms": self.scraper_manager.get_available_platforms()
        }
    
    async def _scrape_with_rate_limits(
        self, 
        scraper, 
        platform: str, 
        username: str, 
        method: str,
        **kwargs
    ) -> Any:
        """Execute scraping method with rate limit management."""
        # Check rate limits first
        if not await self.rate_limit_manager.check_rate_limit(platform):
            # Queue the request if rate limited
            logger.info(f"Rate limit reached for {platform}, queuing request")
            
            scraper_method = getattr(scraper, method)
            return await self.rate_limit_manager.queue_request(
                platform, scraper_method, username, **kwargs
            )
        
        # Execute directly if within limits
        await self.rate_limit_manager.record_request(platform)
        
        scraper_method = getattr(scraper, method)
        return await scraper_method(username, **kwargs)
    
    async def _should_scrape(self, kol_id: int, platform: str) -> bool:
        """Determine if we should scrape based on recent data and rate limits."""
        # Check if we have recent data (within last hour)
        from sqlmodel import select
        
        recent_metrics = self.db.exec(
            select(KOLMetrics).where(
                KOLMetrics.kol_id == kol_id,
                KOLMetrics.platform == platform,
                KOLMetrics.scraped_at > datetime.utcnow() - timedelta(hours=1)
            ).order_by(KOLMetrics.scraped_at.desc())
        ).first()
        
        if recent_metrics:
            return False
        
        # Check rate limits
        return await self.rate_limit_manager.check_rate_limit(platform)
    
    async def _store_kol_metrics(
        self, 
        kol_id: int, 
        platform: str, 
        metrics: SocialMetrics
    ) -> Optional[KOLMetrics]:
        """Store KOL metrics in database."""
        try:
            # Get previous metrics for growth calculation
            from sqlmodel import select
            
            previous_metrics = self.db.exec(
                select(KOLMetrics).where(
                    KOLMetrics.kol_id == kol_id,
                    KOLMetrics.platform == platform
                ).order_by(KOLMetrics.scraped_at.desc())
            ).first()
            
            # Create new metrics record
            kol_metrics = KOLMetrics(
                kol_id=kol_id,
                platform=platform,
                follower_count=metrics.follower_count,
                following_count=metrics.following_count,
                post_count=metrics.post_count,
                engagement_rate=metrics.engagement_rate,
                avg_likes_per_post=metrics.avg_likes,
                avg_comments_per_post=metrics.avg_comments,
                avg_views_per_post=metrics.avg_views,
                platform_specific_data=metrics.platform_specific or {},
                scraped_at=datetime.utcnow(),
                scraping_success=True
            )
            
            # Calculate growth metrics
            if previous_metrics:
                kol_metrics.calculate_growth_from_previous(previous_metrics)
            
            self.db.add(kol_metrics)
            self.db.commit()
            self.db.refresh(kol_metrics)
            
            return kol_metrics
            
        except Exception as e:
            logger.error(f"Error storing KOL metrics: {e}")
            return None
    
    async def _store_posts(
        self, 
        kol_id: int, 
        platform: str, 
        posts: List[PostData]
    ) -> List[Post]:
        """Store posts in database, avoiding duplicates."""
        stored_posts = []
        
        for post_data in posts:
            try:
                # Check if post already exists
                from sqlmodel import select
                
                existing_post = self.db.exec(
                    select(Post).where(
                        Post.kol_id == kol_id,
                        Post.platform == platform,
                        Post.post_id == post_data.post_id
                    )
                ).first()
                
                if existing_post:
                    continue  # Skip duplicate
                
                # Create new post record
                post = Post(
                    kol_id=kol_id,
                    platform=platform,
                    post_id=post_data.post_id,
                    post_url=post_data.url,
                    post_type=post_data.post_type,
                    caption=post_data.caption,
                    hashtags=post_data.hashtags,
                    mentions=post_data.mentions,
                    posted_at=post_data.posted_at,
                    detected_at=datetime.utcnow(),
                    initial_likes=post_data.likes,
                    initial_comments=post_data.comments,
                    initial_shares=post_data.shares,
                    initial_views=post_data.views
                )
                
                self.db.add(post)
                stored_posts.append(post)
                
            except Exception as e:
                logger.error(f"Error storing post {post_data.post_id}: {e}")
                continue
        
        if stored_posts:
            self.db.commit()
            for post in stored_posts:
                self.db.refresh(post)
        
        return stored_posts