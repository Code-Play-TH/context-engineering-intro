"""
Content Monitoring Database Models

SQLAlchemy models for AI-powered content monitoring and analysis functionality.
Supports content analysis, brand safety, compliance checking, and performance prediction.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContentAnalysis(Base):
    """
    Content analysis model for storing AI-powered content analysis results.
    """
    __tablename__ = "content_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # Content identification
    content_url = Column(String(500), nullable=True, index=True)
    content_text = Column(Text, nullable=True)
    media_urls = Column(JSON, default=list)  # List of media file URLs
    platform = Column(String(50), nullable=False, index=True)

    # Relationships
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    kol_id = Column(Integer, ForeignKey("kols.id"), nullable=True, index=True)

    # Analysis configuration
    analysis_types = Column(JSON, default=list)  # Types of analysis performed

    # AI Analysis Results - Sentiment and Emotion
    sentiment_score = Column(Float, nullable=True)  # -1 to 1 scale
    sentiment_label = Column(String(20), nullable=True, index=True)  # positive, negative, neutral, mixed
    emotion_scores = Column(JSON, default=dict)  # Emotion detection scores

    # Content Understanding
    topics = Column(JSON, default=list)           # Detected topics/themes
    entities = Column(JSON, default=list)         # Named entities (people, places, brands)
    hashtags_detected = Column(JSON, default=list)  # Hashtags found in content
    mentions_detected = Column(JSON, default=list)  # @mentions found in content

    # Content Classification
    content_categories = Column(JSON, default=list)  # Content categories
    content_type_detected = Column(String(50), nullable=True)  # post, story, video, etc.
    language_detected = Column(String(10), nullable=True)      # ISO language code

    # Quality Assessment
    quality_score = Column(Float, nullable=True)           # 0 to 1 scale
    engagement_prediction = Column(Float, nullable=True)   # Predicted engagement rate
    virality_score = Column(Float, nullable=True)          # Virality potential 0-1

    # Brand Safety Analysis
    brand_safety_score = Column(Float, nullable=True)  # 0 to 1 scale (1 = safe)
    safety_flags = Column(JSON, default=list)          # List of safety concerns

    # Compliance Analysis
    compliance_score = Column(Float, nullable=True)    # 0 to 1 scale
    compliance_issues = Column(JSON, default=list)     # List of compliance violations

    # Technical Metadata
    ai_confidence = Column(Float, nullable=True)       # Overall AI confidence 0-1
    processing_time = Column(Float, nullable=True)     # Processing time in seconds
    analysis_version = Column(String(20), nullable=True)  # Model version used

    # Status and workflow
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    manual_review_required = Column(Boolean, default=False)
    manual_review_completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Timestamps and tracking
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="content_analyses")
    kol = relationship("KOL", back_populates="content_analyses")
    flags = relationship("ContentFlag", back_populates="content_analysis", cascade="all, delete-orphan")
    brand_safety_reports = relationship("BrandSafetyReport", back_populates="content_analysis", cascade="all, delete-orphan")
    performance_predictions = relationship("PerformancePrediction", back_populates="content_analysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ContentAnalysis(id={self.id}, platform='{self.platform}', status='{self.status}')>"


class ContentFlag(Base):
    """
    Content flag model for tracking content violations and concerns.
    """
    __tablename__ = "content_flags"

    id = Column(Integer, primary_key=True, index=True)

    # Relationship to content analysis
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=False, index=True)

    # Flag details
    flag_type = Column(String(50), nullable=False, index=True)  # brand_safety, compliance, quality, etc.
    severity = Column(String(20), nullable=False, index=True)   # low, medium, high, critical
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # AI confidence in flag 0-1

    # Flag source and processing
    auto_generated = Column(Boolean, default=True)  # Was this flag auto-generated?
    detection_model = Column(String(50), nullable=True)  # Model that detected the issue

    # Status and resolution
    status = Column(String(20), default="pending", index=True)  # pending, reviewed, resolved, dismissed
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)

    # Escalation
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime, nullable=True)
    escalated_to = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    content_analysis = relationship("ContentAnalysis", back_populates="flags")

    def __repr__(self):
        return f"<ContentFlag(id={self.id}, type='{self.flag_type}', severity='{self.severity}')>"


class ComplianceCheck(Base):
    """
    Compliance check model for storing compliance analysis results.
    """
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)

    # Scope of compliance check
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=True, index=True)

    # Compliance results
    overall_score = Column(Float, nullable=False)  # 0 to 1 scale
    compliance_rules_checked = Column(JSON, default=list)  # Rules that were evaluated
    compliance_issues = Column(JSON, default=list)         # Detailed issues found
    recommendations = Column(JSON, default=list)           # Recommendations for improvement

    # Check configuration
    compliance_framework = Column(String(50), nullable=True)  # GDPR, COPPA, FTC, etc.
    region = Column(String(10), nullable=True)               # Geographic region for rules
    industry_standards = Column(JSON, default=list)          # Industry-specific standards

    # Processing details
    check_date = Column(DateTime, default=func.now(), nullable=False)
    processing_time = Column(Float, nullable=True)
    model_version = Column(String(20), nullable=True)

    # Status
    status = Column(String(20), default="completed", index=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="compliance_checks")
    content_analysis = relationship("ContentAnalysis")

    def __repr__(self):
        return f"<ComplianceCheck(id={self.id}, score={self.overall_score:.2f})>"


class PerformancePrediction(Base):
    """
    Performance prediction model for storing AI-powered engagement predictions.
    """
    __tablename__ = "performance_predictions"

    id = Column(Integer, primary_key=True, index=True)

    # Content identification
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    kol_id = Column(Integer, ForeignKey("kols.id"), nullable=True, index=True)
    platform = Column(String(50), nullable=False, index=True)

    # Performance predictions
    predicted_engagement = Column(Float, nullable=True)    # Predicted engagement rate
    predicted_reach = Column(Integer, nullable=True)       # Predicted reach
    predicted_impressions = Column(Integer, nullable=True) # Predicted impressions
    predicted_likes = Column(Integer, nullable=True)       # Predicted likes
    predicted_comments = Column(Integer, nullable=True)    # Predicted comments
    predicted_shares = Column(Integer, nullable=True)      # Predicted shares
    virality_probability = Column(Float, nullable=True)    # Probability of going viral

    # Optimization suggestions
    optimal_posting_time = Column(DateTime, nullable=True)
    optimal_hashtags = Column(JSON, default=list)
    hashtag_effectiveness = Column(JSON, default=dict)     # Hashtag -> effectiveness score
    content_optimization_suggestions = Column(JSON, default=list)

    # Confidence and model info
    confidence = Column(Float, nullable=True)      # Prediction confidence 0-1
    model_name = Column(String(50), nullable=True)
    model_version = Column(String(20), nullable=True)

    # Actual performance (for model training)
    actual_engagement = Column(Float, nullable=True)
    actual_reach = Column(Integer, nullable=True)
    actual_impressions = Column(Integer, nullable=True)
    actual_likes = Column(Integer, nullable=True)
    actual_comments = Column(Integer, nullable=True)
    actual_shares = Column(Integer, nullable=True)
    performance_measured_at = Column(DateTime, nullable=True)

    # Prediction accuracy
    prediction_accuracy = Column(Float, nullable=True)     # How accurate was the prediction

    # Timestamps
    prediction_date = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    content_analysis = relationship("ContentAnalysis", back_populates="performance_predictions")
    campaign = relationship("Campaign", back_populates="performance_predictions")
    kol = relationship("KOL", back_populates="performance_predictions")

    def __repr__(self):
        return f"<PerformancePrediction(id={self.id}, platform='{self.platform}', engagement={self.predicted_engagement})>"


class BrandSafetyReport(Base):
    """
    Brand safety report model for detailed brand safety analysis.
    """
    __tablename__ = "brand_safety_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Content reference
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=False, index=True)

    # Overall assessment
    overall_score = Column(Float, nullable=False)  # 0 to 1 scale (1 = completely safe)

    # Risk categories with scores
    risk_categories = Column(JSON, default=dict)  # Category -> risk score mapping
    # Common categories: violence, hate_speech, adult_content, drugs, gambling, etc.

    # Detailed findings
    detected_risks = Column(JSON, default=list)    # List of specific risks found
    risk_keywords = Column(JSON, default=list)     # Keywords that triggered flags
    context_analysis = Column(JSON, default=dict)  # Contextual risk assessment

    # Recommendations
    recommendations = Column(JSON, default=list)   # Specific recommendations for improvement
    mitigation_strategies = Column(JSON, default=list)  # Ways to reduce risk

    # Analysis details
    confidence = Column(Float, nullable=True)      # Overall confidence in analysis
    analysis_method = Column(String(50), nullable=True)  # Text, image, video, etc.
    analysis_version = Column(String(20), nullable=True)

    # Geographic considerations
    region_specific_risks = Column(JSON, default=dict)  # Risks specific to regions
    cultural_sensitivity_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    content_analysis = relationship("ContentAnalysis", back_populates="brand_safety_reports")

    def __repr__(self):
        return f"<BrandSafetyReport(id={self.id}, score={self.overall_score:.2f})>"


class ContentModeration(Base):
    """
    Content moderation model for tracking moderation decisions and actions.
    """
    __tablename__ = "content_moderations"

    id = Column(Integer, primary_key=True, index=True)

    # Content reference
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=False, index=True)

    # Moderation decision
    moderation_action = Column(String(20), nullable=False, index=True)  # approve, reject, flag, etc.
    reason = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)  # Confidence in moderation decision

    # Automation vs manual
    automated = Column(Boolean, default=True)
    model_used = Column(String(50), nullable=True)
    human_reviewer_id = Column(Integer, nullable=True)

    # Review process
    reviewed_by = Column(Integer, nullable=True)    # Human reviewer
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Appeal process
    appealed = Column(Boolean, default=False)
    appeal_reason = Column(Text, nullable=True)
    appeal_date = Column(DateTime, nullable=True)
    appeal_resolved = Column(Boolean, default=False)
    appeal_resolution = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    content_analysis = relationship("ContentAnalysis")

    def __repr__(self):
        return f"<ContentModeration(id={self.id}, action='{self.moderation_action}')>"


class AIModelMetrics(Base):
    """
    AI model metrics for tracking model performance and accuracy.
    """
    __tablename__ = "ai_model_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Model identification
    model_name = Column(String(50), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)  # sentiment, safety, engagement, etc.

    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_score = Column(Float, nullable=True)

    # Usage statistics
    predictions_made = Column(Integer, default=0)
    successful_predictions = Column(Integer, default=0)
    failed_predictions = Column(Integer, default=0)

    # Performance over time
    avg_processing_time = Column(Float, nullable=True)  # Average processing time in seconds
    avg_confidence_score = Column(Float, nullable=True)

    # Evaluation period
    evaluation_start_date = Column(DateTime, nullable=True)
    evaluation_end_date = Column(DateTime, nullable=True)
    evaluation_dataset_size = Column(Integer, nullable=True)

    # Model configuration
    hyperparameters = Column(JSON, default=dict)
    training_data_info = Column(JSON, default=dict)

    # Status
    is_active = Column(Boolean, default=True)
    deployment_date = Column(DateTime, nullable=True)
    retirement_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AIModelMetrics(id={self.id}, model='{self.model_name}', version='{self.model_version}')>"


class ContentMonitoringAlert(Base):
    """
    Content monitoring alert model for real-time alerting system.
    """
    __tablename__ = "content_monitoring_alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Alert identification
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)

    # Content reference
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)

    # Alert details
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Alert rules and triggers
    triggered_by_rule = Column(String(100), nullable=True)
    trigger_conditions = Column(JSON, default=dict)
    trigger_values = Column(JSON, default=dict)

    # Notification status
    notifications_sent = Column(JSON, default=list)  # List of notification channels used
    notification_status = Column(JSON, default=dict)  # Status per channel

    # Alert lifecycle
    status = Column(String(20), default="active", index=True)  # active, acknowledged, resolved, dismissed
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)  # Auto-dismiss after this time

    # Relationships
    content_analysis = relationship("ContentAnalysis")
    campaign = relationship("Campaign")

    def __repr__(self):
        return f"<ContentMonitoringAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}')>"


class ContentOptimizationSuggestion(Base):
    """
    Content optimization suggestion model for AI-powered content improvement recommendations.
    """
    __tablename__ = "content_optimization_suggestions"

    id = Column(Integer, primary_key=True, index=True)

    # Content reference
    content_analysis_id = Column(Integer, ForeignKey("content_analyses.id"), nullable=False, index=True)

    # Suggestion details
    suggestion_type = Column(String(50), nullable=False, index=True)  # hashtags, timing, content_type, etc.
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    # Impact assessment
    impact_score = Column(Float, nullable=True)  # Expected impact on performance 0-1
    confidence = Column(Float, nullable=True)    # AI confidence in suggestion 0-1
    implementation_difficulty = Column(String(20), nullable=True)  # easy, medium, hard

    # Specific recommendations
    current_value = Column(Text, nullable=True)    # Current state
    suggested_value = Column(Text, nullable=True)  # Suggested improvement
    expected_improvement = Column(Float, nullable=True)  # Expected % improvement

    # Suggestion metadata
    model_used = Column(String(50), nullable=True)
    based_on_data = Column(JSON, default=dict)  # Data sources used for suggestion

    # User interaction
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    applied_by = Column(Integer, nullable=True)
    effectiveness_rating = Column(Float, nullable=True)  # User rating of suggestion

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Suggestion becomes stale after this

    # Relationships
    content_analysis = relationship("ContentAnalysis")

    def __repr__(self):
        return f"<ContentOptimizationSuggestion(id={self.id}, type='{self.suggestion_type}')>"