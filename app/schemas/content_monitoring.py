"""
Content Monitoring Pydantic Schemas

Provides validation schemas for AI-powered content monitoring operations including:
- Content analysis and classification
- Brand safety and compliance checking
- Performance prediction and optimization
- Content moderation and flagging
- AI model predictions and insights
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from enum import Enum


class AnalysisType(str, Enum):
    """Content analysis type enumeration."""
    SENTIMENT = "sentiment"
    EMOTION = "emotion"
    TOPICS = "topics"
    ENTITIES = "entities"
    LANGUAGE = "language"
    QUALITY = "quality"
    BRAND_SAFETY = "brand_safety"
    COMPLIANCE = "compliance"
    ENGAGEMENT_PREDICTION = "engagement_prediction"
    VIRALITY = "virality"
    CONTENT_TYPE = "content_type"
    HASHTAG_ANALYSIS = "hashtag_analysis"
    MENTION_ANALYSIS = "mention_analysis"


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class SeverityLevel(str, Enum):
    """Severity level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FlagType(str, Enum):
    """Content flag type enumeration."""
    BRAND_SAFETY = "brand_safety"
    COMPLIANCE = "compliance"
    QUALITY = "quality"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    COPYRIGHT = "copyright"
    SPAM = "spam"
    MISINFORMATION = "misinformation"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    ADULT_CONTENT = "adult_content"


class FlagStatus(str, Enum):
    """Flag status enumeration."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class SocialPlatform(str, Enum):
    """Social media platform enumeration."""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITCH = "twitch"


class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Core Content Analysis Schemas
class ContentAnalysisBase(BaseModel):
    """Base schema for content analysis."""
    content_url: Optional[HttpUrl] = None
    content_text: Optional[str] = Field(None, max_length=10000)
    media_urls: List[str] = Field(default_factory=list)
    platform: SocialPlatform
    analysis_types: List[AnalysisType] = Field(default_factory=list)


class ContentAnalysisCreate(ContentAnalysisBase):
    """Schema for creating content analysis."""
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None


class ContentAnalysisUpdate(BaseModel):
    """Schema for updating content analysis."""
    status: Optional[AnalysisStatus] = None
    notes: Optional[str] = Field(None, max_length=2000)
    manual_review_completed: Optional[bool] = None


class ContentAnalysisResponse(ContentAnalysisBase):
    """Schema for content analysis responses."""
    id: int
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None

    # AI Analysis Results
    sentiment_score: float = Field(ge=-1, le=1, description="Sentiment score from -1 to 1")
    sentiment_label: SentimentLabel
    emotion_scores: Dict[str, float] = Field(default_factory=dict)
    topics: List[str] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    hashtags_detected: List[str] = Field(default_factory=list)
    mentions_detected: List[str] = Field(default_factory=list)

    # Content Classification
    content_categories: List[str] = Field(default_factory=list)
    content_type_detected: str
    language_detected: str

    # Quality Assessment
    quality_score: float = Field(ge=0, le=1, description="Content quality score")
    engagement_prediction: float = Field(ge=0, description="Predicted engagement rate")
    virality_score: float = Field(ge=0, le=1, description="Virality potential score")

    # Brand Safety
    brand_safety_score: float = Field(ge=0, le=1, description="Brand safety score")
    safety_flags: List[Dict[str, Any]] = Field(default_factory=list)

    # Compliance
    compliance_score: float = Field(ge=0, le=1, description="Compliance score")
    compliance_issues: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    ai_confidence: float = Field(ge=0, le=1, description="AI prediction confidence")
    processing_time: float = Field(ge=0, description="Processing time in seconds")
    analysis_version: str
    status: AnalysisStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Content Flag Schemas
class ContentFlagBase(BaseModel):
    """Base schema for content flags."""
    flag_type: FlagType
    severity: SeverityLevel
    description: str = Field(..., min_length=1, max_length=1000)


class ContentFlagCreate(ContentFlagBase):
    """Schema for creating content flags."""
    content_analysis_id: int
    confidence: float = Field(ge=0, le=1)
    auto_generated: bool = False


class ContentFlagResponse(ContentFlagBase):
    """Schema for content flag responses."""
    id: int
    content_analysis_id: int
    confidence: float
    auto_generated: bool
    status: FlagStatus
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Compliance Schemas
class ComplianceIssue(BaseModel):
    """Schema for compliance issues."""
    issue_type: str
    description: str
    severity: SeverityLevel
    recommendation: str
    confidence: float = Field(ge=0, le=1)


class ComplianceCheckResponse(BaseModel):
    """Schema for compliance check responses."""
    id: int
    campaign_id: Optional[int] = None
    overall_score: float = Field(ge=0, le=1)
    compliance_issues: List[ComplianceIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    check_date: datetime
    status: str
    task_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Performance Prediction Schemas
class PerformancePredictionResponse(BaseModel):
    """Schema for performance prediction responses."""
    id: int
    content_analysis_id: Optional[int] = None
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    platform: SocialPlatform

    # Predictions
    predicted_engagement: float = Field(ge=0, description="Predicted engagement rate")
    predicted_reach: int = Field(ge=0, description="Predicted reach")
    predicted_impressions: int = Field(ge=0, description="Predicted impressions")
    virality_probability: float = Field(ge=0, le=1, description="Probability of going viral")

    # Performance Factors
    optimal_posting_time: Optional[datetime] = None
    hashtag_effectiveness: Dict[str, float] = Field(default_factory=dict)
    content_optimization_suggestions: List[str] = Field(default_factory=list)

    # Confidence and Metadata
    confidence: float = Field(ge=0, le=1)
    model_version: str
    prediction_date: datetime

    model_config = ConfigDict(from_attributes=True)


# Brand Safety Schemas
class BrandSafetyRisk(BaseModel):
    """Schema for brand safety risks."""
    risk_type: str
    severity: SeverityLevel
    description: str
    confidence: float = Field(ge=0, le=1)
    detected_content: Optional[str] = None


class BrandSafetyReportResponse(BaseModel):
    """Schema for brand safety report responses."""
    id: int
    content_analysis_id: int
    overall_score: float = Field(ge=0, le=1, description="Overall brand safety score")
    risk_categories: Dict[str, float] = Field(default_factory=dict)
    detected_risks: List[BrandSafetyRisk] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    analysis_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Content Moderation Schemas
class ContentModerationAction(str, Enum):
    """Content moderation actions."""
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    REQUIRE_REVIEW = "require_review"
    AUTO_MODERATE = "auto_moderate"


class ContentModerationResponse(BaseModel):
    """Schema for content moderation responses."""
    id: int
    content_analysis_id: int
    moderation_action: ContentModerationAction
    reason: str
    confidence: float = Field(ge=0, le=1)
    automated: bool
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Filter and Search Schemas
class ContentMonitoringFilters(BaseModel):
    """Schema for content monitoring filters."""
    platform: Optional[List[SocialPlatform]] = None
    campaign_id: Optional[List[int]] = None
    kol_id: Optional[List[int]] = None
    sentiment: Optional[List[SentimentLabel]] = None
    status: Optional[List[AnalysisStatus]] = None
    analysis_types: Optional[List[AnalysisType]] = None
    min_quality_score: Optional[float] = Field(None, ge=0, le=1)
    max_quality_score: Optional[float] = Field(None, ge=0, le=1)
    min_brand_safety_score: Optional[float] = Field(None, ge=0, le=1)
    min_engagement_prediction: Optional[float] = Field(None, ge=0)
    has_flags: Optional[bool] = None
    flag_types: Optional[List[FlagType]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Analytics Schemas
class ContentAnalyticsRequest(BaseModel):
    """Schema for content analytics requests."""
    date_range: Dict[str, datetime]
    filters: Optional[ContentMonitoringFilters] = None
    metrics: List[str] = Field(default_factory=lambda: ["sentiment", "quality", "engagement"])
    group_by: Optional[str] = Field(None, pattern="^(platform|campaign|kol|date)$")


class ContentAnalyticsResponse(BaseModel):
    """Schema for content analytics responses."""
    total_analyses: int
    date_range: Dict[str, datetime]

    # Aggregate Metrics
    avg_sentiment_score: float
    avg_quality_score: float
    avg_brand_safety_score: float
    avg_engagement_prediction: float

    # Distributions
    sentiment_distribution: Dict[str, int]
    platform_distribution: Dict[str, int]
    flag_distribution: Dict[str, int]

    # Trends
    daily_analysis_counts: List[Dict[str, Any]]
    quality_trends: List[Dict[str, Any]]
    sentiment_trends: List[Dict[str, Any]]

    # Top Insights
    top_performing_content: List[Dict[str, Any]]
    most_flagged_content: List[Dict[str, Any]]
    recommendations: List[str]

    generated_at: datetime


# Bulk Operations Schemas
class BulkContentItem(BaseModel):
    """Schema for bulk content analysis items."""
    content_url: Optional[HttpUrl] = None
    content_text: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    platform: SocialPlatform
    campaign_id: Optional[int] = None
    kol_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkAnalysisConfig(BaseModel):
    """Schema for bulk analysis configuration."""
    analysis_types: List[AnalysisType] = Field(default_factory=list)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    notify_on_completion: bool = True
    auto_flag_threshold: float = Field(default=0.7, ge=0, le=1)


class BulkContentAnalysisRequest(BaseModel):
    """Schema for bulk content analysis requests."""
    content_items: List[BulkContentItem] = Field(..., min_length=1, max_length=100)
    analysis_config: BulkAnalysisConfig


class BulkAnalysisResponse(BaseModel):
    """Schema for bulk analysis responses."""
    task_id: str
    total_items: int
    processed_items: int
    successful_analyses: int
    failed_analyses: int
    flagged_items: int
    status: str
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    completion_percentage: float = Field(ge=0, le=100)
    estimated_completion: Optional[datetime] = None


# AI Model Schemas
class AIModelPrediction(BaseModel):
    """Schema for AI model predictions."""
    model_name: str
    model_version: str
    prediction_type: str
    confidence: float = Field(ge=0, le=1)
    prediction_value: Union[float, str, Dict[str, Any]]
    explanation: Optional[str] = None
    feature_importance: Dict[str, float] = Field(default_factory=dict)


class ModelPerformanceMetrics(BaseModel):
    """Schema for AI model performance metrics."""
    model_name: str
    model_version: str
    accuracy: float = Field(ge=0, le=1)
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    f1_score: float = Field(ge=0, le=1)
    predictions_made: int
    last_updated: datetime


# Webhook and Notification Schemas
class ContentAlertRule(BaseModel):
    """Schema for content alert rules."""
    rule_name: str = Field(..., min_length=1, max_length=100)
    conditions: Dict[str, Any]
    actions: List[str]
    is_active: bool = True
    priority: SeverityLevel = SeverityLevel.MEDIUM


class ContentAlert(BaseModel):
    """Schema for content alerts."""
    alert_id: str
    rule_name: str
    content_analysis_id: int
    severity: SeverityLevel
    message: str
    triggered_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None


# Real-time Monitoring Schemas
class MonitoringConfig(BaseModel):
    """Schema for real-time monitoring configuration."""
    platforms: List[SocialPlatform] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    sentiment_threshold: float = Field(default=0.3, ge=-1, le=1)
    quality_threshold: float = Field(default=0.5, ge=0, le=1)
    brand_safety_threshold: float = Field(default=0.7, ge=0, le=1)
    alert_on_flags: bool = True
    analysis_frequency: str = Field(default="realtime", pattern="^(realtime|hourly|daily)$")


class MonitoringStatus(BaseModel):
    """Schema for monitoring status."""
    monitoring_id: str
    campaign_id: Optional[int] = None
    status: str
    started_at: datetime
    last_check: Optional[datetime] = None
    items_monitored: int = 0
    alerts_generated: int = 0
    config: MonitoringConfig


# Content Optimization Schemas
class OptimizationSuggestion(BaseModel):
    """Schema for content optimization suggestions."""
    suggestion_type: str
    description: str
    impact_score: float = Field(ge=0, le=1, description="Expected impact on performance")
    confidence: float = Field(ge=0, le=1)
    implementation_difficulty: str = Field(pattern="^(easy|medium|hard)$")
    category: str  # hashtags, timing, content_type, etc.


class ContentOptimizationResponse(BaseModel):
    """Schema for content optimization responses."""
    content_analysis_id: int
    current_performance_prediction: float
    optimized_performance_prediction: float
    improvement_potential: float = Field(ge=0, description="Percentage improvement expected")
    suggestions: List[OptimizationSuggestion]
    priority_actions: List[str]
    generated_at: datetime


# Comparative Analysis Schemas
class ContentComparison(BaseModel):
    """Schema for content comparison analysis."""
    content_a_id: int
    content_b_id: int
    comparison_metrics: Dict[str, Dict[str, float]]
    winner: Optional[str] = None  # "content_a", "content_b", or "tie"
    insights: List[str]
    recommendations: List[str]
    confidence: float = Field(ge=0, le=1)


class BenchmarkComparison(BaseModel):
    """Schema for benchmark comparison."""
    content_analysis_id: int
    industry_benchmarks: Dict[str, float]
    performance_vs_benchmark: Dict[str, float]
    ranking_percentile: float = Field(ge=0, le=100)
    areas_of_strength: List[str]
    areas_for_improvement: List[str]