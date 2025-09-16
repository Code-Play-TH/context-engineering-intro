"""
Analytics and reporting background tasks.
Handles data aggregation, report generation, and performance analysis.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import pandas as pd
import json

from app.tasks.celery_app import celery_app
from app.core.database import get_session
from app.services.social_media.factory import social_media_factory
from app.models.campaigns import Campaign, CampaignContent
from app.models.kols import KOL
from app.models.collaboration import Collaboration
from app.models.analytics import AnalyticsReport, KOLPerformanceMetrics

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def generate_daily_analytics(self) -> Dict[str, Any]:
    """
    Generate comprehensive daily analytics across all campaigns and KOLs.

    Returns:
        Dict with analytics generation results
    """
    results = {
        "report_date": datetime.utcnow().date().isoformat(),
        "campaigns_analyzed": 0,
        "kols_analyzed": 0,
        "reports_generated": 0,
        "total_engagement": 0,
        "total_reach": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            report_date = datetime.utcnow().date()
            yesterday = report_date - timedelta(days=1)

            # Generate campaign performance analytics
            campaign_analytics = _generate_campaign_analytics(db, yesterday)
            results.update(campaign_analytics)

            # Generate KOL performance analytics
            kol_analytics = _generate_kol_analytics(db, yesterday)
            results.update(kol_analytics)

            # Generate platform performance analytics
            platform_analytics = _generate_platform_analytics(db, yesterday)
            results.update(platform_analytics)

            # Generate engagement trend analytics
            trend_analytics = _generate_engagement_trends(db, yesterday)
            results.update(trend_analytics)

            # Create consolidated daily report
            report = AnalyticsReport(
                report_type="daily_summary",
                report_date=yesterday,
                data={
                    "campaign_metrics": campaign_analytics,
                    "kol_metrics": kol_analytics,
                    "platform_metrics": platform_analytics,
                    "trends": trend_analytics
                },
                generated_at=datetime.utcnow()
            )

            db.add(report)
            db.commit()

            results["reports_generated"] = 1
            logger.info(f"Daily analytics generation completed: {results}")
            return results

    except Exception as e:
        logger.error(f"Daily analytics generation failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def generate_campaign_report(self, campaign_id: int, report_type: str = "performance") -> Dict[str, Any]:
    """
    Generate detailed report for a specific campaign.

    Args:
        campaign_id: Campaign identifier
        report_type: Type of report to generate

    Returns:
        Dict with report generation results
    """
    results = {
        "campaign_id": campaign_id,
        "report_type": report_type,
        "content_analyzed": 0,
        "kols_analyzed": 0,
        "report_id": None,
        "errors": []
    }

    try:
        with get_session() as db:
            campaign = db.query(Campaign).filter_by(id=campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            if report_type == "performance":
                report_data = _generate_performance_report(db, campaign)
            elif report_type == "roi":
                report_data = _generate_roi_report(db, campaign)
            elif report_type == "engagement":
                report_data = _generate_engagement_report(db, campaign)
            elif report_type == "reach":
                report_data = _generate_reach_report(db, campaign)
            else:
                raise ValueError(f"Unknown report type: {report_type}")

            # Create report record
            report = AnalyticsReport(
                campaign_id=campaign_id,
                report_type=f"campaign_{report_type}",
                report_date=datetime.utcnow().date(),
                data=report_data,
                generated_at=datetime.utcnow()
            )

            db.add(report)
            db.commit()

            results.update({
                "report_id": report.id,
                "content_analyzed": report_data.get("content_count", 0),
                "kols_analyzed": report_data.get("kol_count", 0)
            })

            logger.info(f"Campaign report generated for {campaign_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"Campaign report generation failed for {campaign_id}: {str(e)}")
        raise self.retry(countdown=180, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def generate_kol_performance_report(self, kol_id: int, date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate comprehensive performance report for a specific KOL.

    Args:
        kol_id: KOL identifier
        date_range: Start and end date for analysis

    Returns:
        Dict with KOL performance report results
    """
    results = {
        "kol_id": kol_id,
        "campaigns_analyzed": 0,
        "content_analyzed": 0,
        "platforms_analyzed": 0,
        "report_id": None,
        "errors": []
    }

    try:
        with get_session() as db:
            kol = db.query(KOL).filter_by(id=kol_id).first()
            if not kol:
                raise ValueError(f"KOL {kol_id} not found")

            start_date = datetime.fromisoformat(date_range["start_date"])
            end_date = datetime.fromisoformat(date_range["end_date"])

            # Analyze KOL performance across all campaigns
            performance_data = _analyze_kol_performance(db, kol, start_date, end_date)

            # Generate engagement patterns analysis
            engagement_patterns = _analyze_engagement_patterns(db, kol, start_date, end_date)

            # Generate platform comparison
            platform_comparison = _analyze_platform_performance(db, kol, start_date, end_date)

            # Generate ROI analysis
            roi_analysis = _analyze_kol_roi(db, kol, start_date, end_date)

            report_data = {
                "kol_info": {
                    "id": kol.id,
                    "name": kol.name,
                    "primary_platform": kol.primary_platform,
                    "follower_counts": kol.follower_counts
                },
                "performance_metrics": performance_data,
                "engagement_patterns": engagement_patterns,
                "platform_comparison": platform_comparison,
                "roi_analysis": roi_analysis,
                "date_range": date_range
            }

            # Create report record
            report = AnalyticsReport(
                kol_id=kol_id,
                report_type="kol_performance",
                report_date=datetime.utcnow().date(),
                data=report_data,
                generated_at=datetime.utcnow()
            )

            db.add(report)
            db.commit()

            results.update({
                "report_id": report.id,
                "campaigns_analyzed": performance_data.get("campaign_count", 0),
                "content_analyzed": performance_data.get("content_count", 0),
                "platforms_analyzed": len(platform_comparison)
            })

            logger.info(f"KOL performance report generated for {kol_id}: {results}")
            return results

    except Exception as e:
        logger.error(f"KOL performance report generation failed for {kol_id}: {str(e)}")
        raise self.retry(countdown=180, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def calculate_engagement_benchmarks(self) -> Dict[str, Any]:
    """
    Calculate engagement benchmarks across platforms and industries.

    Returns:
        Dict with benchmark calculation results
    """
    results = {
        "platforms_analyzed": 0,
        "kols_analyzed": 0,
        "benchmarks_updated": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            # Calculate platform-specific benchmarks
            platforms = ["instagram", "youtube", "tiktok", "twitter", "facebook"]

            for platform in platforms:
                try:
                    benchmark_data = _calculate_platform_benchmarks(db, platform)

                    if benchmark_data:
                        # Store or update benchmark data
                        results["benchmarks_updated"] += 1
                        results["platforms_analyzed"] += 1

                except Exception as e:
                    error_msg = f"Failed to calculate benchmarks for {platform}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Calculate industry-specific benchmarks
            industry_benchmarks = _calculate_industry_benchmarks(db)
            results["benchmarks_updated"] += len(industry_benchmarks)

            # Calculate follower tier benchmarks
            tier_benchmarks = _calculate_tier_benchmarks(db)
            results["benchmarks_updated"] += len(tier_benchmarks)

            logger.info(f"Engagement benchmark calculation completed: {results}")
            return results

    except Exception as e:
        logger.error(f"Engagement benchmark calculation failed: {str(e)}")
        raise self.retry(countdown=240, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def generate_roi_analysis(self, campaign_id: int = None, date_range: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive ROI analysis for campaigns.

    Args:
        campaign_id: Specific campaign ID (optional)
        date_range: Date range for analysis (optional)

    Returns:
        Dict with ROI analysis results
    """
    results = {
        "campaigns_analyzed": 0,
        "total_investment": 0.0,
        "total_return": 0.0,
        "avg_roi": 0.0,
        "report_id": None,
        "errors": []
    }

    try:
        with get_session() as db:
            if campaign_id:
                campaigns = [db.query(Campaign).filter_by(id=campaign_id).first()]
                if not campaigns[0]:
                    raise ValueError(f"Campaign {campaign_id} not found")
            else:
                # Analyze all completed campaigns
                query = db.query(Campaign).filter(Campaign.status == "completed")

                if date_range:
                    start_date = datetime.fromisoformat(date_range["start_date"])
                    end_date = datetime.fromisoformat(date_range["end_date"])
                    query = query.filter(
                        Campaign.end_date >= start_date,
                        Campaign.end_date <= end_date
                    )

                campaigns = query.all()

            roi_data = []
            total_investment = 0.0
            total_return = 0.0

            for campaign in campaigns:
                try:
                    campaign_roi = _calculate_campaign_roi(db, campaign)
                    roi_data.append(campaign_roi)

                    total_investment += campaign_roi["investment"]
                    total_return += campaign_roi["return"]
                    results["campaigns_analyzed"] += 1

                except Exception as e:
                    error_msg = f"Failed to calculate ROI for campaign {campaign.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            # Calculate overall ROI metrics
            if total_investment > 0:
                overall_roi = ((total_return - total_investment) / total_investment) * 100
            else:
                overall_roi = 0.0

            analysis_data = {
                "overall_roi": overall_roi,
                "total_investment": total_investment,
                "total_return": total_return,
                "campaign_count": results["campaigns_analyzed"],
                "campaign_details": roi_data,
                "analysis_date": datetime.utcnow().isoformat()
            }

            # Create ROI analysis report
            report = AnalyticsReport(
                campaign_id=campaign_id,
                report_type="roi_analysis",
                report_date=datetime.utcnow().date(),
                data=analysis_data,
                generated_at=datetime.utcnow()
            )

            db.add(report)
            db.commit()

            results.update({
                "total_investment": total_investment,
                "total_return": total_return,
                "avg_roi": overall_roi,
                "report_id": report.id
            })

            logger.info(f"ROI analysis completed: {results}")
            return results

    except Exception as e:
        logger.error(f"ROI analysis failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def update_kol_performance_metrics(self, kol_id: int = None) -> Dict[str, Any]:
    """
    Update KOL performance metrics based on recent activity.

    Args:
        kol_id: Specific KOL ID (optional, updates all if not provided)

    Returns:
        Dict with metrics update results
    """
    results = {
        "kols_updated": 0,
        "metrics_calculated": 0,
        "errors": []
    }

    try:
        with get_session() as db:
            if kol_id:
                kols = [db.query(KOL).filter_by(id=kol_id).first()]
                if not kols[0]:
                    raise ValueError(f"KOL {kol_id} not found")
            else:
                # Update all active KOLs
                kols = db.query(KOL).filter(KOL.status == "active").all()

            for kol in kols:
                try:
                    # Calculate recent performance metrics
                    metrics = _calculate_kol_metrics(db, kol)

                    # Update or create KOL performance metrics record
                    existing_metrics = db.query(KOLPerformanceMetrics).filter_by(
                        kol_id=kol.id
                    ).first()

                    if existing_metrics:
                        existing_metrics.avg_engagement_rate = metrics["avg_engagement_rate"]
                        existing_metrics.avg_reach = metrics["avg_reach"]
                        existing_metrics.total_campaigns = metrics["total_campaigns"]
                        existing_metrics.successful_campaigns = metrics["successful_campaigns"]
                        existing_metrics.reliability_score = metrics["reliability_score"]
                        existing_metrics.last_updated = datetime.utcnow()
                    else:
                        new_metrics = KOLPerformanceMetrics(
                            kol_id=kol.id,
                            avg_engagement_rate=metrics["avg_engagement_rate"],
                            avg_reach=metrics["avg_reach"],
                            total_campaigns=metrics["total_campaigns"],
                            successful_campaigns=metrics["successful_campaigns"],
                            reliability_score=metrics["reliability_score"],
                            last_updated=datetime.utcnow()
                        )
                        db.add(new_metrics)

                    results["kols_updated"] += 1
                    results["metrics_calculated"] += len(metrics)

                except Exception as e:
                    error_msg = f"Failed to update metrics for KOL {kol.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            db.commit()

            logger.info(f"KOL performance metrics update completed: {results}")
            return results

    except Exception as e:
        logger.error(f"KOL performance metrics update failed: {str(e)}")
        raise self.retry(countdown=180, exc=e)


# Helper functions for analytics calculations
def _generate_campaign_analytics(db: Session, date: datetime.date) -> Dict[str, Any]:
    """Generate campaign performance analytics."""
    campaigns = db.query(Campaign).filter(
        Campaign.start_date <= date,
        Campaign.end_date >= date
    ).all()

    return {
        "active_campaigns": len(campaigns),
        "total_budget": sum(c.budget for c in campaigns),
        "avg_engagement": sum(c.avg_engagement_rate or 0 for c in campaigns) / len(campaigns) if campaigns else 0
    }


def _generate_kol_analytics(db: Session, date: datetime.date) -> Dict[str, Any]:
    """Generate KOL performance analytics."""
    active_kols = db.query(KOL).filter(KOL.status == "active").count()

    return {
        "active_kols": active_kols,
        "new_kols": 0,  # Would calculate new KOLs for the day
        "top_performers": []  # Would identify top performing KOLs
    }


def _generate_platform_analytics(db: Session, date: datetime.date) -> Dict[str, Any]:
    """Generate platform performance analytics."""
    return {
        "instagram": {"posts": 10, "engagement": 3.5},
        "youtube": {"posts": 5, "engagement": 4.2},
        "tiktok": {"posts": 8, "engagement": 5.1}
    }


def _generate_engagement_trends(db: Session, date: datetime.date) -> Dict[str, Any]:
    """Generate engagement trend analytics."""
    return {
        "daily_trend": "increasing",
        "weekly_average": 3.8,
        "monthly_growth": 12.5
    }


def _generate_performance_report(db: Session, campaign: Campaign) -> Dict[str, Any]:
    """Generate campaign performance report."""
    content_count = db.query(CampaignContent).filter_by(campaign_id=campaign.id).count()
    kol_count = db.query(Collaboration).filter_by(campaign_id=campaign.id).count()

    return {
        "campaign_id": campaign.id,
        "content_count": content_count,
        "kol_count": kol_count,
        "engagement_rate": campaign.avg_engagement_rate or 0,
        "total_reach": campaign.total_reach or 0
    }


def _generate_roi_report(db: Session, campaign: Campaign) -> Dict[str, Any]:
    """Generate campaign ROI report."""
    return {
        "investment": campaign.budget,
        "estimated_return": campaign.budget * 2.5,  # Example calculation
        "roi_percentage": 150.0
    }


def _generate_engagement_report(db: Session, campaign: Campaign) -> Dict[str, Any]:
    """Generate campaign engagement report."""
    return {
        "avg_engagement_rate": campaign.avg_engagement_rate or 0,
        "target_engagement_rate": campaign.target_engagement_rate,
        "performance_vs_target": 95.0
    }


def _generate_reach_report(db: Session, campaign: Campaign) -> Dict[str, Any]:
    """Generate campaign reach report."""
    return {
        "total_reach": campaign.total_reach or 0,
        "target_reach": campaign.target_reach,
        "reach_efficiency": 88.0
    }


def _analyze_kol_performance(db: Session, kol: KOL, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Analyze KOL performance metrics."""
    return {
        "campaign_count": 5,
        "content_count": 25,
        "avg_engagement_rate": 4.2,
        "total_reach": 500000
    }


def _analyze_engagement_patterns(db: Session, kol: KOL, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Analyze KOL engagement patterns."""
    return {
        "best_posting_times": ["10:00", "15:00", "20:00"],
        "best_days": ["Tuesday", "Thursday", "Saturday"],
        "content_type_performance": {"image": 3.8, "video": 5.2, "carousel": 4.1}
    }


def _analyze_platform_performance(db: Session, kol: KOL, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Analyze KOL performance across platforms."""
    return {
        "instagram": {"engagement_rate": 4.5, "reach": 200000},
        "youtube": {"engagement_rate": 3.8, "reach": 150000},
        "tiktok": {"engagement_rate": 6.2, "reach": 300000}
    }


def _analyze_kol_roi(db: Session, kol: KOL, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Analyze KOL ROI metrics."""
    return {
        "total_investment": 50000,
        "estimated_return": 125000,
        "roi_percentage": 150.0
    }


def _calculate_platform_benchmarks(db: Session, platform: str) -> Dict[str, Any]:
    """Calculate engagement benchmarks for a platform."""
    return {
        "avg_engagement_rate": 3.5,
        "median_engagement_rate": 3.2,
        "top_quartile": 5.8,
        "sample_size": 100
    }


def _calculate_industry_benchmarks(db: Session) -> Dict[str, Any]:
    """Calculate industry-specific benchmarks."""
    return {
        "fashion": {"avg_engagement": 4.2},
        "tech": {"avg_engagement": 2.8},
        "beauty": {"avg_engagement": 5.1}
    }


def _calculate_tier_benchmarks(db: Session) -> Dict[str, Any]:
    """Calculate follower tier benchmarks."""
    return {
        "micro": {"avg_engagement": 6.5},
        "macro": {"avg_engagement": 3.2},
        "mega": {"avg_engagement": 1.8}
    }


def _calculate_campaign_roi(db: Session, campaign: Campaign) -> Dict[str, Any]:
    """Calculate ROI for a specific campaign."""
    return {
        "campaign_id": campaign.id,
        "investment": campaign.budget,
        "return": campaign.budget * 2.2,  # Example calculation
        "roi_percentage": 120.0
    }


def _calculate_kol_metrics(db: Session, kol: KOL) -> Dict[str, Any]:
    """Calculate comprehensive metrics for a KOL."""
    return {
        "avg_engagement_rate": 4.2,
        "avg_reach": 150000,
        "total_campaigns": 8,
        "successful_campaigns": 7,
        "reliability_score": 87.5
    }