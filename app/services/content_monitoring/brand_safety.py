"""
Brand Safety Analyzer Service

Provides comprehensive brand safety assessment including:
- Content risk evaluation
- Brand reputation protection
- Inappropriate content detection
- Context analysis for brand alignment
- Risk categorization and scoring
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum

from app.schemas.content_monitoring import (
    SeverityLevel, SocialPlatform, BrandSafetyRisk
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RiskCategory(str, Enum):
    """Brand safety risk categories."""
    ADULT_CONTENT = "adult_content"
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    ILLEGAL_ACTIVITIES = "illegal_activities"
    MISINFORMATION = "misinformation"
    SPAM = "spam"
    CONTROVERSIAL_TOPICS = "controversial_topics"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    COMPETITOR_MENTIONS = "competitor_mentions"
    INAPPROPRIATE_LANGUAGE = "inappropriate_language"


class BrandSafetyAnalyzer:
    """
    Comprehensive brand safety analysis service for content risk assessment.
    """

    def __init__(self):
        """Initialize the Brand Safety Analyzer with risk patterns and configurations."""
        self._load_safety_patterns()
        self._load_brand_guidelines()

    def _load_safety_patterns(self) -> None:
        """
        Load brand safety patterns and risk indicators.
        """
        # Adult content patterns
        self.adult_content_patterns = [
            r'\b(adult|porn|xxx|explicit|nude|naked|sex|sexual)\b',
            r'\b(escort|prostitute|hooker|brothel)\b',
            r'\b(fetish|bdsm|kink|erotic)\b'
        ]

        # Violence patterns
        self.violence_patterns = [
            r'\b(kill|murder|death|violence|assault|attack|fight|war)\b',
            r'\b(gun|weapon|knife|bomb|explosive|terrorist)\b',
            r'\b(blood|gore|torture|brutal|savage)\b'
        ]

        # Hate speech patterns
        self.hate_speech_patterns = [
            r'\b(hate|racist|racism|discrimination|prejudice)\b',
            r'\b(nazi|fascist|supremacist|extremist)\b',
            r'\b(bigot|homophobe|xenophobe|islamophobe)\b'
        ]

        # Illegal activities patterns
        self.illegal_patterns = [
            r'\b(drugs|cocaine|heroin|marijuana|weed|pot|meth)\b',
            r'\b(steal|theft|robbery|fraud|scam|illegal)\b',
            r'\b(counterfeit|piracy|copyright|infringement)\b'
        ]

        # Misinformation patterns
        self.misinformation_patterns = [
            r'\b(conspiracy|hoax|fake news|misinformation|disinformation)\b',
            r'\b(covid hoax|vaccine conspiracy|flat earth)\b',
            r'\b(election fraud|stolen election|deep state)\b'
        ]

        # Spam patterns
        self.spam_patterns = [
            r'\b(get rich quick|make money fast|guaranteed income)\b',
            r'\b(free money|easy cash|work from home)\b',
            r'\b(click here|limited time|act now|urgent)\b'
        ]

        # Controversial topics patterns
        self.controversial_patterns = [
            r'\b(abortion|gun control|climate change|politics|election)\b',
            r'\b(religion|religious|islam|christianity|judaism)\b',
            r'\b(immigration|refugee|border|deportation)\b'
        ]

        # Inappropriate language patterns
        self.profanity_patterns = [
            r'\b(damn|hell|shit|fuck|bitch|ass|crap)\b',
            r'\b(stupid|idiot|moron|retard|loser)\b'
        ]

        # Competitor mention patterns (to be customized per brand)
        self.competitor_patterns = [
            r'\b(competitor|rival|alternative|vs|versus|better than)\b'
        ]

    def _load_brand_guidelines(self) -> None:
        """
        Load brand-specific safety guidelines and thresholds.
        """
        # Brand safety thresholds (configurable per brand)
        self.safety_thresholds = {
            RiskCategory.ADULT_CONTENT: 0.1,
            RiskCategory.VIOLENCE: 0.2,
            RiskCategory.HATE_SPEECH: 0.0,  # Zero tolerance
            RiskCategory.ILLEGAL_ACTIVITIES: 0.0,  # Zero tolerance
            RiskCategory.MISINFORMATION: 0.1,
            RiskCategory.SPAM: 0.3,
            RiskCategory.CONTROVERSIAL_TOPICS: 0.4,
            RiskCategory.NEGATIVE_SENTIMENT: 0.6,
            RiskCategory.COMPETITOR_MENTIONS: 0.5,
            RiskCategory.INAPPROPRIATE_LANGUAGE: 0.3
        }

        # Risk severity mapping
        self.risk_severity_mapping = {
            (0.0, 0.2): SeverityLevel.LOW,
            (0.2, 0.5): SeverityLevel.MEDIUM,
            (0.5, 0.8): SeverityLevel.HIGH,
            (0.8, 1.0): SeverityLevel.CRITICAL
        }

        # Platform-specific risk adjustments
        self.platform_risk_adjustments = {
            SocialPlatform.YOUTUBE: {
                RiskCategory.ADULT_CONTENT: 1.2,  # Higher scrutiny for video content
                RiskCategory.VIOLENCE: 1.3
            },
            SocialPlatform.TIKTOK: {
                RiskCategory.INAPPROPRIATE_LANGUAGE: 0.8,  # More lenient for younger audience
                RiskCategory.CONTROVERSIAL_TOPICS: 1.1
            },
            SocialPlatform.LINKEDIN: {
                RiskCategory.CONTROVERSIAL_TOPICS: 1.5,  # Professional context
                RiskCategory.INAPPROPRIATE_LANGUAGE: 1.3
            }
        }

    async def analyze_brand_safety(
        self,
        content_text: Optional[str] = None,
        content_url: Optional[str] = None,
        media_urls: List[str] = None,
        platform: SocialPlatform = None,
        brand_guidelines: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive brand safety analysis.

        Args:
            content_text: Text content to analyze
            content_url: URL of the content
            media_urls: List of media URLs
            platform: Social media platform
            brand_guidelines: Custom brand safety guidelines
            context: Additional context for analysis

        Returns:
            Dict containing brand safety analysis results
        """
        if not content_text and not content_url:
            raise ValueError("Either content_text or content_url must be provided")

        detected_risks = []
        risk_categories = {}
        overall_score = 1.0

        try:
            # Extract text if URL provided
            if content_url and not content_text:
                content_text = await self._extract_text_from_url(content_url)

            if not content_text:
                content_text = ""

            # Analyze different risk categories
            content_lower = content_text.lower()

            # Adult content analysis
            adult_risk = await self._analyze_adult_content(content_lower)
            if adult_risk:
                detected_risks.extend(adult_risk)
                risk_categories[RiskCategory.ADULT_CONTENT] = len(adult_risk) / 10

            # Violence analysis
            violence_risk = await self._analyze_violence(content_lower)
            if violence_risk:
                detected_risks.extend(violence_risk)
                risk_categories[RiskCategory.VIOLENCE] = len(violence_risk) / 10

            # Hate speech analysis
            hate_risk = await self._analyze_hate_speech(content_lower)
            if hate_risk:
                detected_risks.extend(hate_risk)
                risk_categories[RiskCategory.HATE_SPEECH] = len(hate_risk) / 10

            # Illegal activities analysis
            illegal_risk = await self._analyze_illegal_activities(content_lower)
            if illegal_risk:
                detected_risks.extend(illegal_risk)
                risk_categories[RiskCategory.ILLEGAL_ACTIVITIES] = len(illegal_risk) / 10

            # Misinformation analysis
            misinfo_risk = await self._analyze_misinformation(content_lower)
            if misinfo_risk:
                detected_risks.extend(misinfo_risk)
                risk_categories[RiskCategory.MISINFORMATION] = len(misinfo_risk) / 10

            # Spam analysis
            spam_risk = await self._analyze_spam(content_lower)
            if spam_risk:
                detected_risks.extend(spam_risk)
                risk_categories[RiskCategory.SPAM] = len(spam_risk) / 10

            # Controversial topics analysis
            controversial_risk = await self._analyze_controversial_topics(content_lower)
            if controversial_risk:
                detected_risks.extend(controversial_risk)
                risk_categories[RiskCategory.CONTROVERSIAL_TOPICS] = len(controversial_risk) / 10

            # Inappropriate language analysis
            language_risk = await self._analyze_inappropriate_language(content_lower)
            if language_risk:
                detected_risks.extend(language_risk)
                risk_categories[RiskCategory.INAPPROPRIATE_LANGUAGE] = len(language_risk) / 10

            # Competitor mentions analysis
            competitor_risk = await self._analyze_competitor_mentions(content_lower)
            if competitor_risk:
                detected_risks.extend(competitor_risk)
                risk_categories[RiskCategory.COMPETITOR_MENTIONS] = len(competitor_risk) / 10

            # Sentiment analysis for brand safety
            sentiment_risk = await self._analyze_negative_sentiment(content_text)
            if sentiment_risk:
                detected_risks.extend(sentiment_risk)
                risk_categories[RiskCategory.NEGATIVE_SENTIMENT] = sentiment_risk[0].confidence

            # Apply platform-specific adjustments
            if platform:
                risk_categories = self._apply_platform_adjustments(risk_categories, platform)

            # Calculate overall brand safety score
            overall_score = await self._calculate_overall_score(
                risk_categories, brand_guidelines
            )

            # Generate recommendations
            recommendations = await self._generate_safety_recommendations(
                detected_risks, risk_categories, platform
            )

            return {
                'overall_score': overall_score,
                'risk_categories': risk_categories,
                'detected_risks': [risk.dict() for risk in detected_risks],
                'recommendations': recommendations,
                'confidence': self._calculate_confidence(detected_risks),
                'analysis_version': '1.0.0',
                'created_at': datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Brand safety analysis failed: {str(e)}")
            raise

    async def _analyze_adult_content(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for adult/explicit material.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.adult_content_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.8)  # Adult content is high severity
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.ADULT_CONTENT,
                        severity=severity,
                        description=f"Adult content detected: '{match}'",
                        confidence=0.9,
                        detected_content=match
                    ))

        return risks

    async def _analyze_violence(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for violent content.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.violence_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.7)
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.VIOLENCE,
                        severity=severity,
                        description=f"Violent content detected: '{match}'",
                        confidence=0.8,
                        detected_content=match
                    ))

        return risks

    async def _analyze_hate_speech(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for hate speech.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.hate_speech_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = SeverityLevel.CRITICAL  # Hate speech is always critical
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.HATE_SPEECH,
                        severity=severity,
                        description=f"Hate speech detected: '{match}'",
                        confidence=0.9,
                        detected_content=match
                    ))

        return risks

    async def _analyze_illegal_activities(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for illegal activities.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.illegal_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = SeverityLevel.CRITICAL  # Illegal activities are critical
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.ILLEGAL_ACTIVITIES,
                        severity=severity,
                        description=f"Illegal activity reference detected: '{match}'",
                        confidence=0.8,
                        detected_content=match
                    ))

        return risks

    async def _analyze_misinformation(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for misinformation.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.misinformation_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.6)
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.MISINFORMATION,
                        severity=severity,
                        description=f"Potential misinformation detected: '{match}'",
                        confidence=0.7,
                        detected_content=match
                    ))

        return risks

    async def _analyze_spam(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for spam characteristics.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.spam_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.4)
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.SPAM,
                        severity=severity,
                        description=f"Spam-like content detected: '{match}'",
                        confidence=0.6,
                        detected_content=match
                    ))

        return risks

    async def _analyze_controversial_topics(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for controversial topics.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.controversial_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.5)
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.CONTROVERSIAL_TOPICS,
                        severity=severity,
                        description=f"Controversial topic detected: '{match}'",
                        confidence=0.7,
                        detected_content=match
                    ))

        return risks

    async def _analyze_inappropriate_language(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for inappropriate language.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.profanity_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.3)
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.INAPPROPRIATE_LANGUAGE,
                        severity=severity,
                        description=f"Inappropriate language detected: '{match}'",
                        confidence=0.8,
                        detected_content=match
                    ))

        return risks

    async def _analyze_competitor_mentions(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for competitor mentions.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        for pattern in self.competitor_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    severity = self._determine_severity(0.4)
                    risks.append(BrandSafetyRisk(
                        risk_type=RiskCategory.COMPETITOR_MENTIONS,
                        severity=severity,
                        description=f"Potential competitor mention: '{match}'",
                        confidence=0.6,
                        detected_content=match
                    ))

        return risks

    async def _analyze_negative_sentiment(self, content_text: str) -> List[BrandSafetyRisk]:
        """
        Analyze content for negative sentiment that could impact brand safety.

        Args:
            content_text: Text content to analyze

        Returns:
            List of detected brand safety risks
        """
        risks = []

        # Simple sentiment analysis for brand safety
        negative_indicators = [
            'terrible', 'awful', 'horrible', 'worst', 'hate', 'disgusting',
            'disappointing', 'failed', 'broken', 'useless', 'waste'
        ]

        content_lower = content_text.lower()
        negative_count = sum(1 for word in negative_indicators if word in content_lower)

        if negative_count > 2:  # Threshold for concerning negative sentiment
            severity = self._determine_severity(min(negative_count * 0.1, 0.8))
            risks.append(BrandSafetyRisk(
                risk_type=RiskCategory.NEGATIVE_SENTIMENT,
                severity=severity,
                description=f"High negative sentiment detected ({negative_count} negative indicators)",
                confidence=min(negative_count * 0.15, 0.9),
                detected_content=f"{negative_count} negative terms"
            ))

        return risks

    def _apply_platform_adjustments(
        self,
        risk_categories: Dict[RiskCategory, float],
        platform: SocialPlatform
    ) -> Dict[RiskCategory, float]:
        """
        Apply platform-specific risk adjustments.

        Args:
            risk_categories: Current risk category scores
            platform: Social media platform

        Returns:
            Adjusted risk category scores
        """
        adjustments = self.platform_risk_adjustments.get(platform, {})

        for category, adjustment in adjustments.items():
            if category in risk_categories:
                risk_categories[category] = min(1.0, risk_categories[category] * adjustment)

        return risk_categories

    async def _calculate_overall_score(
        self,
        risk_categories: Dict[RiskCategory, float],
        brand_guidelines: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate overall brand safety score.

        Args:
            risk_categories: Risk category scores
            brand_guidelines: Custom brand guidelines

        Returns:
            Overall brand safety score (0-1)
        """
        if not risk_categories:
            return 1.0

        # Use custom thresholds if provided
        thresholds = brand_guidelines.get('safety_thresholds', self.safety_thresholds) \
                    if brand_guidelines else self.safety_thresholds

        total_penalty = 0.0
        weight_sum = 0.0

        for category, score in risk_categories.items():
            threshold = thresholds.get(category, 0.5)

            # Calculate penalty based on threshold exceedance
            if score > threshold:
                penalty = (score - threshold) / (1.0 - threshold)

                # Weight penalties by category severity
                category_weight = self._get_category_weight(category)
                total_penalty += penalty * category_weight
                weight_sum += category_weight

        if weight_sum > 0:
            average_penalty = total_penalty / weight_sum
            return max(0.0, 1.0 - average_penalty)

        return 1.0

    def _get_category_weight(self, category: RiskCategory) -> float:
        """
        Get the weight/importance of a risk category.

        Args:
            category: Risk category

        Returns:
            Weight value
        """
        weights = {
            RiskCategory.HATE_SPEECH: 1.0,
            RiskCategory.ILLEGAL_ACTIVITIES: 1.0,
            RiskCategory.ADULT_CONTENT: 0.8,
            RiskCategory.VIOLENCE: 0.8,
            RiskCategory.MISINFORMATION: 0.7,
            RiskCategory.CONTROVERSIAL_TOPICS: 0.5,
            RiskCategory.INAPPROPRIATE_LANGUAGE: 0.4,
            RiskCategory.SPAM: 0.3,
            RiskCategory.COMPETITOR_MENTIONS: 0.3,
            RiskCategory.NEGATIVE_SENTIMENT: 0.2
        }

        return weights.get(category, 0.5)

    def _determine_severity(self, risk_score: float) -> SeverityLevel:
        """
        Determine severity level based on risk score.

        Args:
            risk_score: Risk score (0-1)

        Returns:
            Severity level
        """
        for (min_score, max_score), severity in self.risk_severity_mapping.items():
            if min_score <= risk_score < max_score:
                return severity

        return SeverityLevel.LOW

    async def _generate_safety_recommendations(
        self,
        detected_risks: List[BrandSafetyRisk],
        risk_categories: Dict[RiskCategory, float],
        platform: Optional[SocialPlatform]
    ) -> List[str]:
        """
        Generate brand safety recommendations.

        Args:
            detected_risks: List of detected risks
            risk_categories: Risk category scores
            platform: Social media platform

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Critical and high severity recommendations
        critical_risks = [risk for risk in detected_risks if risk.severity == SeverityLevel.CRITICAL]
        if critical_risks:
            recommendations.append("URGENT: Content contains critical brand safety violations - do not publish")
            recommendations.append("Review and remove all flagged critical content before proceeding")

        high_risks = [risk for risk in detected_risks if risk.severity == SeverityLevel.HIGH]
        if high_risks:
            recommendations.append("HIGH PRIORITY: Address high-severity brand safety issues")

        # Category-specific recommendations
        if RiskCategory.ADULT_CONTENT in risk_categories:
            recommendations.append("Remove or modify adult/explicit content references")

        if RiskCategory.HATE_SPEECH in risk_categories:
            recommendations.append("Completely remove hate speech content - zero tolerance policy")

        if RiskCategory.INAPPROPRIATE_LANGUAGE in risk_categories:
            recommendations.append("Consider replacing inappropriate language with professional alternatives")

        if RiskCategory.CONTROVERSIAL_TOPICS in risk_categories:
            recommendations.append("Review controversial topic mentions for brand alignment")

        if RiskCategory.COMPETITOR_MENTIONS in risk_categories:
            recommendations.append("Remove or clarify competitor references to avoid confusion")

        # Platform-specific recommendations
        if platform:
            if platform == SocialPlatform.LINKEDIN and RiskCategory.INAPPROPRIATE_LANGUAGE in risk_categories:
                recommendations.append("Maintain professional tone appropriate for LinkedIn audience")

            if platform == SocialPlatform.YOUTUBE and RiskCategory.ADULT_CONTENT in risk_categories:
                recommendations.append("Ensure video content meets YouTube's strict community guidelines")

        # General recommendations
        if detected_risks:
            recommendations.extend([
                "Implement content review process before publishing",
                "Consider brand safety guidelines for future content creation",
                "Monitor audience feedback for any safety concerns"
            ])

        return recommendations

    def _calculate_confidence(self, detected_risks: List[BrandSafetyRisk]) -> float:
        """
        Calculate confidence score for the analysis.

        Args:
            detected_risks: List of detected risks

        Returns:
            Confidence score (0-1)
        """
        if not detected_risks:
            return 0.9  # High confidence when no risks detected

        # Average confidence of detected risks
        total_confidence = sum(risk.confidence for risk in detected_risks)
        return total_confidence / len(detected_risks)

    async def _extract_text_from_url(self, url: str) -> str:
        """
        Extract text content from a URL for analysis.

        Args:
            url: URL to extract text from

        Returns:
            Extracted text content
        """
        # Placeholder for URL text extraction
        # In production, this would use web scraping or API calls
        logger.info(f"Extracting text from URL for brand safety analysis: {url}")
        return ""