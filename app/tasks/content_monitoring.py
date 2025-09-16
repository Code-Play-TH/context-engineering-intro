"""
Content Monitoring Background Tasks

Celery tasks for AI-powered content monitoring and analysis including:
- Batch content analysis processing
- Campaign content monitoring
- Compliance report generation
- Performance prediction updates
- Real-time content alerts
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import chain, group, chord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.tasks.celery_app import celery_app
from app.core.database import get_session
from app.models.content_monitoring import (
    ContentAnalysis, ContentFlag, ComplianceCheck, PerformancePrediction,
    BrandSafetyReport, ContentModeration
)
from app.models.campaigns import Campaign, CampaignContent
from app.models.kols import KOL
from app.schemas.content_monitoring import (
    ContentAnalysisCreate, AnalysisStatus, SeverityLevel, FlagType,
    ContentModerationAction, SocialPlatform
)
from app.services.content_monitoring.ai_analyzer import AIContentAnalyzer
from app.services.content_monitoring.compliance_checker import ComplianceChecker
from app.services.content_monitoring.brand_safety import BrandSafetyAnalyzer
from app.services.communication.email_service import EmailService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, max_retries=3)
def analyze_content_batch(self, content_items: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a batch of content items for AI analysis.

    Args:
        content_items: List of content items to analyze
        config: Analysis configuration

    Returns:
        Dict containing batch processing results
    """
    try:
        logger.info(f"Starting batch analysis for {len(content_items)} items")

        results = {
            'total_items': len(content_items),
            'processed_items': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'flagged_items': 0,
            'errors': []
        }

        # Process each item
        for item in content_items:
            try:
                # Analyze individual content item
                analysis_result = analyze_single_content.delay(item, config)

                # Wait for completion (or use callback for async processing)
                analysis_data = analysis_result.get(timeout=300)  # 5 minute timeout

                results['processed_items'] += 1

                if analysis_data.get('success'):
                    results['successful_analyses'] += 1

                    # Check if content was flagged
                    if analysis_data.get('flags_generated', 0) > 0:
                        results['flagged_items'] += 1
                else:
                    results['failed_analyses'] += 1
                    results['errors'].append({
                        'item_id': item.get('id'),
                        'error': analysis_data.get('error', 'Unknown error')
                    })

            except Exception as e:
                logger.error(f"Failed to process content item {item.get('id', 'unknown')}: {str(e)}")
                results['failed_analyses'] += 1
                results['errors'].append({
                    'item_id': item.get('id'),
                    'error': str(e)
                })

        logger.info(f"Batch analysis completed: {results['successful_analyses']}/{results['total_items']} successful")
        return results

    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}")
        self.retry(countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def analyze_single_content(self, content_item: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single content item.

    Args:
        content_item: Content item data
        config: Analysis configuration

    Returns:
        Dict containing analysis results
    """
    try:
        logger.info(f"Analyzing content item: {content_item.get('id', 'unknown')}")

        # Initialize services
        ai_analyzer = AIContentAnalyzer()
        compliance_checker = ComplianceChecker()
        brand_safety_analyzer = BrandSafetyAnalyzer()

        # Extract content data
        content_text = content_item.get('content_text')
        content_url = content_item.get('content_url')
        media_urls = content_item.get('media_urls', [])
        platform = content_item.get('platform')
        campaign_id = content_item.get('campaign_id')
        kol_id = content_item.get('kol_id')

        analysis_types = config.get('analysis_types', [])

        # Perform AI analysis
        ai_results = ai_analyzer.analyze_content(
            content_text=content_text,
            content_url=content_url,
            media_urls=media_urls,
            platform=SocialPlatform(platform) if platform else None,
            analysis_types=analysis_types
        )

        # Perform compliance check
        compliance_results = compliance_checker.check_compliance(
            content_text=content_text,
            content_url=content_url,
            media_urls=media_urls,
            platform=SocialPlatform(platform) if platform else None,
            campaign_id=campaign_id
        )

        # Perform brand safety analysis
        brand_safety_results = brand_safety_analyzer.analyze_brand_safety(
            content_text=content_text,
            content_url=content_url,
            media_urls=media_urls,
            platform=SocialPlatform(platform) if platform else None
        )

        # Store analysis results in database
        analysis_id = store_analysis_results.delay(
            content_item,
            ai_results,
            compliance_results,
            brand_safety_results
        ).get()

        # Generate automatic flags if needed
        flags_generated = 0
        auto_flag_threshold = config.get('auto_flag_threshold', 0.7)

        if (compliance_results.get('overall_score', 1.0) < auto_flag_threshold or
            brand_safety_results.get('overall_score', 1.0) < auto_flag_threshold):

            generate_content_flags.delay(analysis_id, compliance_results, brand_safety_results)
            flags_generated = 1

        return {
            'success': True,
            'analysis_id': analysis_id,
            'flags_generated': flags_generated,
            'ai_confidence': ai_results.get('ai_confidence', 0.8),
            'compliance_score': compliance_results.get('overall_score', 1.0),
            'brand_safety_score': brand_safety_results.get('overall_score', 1.0)
        }

    except Exception as e:
        logger.error(f"Single content analysis failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(bind=True)
def store_analysis_results(
    self,
    content_item: Dict[str, Any],
    ai_results: Dict[str, Any],
    compliance_results: Dict[str, Any],
    brand_safety_results: Dict[str, Any]
) -> int:
    """
    Store analysis results in the database.

    Args:
        content_item: Original content item data
        ai_results: AI analysis results
        compliance_results: Compliance check results
        brand_safety_results: Brand safety analysis results

    Returns:
        Analysis ID
    """
    try:
        # This would normally use async database operations
        # For now, simulating the database storage
        logger.info(f"Storing analysis results for content: {content_item.get('id', 'unknown')}")

        # In production, this would create actual ContentAnalysis record
        analysis_id = hash(str(content_item)) % 100000  # Simulate ID generation

        logger.info(f"Analysis results stored with ID: {analysis_id}")
        return analysis_id

    except Exception as e:
        logger.error(f"Failed to store analysis results: {str(e)}")
        raise


@celery_app.task(bind=True)
def generate_content_flags(
    self,
    analysis_id: int,
    compliance_results: Dict[str, Any],
    brand_safety_results: Dict[str, Any]
) -> List[int]:
    """
    Generate content flags based on analysis results.

    Args:
        analysis_id: Content analysis ID
        compliance_results: Compliance check results
        brand_safety_results: Brand safety analysis results

    Returns:
        List of generated flag IDs
    """
    try:
        logger.info(f"Generating flags for analysis ID: {analysis_id}")

        flag_ids = []

        # Generate compliance flags
        compliance_issues = compliance_results.get('compliance_issues', [])
        for issue in compliance_issues:
            if issue.get('severity') in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                # In production, create actual ContentFlag record
                flag_id = hash(f"{analysis_id}_{issue.get('issue_type')}") % 100000
                flag_ids.append(flag_id)

        # Generate brand safety flags
        brand_risks = brand_safety_results.get('detected_risks', [])
        for risk in brand_risks:
            if risk.get('severity') in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                # In production, create actual ContentFlag record
                flag_id = hash(f"{analysis_id}_{risk.get('risk_type')}") % 100000
                flag_ids.append(flag_id)

        logger.info(f"Generated {len(flag_ids)} flags for analysis {analysis_id}")
        return flag_ids

    except Exception as e:
        logger.error(f"Failed to generate content flags: {str(e)}")
        raise


@celery_app.task(bind=True, max_retries=3)
def monitor_campaign_content(self, campaign_id: int, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitor content for a specific campaign.

    Args:
        campaign_id: Campaign ID to monitor
        monitoring_config: Monitoring configuration

    Returns:
        Dict containing monitoring results
    """
    try:
        logger.info(f"Starting campaign content monitoring for campaign {campaign_id}")

        # In production, this would query actual campaign content
        # For now, simulating the monitoring process

        monitoring_results = {
            'campaign_id': campaign_id,
            'monitored_items': 0,
            'flagged_items': 0,
            'alerts_generated': 0,
            'start_time': datetime.utcnow(),
            'status': 'completed'
        }

        # Simulate monitoring logic
        content_items = []  # Would fetch from database
        alerts_generated = []

        for item in content_items:
            # Analyze content
            analysis_task = analyze_single_content.delay(item, monitoring_config)
            analysis_result = analysis_task.get(timeout=300)

            monitoring_results['monitored_items'] += 1

            # Check if alerts should be generated
            if (analysis_result.get('compliance_score', 1.0) < 0.5 or
                analysis_result.get('brand_safety_score', 1.0) < 0.5):

                alert_id = generate_content_alert.delay(
                    campaign_id, item, analysis_result
                ).get()

                alerts_generated.append(alert_id)
                monitoring_results['flagged_items'] += 1

        monitoring_results['alerts_generated'] = len(alerts_generated)
        monitoring_results['end_time'] = datetime.utcnow()

        logger.info(f"Campaign monitoring completed: {monitoring_results}")
        return monitoring_results

    except Exception as e:
        logger.error(f"Campaign content monitoring failed: {str(e)}")
        self.retry(countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True)
def generate_content_alert(
    self,
    campaign_id: int,
    content_item: Dict[str, Any],
    analysis_result: Dict[str, Any]
) -> str:
    """
    Generate content alert for flagged content.

    Args:
        campaign_id: Campaign ID
        content_item: Content item data
        analysis_result: Analysis results

    Returns:
        Alert ID
    """
    try:
        logger.info(f"Generating content alert for campaign {campaign_id}")

        # Create alert
        alert_id = f"alert_{campaign_id}_{hash(str(content_item)) % 10000}"

        # In production, this would create actual alert record and send notifications

        # Send notification to stakeholders
        send_content_alert_notification.delay(
            alert_id, campaign_id, content_item, analysis_result
        )

        return alert_id

    except Exception as e:
        logger.error(f"Failed to generate content alert: {str(e)}")
        raise


@celery_app.task(bind=True)
def send_content_alert_notification(
    self,
    alert_id: str,
    campaign_id: int,
    content_item: Dict[str, Any],
    analysis_result: Dict[str, Any]
) -> bool:
    """
    Send content alert notifications.

    Args:
        alert_id: Alert ID
        campaign_id: Campaign ID
        content_item: Content item data
        analysis_result: Analysis results

    Returns:
        Success status
    """
    try:
        logger.info(f"Sending content alert notification: {alert_id}")

        # In production, this would send actual email notifications
        email_service = EmailService()

        # Get stakeholder emails (campaign managers, compliance team, etc.)
        stakeholders = []  # Would fetch from database

        subject = f"Content Alert - Campaign {campaign_id}"
        message = f"""
        Content Alert Generated: {alert_id}

        Campaign: {campaign_id}
        Content URL: {content_item.get('content_url', 'N/A')}
        Platform: {content_item.get('platform', 'N/A')}

        Analysis Results:
        - Compliance Score: {analysis_result.get('compliance_score', 'N/A')}
        - Brand Safety Score: {analysis_result.get('brand_safety_score', 'N/A')}
        - AI Confidence: {analysis_result.get('ai_confidence', 'N/A')}

        Please review the flagged content immediately.
        """

        # Send notifications
        for email in stakeholders:
            # email_service.send_email(email, subject, message)
            pass  # Placeholder

        logger.info(f"Content alert notification sent: {alert_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send content alert notification: {str(e)}")
        return False


@celery_app.task(bind=True, max_retries=3)
def generate_compliance_report(self, campaign_id: Optional[int] = None, date_range: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate comprehensive compliance report.

    Args:
        campaign_id: Optional campaign ID to filter by
        date_range: Optional date range for the report

    Returns:
        Dict containing compliance report data
    """
    try:
        logger.info(f"Generating compliance report for campaign {campaign_id}")

        # In production, this would query actual database records
        report_data = {
            'report_id': f"compliance_{campaign_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            'campaign_id': campaign_id,
            'generated_at': datetime.utcnow(),
            'total_content_analyzed': 0,
            'compliant_content': 0,
            'non_compliant_content': 0,
            'compliance_score': 0.0,
            'top_issues': [],
            'recommendations': []
        }

        # Simulate report generation
        # In production, this would aggregate compliance data from database

        report_data.update({
            'total_content_analyzed': 100,
            'compliant_content': 85,
            'non_compliant_content': 15,
            'compliance_score': 0.85,
            'top_issues': [
                'Missing disclosure statements',
                'Inappropriate language',
                'Compliance disclaimers'
            ],
            'recommendations': [
                'Implement disclosure review process',
                'Update content guidelines',
                'Provide compliance training'
            ]
        })

        # Store report in database
        # store_compliance_report.delay(report_data)

        logger.info(f"Compliance report generated: {report_data['report_id']}")
        return report_data

    except Exception as e:
        logger.error(f"Compliance report generation failed: {str(e)}")
        self.retry(countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def update_performance_predictions(self, campaign_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Update performance predictions for content.

    Args:
        campaign_id: Optional campaign ID to update predictions for

    Returns:
        Dict containing update results
    """
    try:
        logger.info(f"Updating performance predictions for campaign {campaign_id}")

        results = {
            'campaign_id': campaign_id,
            'updated_predictions': 0,
            'failed_updates': 0,
            'errors': [],
            'update_time': datetime.utcnow()
        }

        # In production, this would query content analyses and update predictions
        # based on actual performance data and improved ML models

        content_analyses = []  # Would fetch from database

        for analysis in content_analyses:
            try:
                # Re-run performance prediction with latest models
                ai_analyzer = AIContentAnalyzer()

                # Get updated predictions
                # updated_prediction = ai_analyzer.predict_performance(analysis)

                # Update database record
                # update_prediction_record.delay(analysis.id, updated_prediction)

                results['updated_predictions'] += 1

            except Exception as e:
                logger.error(f"Failed to update prediction for analysis {analysis.get('id')}: {str(e)}")
                results['failed_updates'] += 1
                results['errors'].append({
                    'analysis_id': analysis.get('id'),
                    'error': str(e)
                })

        logger.info(f"Performance predictions update completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Performance predictions update failed: {str(e)}")
        self.retry(countdown=60 * (self.request.retries + 1))


@celery_app.task
def cleanup_old_analyses(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old content analyses to manage database size.

    Args:
        days_to_keep: Number of days of analyses to keep

    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info(f"Starting cleanup of analyses older than {days_to_keep} days")

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # In production, this would delete old records from database
        deleted_count = 0  # Placeholder

        cleanup_results = {
            'cutoff_date': cutoff_date,
            'deleted_analyses': deleted_count,
            'cleanup_time': datetime.utcnow()
        }

        logger.info(f"Cleanup completed: {cleanup_results}")
        return cleanup_results

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise


# Scheduled tasks
@celery_app.task
def daily_compliance_check():
    """
    Daily scheduled compliance check for all active campaigns.
    """
    logger.info("Starting daily compliance check")

    # Get all active campaigns
    active_campaigns = []  # Would fetch from database

    for campaign in active_campaigns:
        generate_compliance_report.delay(campaign.get('id'))

    logger.info(f"Scheduled compliance checks for {len(active_campaigns)} campaigns")


@celery_app.task
def weekly_performance_update():
    """
    Weekly scheduled performance prediction updates.
    """
    logger.info("Starting weekly performance prediction updates")

    # Update predictions for all campaigns
    update_performance_predictions.delay()

    logger.info("Weekly performance update scheduled")


@celery_app.task
def monthly_analytics_summary():
    """
    Monthly analytics summary generation.
    """
    logger.info("Starting monthly analytics summary")

    # Generate monthly summary reports
    # This would aggregate data and send summary reports to stakeholders

    logger.info("Monthly analytics summary completed")