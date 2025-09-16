"""
AI Content Analyzer Service

Provides comprehensive AI-powered content analysis including:
- Sentiment and emotion analysis
- Topic extraction and classification
- Entity recognition and linking
- Language detection and quality assessment
- Engagement and virality prediction
- Content type classification
"""

import re
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from textblob import TextBlob
import spacy
from collections import Counter

from app.schemas.content_monitoring import (
    SentimentLabel, AnalysisType, SocialPlatform
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIContentAnalyzer:
    """
    AI-powered content analysis service for comprehensive content evaluation.
    """

    def __init__(self):
        """Initialize the AI Content Analyzer with required models and configurations."""
        self.nlp = None
        self._load_models()

        # Content quality indicators
        self.quality_keywords = {
            'high': ['exclusive', 'premium', 'unique', 'innovative', 'breakthrough'],
            'medium': ['good', 'nice', 'interesting', 'cool', 'awesome'],
            'low': ['bad', 'terrible', 'awful', 'boring', 'waste']
        }

        # Engagement prediction factors
        self.engagement_factors = {
            'hashtags': 0.15,
            'mentions': 0.10,
            'questions': 0.20,
            'call_to_action': 0.25,
            'visual_content': 0.30
        }

    def _load_models(self) -> None:
        """
        Load required NLP models and AI services.

        Note: In production, this would load actual AI/ML models.
        For now, using lightweight alternatives.
        """
        try:
            # Load spaCy model for NLP tasks
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            logger.warning("spaCy model not found, using basic text processing")
            self.nlp = None

    async def analyze_content(
        self,
        content_text: Optional[str] = None,
        content_url: Optional[str] = None,
        media_urls: List[str] = None,
        platform: SocialPlatform = None,
        analysis_types: List[AnalysisType] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive content analysis.

        Args:
            content_text: Text content to analyze
            content_url: URL of the content
            media_urls: List of media URLs
            platform: Social media platform
            analysis_types: Types of analysis to perform

        Returns:
            Dict containing analysis results
        """
        if not content_text and not content_url:
            raise ValueError("Either content_text or content_url must be provided")

        # If no analysis types specified, perform all
        if not analysis_types:
            analysis_types = list(AnalysisType)

        results = {
            'analysis_version': '1.0.0',
            'processing_time': 0.0,
            'ai_confidence': 0.85
        }

        start_time = datetime.utcnow()

        try:
            # Extract text if URL provided
            if content_url and not content_text:
                content_text = await self._extract_text_from_url(content_url)

            if not content_text:
                content_text = ""

            # Perform requested analyses
            if AnalysisType.SENTIMENT in analysis_types:
                sentiment_results = await self._analyze_sentiment(content_text)
                results.update(sentiment_results)

            if AnalysisType.EMOTION in analysis_types:
                emotion_results = await self._analyze_emotions(content_text)
                results.update(emotion_results)

            if AnalysisType.TOPICS in analysis_types:
                topic_results = await self._extract_topics(content_text)
                results.update(topic_results)

            if AnalysisType.ENTITIES in analysis_types:
                entity_results = await self._extract_entities(content_text)
                results.update(entity_results)

            if AnalysisType.LANGUAGE in analysis_types:
                language_results = await self._detect_language(content_text)
                results.update(language_results)

            if AnalysisType.QUALITY in analysis_types:
                quality_results = await self._assess_quality(content_text, media_urls)
                results.update(quality_results)

            if AnalysisType.ENGAGEMENT_PREDICTION in analysis_types:
                engagement_results = await self._predict_engagement(
                    content_text, platform, media_urls
                )
                results.update(engagement_results)

            if AnalysisType.VIRALITY in analysis_types:
                virality_results = await self._assess_virality(content_text, platform)
                results.update(virality_results)

            if AnalysisType.CONTENT_TYPE in analysis_types:
                content_type_results = await self._classify_content_type(
                    content_text, media_urls
                )
                results.update(content_type_results)

            if AnalysisType.HASHTAG_ANALYSIS in analysis_types:
                hashtag_results = await self._analyze_hashtags(content_text)
                results.update(hashtag_results)

            if AnalysisType.MENTION_ANALYSIS in analysis_types:
                mention_results = await self._analyze_mentions(content_text)
                results.update(mention_results)

            # Calculate processing time
            end_time = datetime.utcnow()
            results['processing_time'] = (end_time - start_time).total_seconds()

            return results

        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            raise

    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing sentiment analysis results
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity

            # Map polarity to sentiment labels
            if polarity > 0.1:
                sentiment_label = SentimentLabel.POSITIVE
            elif polarity < -0.1:
                sentiment_label = SentimentLabel.NEGATIVE
            else:
                sentiment_label = SentimentLabel.NEUTRAL

            # Check for mixed sentiment (conflicting emotions)
            sentences = blob.sentences
            if len(sentences) > 1:
                polarities = [s.sentiment.polarity for s in sentences]
                if max(polarities) > 0.1 and min(polarities) < -0.1:
                    sentiment_label = SentimentLabel.MIXED

            return {
                'sentiment_score': polarity,
                'sentiment_label': sentiment_label
            }

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': SentimentLabel.NEUTRAL
            }

    async def _analyze_emotions(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotions in the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing emotion analysis results
        """
        # Basic emotion detection based on keywords
        emotion_keywords = {
            'joy': ['happy', 'excited', 'thrilled', 'delighted', 'amazing'],
            'sadness': ['sad', 'disappointed', 'upset', 'depressed', 'crying'],
            'anger': ['angry', 'furious', 'mad', 'irritated', 'outraged'],
            'fear': ['scared', 'afraid', 'terrified', 'worried', 'anxious'],
            'surprise': ['surprised', 'shocked', 'amazed', 'unexpected', 'wow'],
            'disgust': ['disgusting', 'awful', 'terrible', 'gross', 'yuck']
        }

        text_lower = text.lower()
        emotion_scores = {}

        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            # Normalize score
            emotion_scores[emotion] = min(score / len(keywords), 1.0)

        return {'emotion_scores': emotion_scores}

    async def _extract_topics(self, text: str) -> Dict[str, Any]:
        """
        Extract topics from the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing topic extraction results
        """
        if not self.nlp:
            return {'topics': []}

        try:
            doc = self.nlp(text)

            # Extract noun phrases as potential topics
            topics = []
            for chunk in doc.noun_chunks:
                if len(chunk.text.strip()) > 2:
                    topics.append(chunk.text.strip())

            # Get most common topics
            topic_counts = Counter(topics)
            top_topics = [topic for topic, count in topic_counts.most_common(10)]

            return {'topics': top_topics}

        except Exception as e:
            logger.error(f"Topic extraction failed: {str(e)}")
            return {'topics': []}

    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing entity extraction results
        """
        if not self.nlp:
            return {'entities': []}

        try:
            doc = self.nlp(text)

            entities = []
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'description': spacy.explain(ent.label_),
                    'start': ent.start_char,
                    'end': ent.end_char
                })

            return {'entities': entities}

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return {'entities': []}

    async def _detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing language detection results
        """
        try:
            blob = TextBlob(text)
            # Simple language detection (in production, use proper language detection)
            language = 'en'  # Default to English

            # Basic heuristics for common languages
            if any(char in text for char in '你好中文'):
                language = 'zh'
            elif any(char in text for char in 'こんにちは日本語'):
                language = 'ja'
            elif any(char in text for char in '안녕하세요한국어'):
                language = 'ko'

            return {'language_detected': language}

        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return {'language_detected': 'en'}

    async def _assess_quality(
        self,
        text: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assess the quality of the content.

        Args:
            text: Text content to analyze
            media_urls: List of media URLs

        Returns:
            Dict containing quality assessment results
        """
        score = 0.5  # Base score

        # Text quality factors
        if text:
            # Length factor
            if 50 <= len(text) <= 500:
                score += 0.1
            elif len(text) > 500:
                score += 0.05

            # Grammar and spelling (basic check)
            blob = TextBlob(text)
            try:
                corrected = blob.correct()
                if str(blob) == str(corrected):
                    score += 0.1  # No corrections needed
            except:
                pass

            # Keyword quality check
            text_lower = text.lower()
            high_quality_count = sum(1 for word in self.quality_keywords['high']
                                   if word in text_lower)
            low_quality_count = sum(1 for word in self.quality_keywords['low']
                                  if word in text_lower)

            score += (high_quality_count * 0.05)
            score -= (low_quality_count * 0.1)

        # Media quality factor
        if media_urls:
            score += min(len(media_urls) * 0.1, 0.2)

        # Ensure score is between 0 and 1
        quality_score = max(0.0, min(1.0, score))

        return {'quality_score': quality_score}

    async def _predict_engagement(
        self,
        text: str,
        platform: SocialPlatform,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Predict engagement rate for the content.

        Args:
            text: Text content to analyze
            platform: Social media platform
            media_urls: List of media URLs

        Returns:
            Dict containing engagement prediction results
        """
        base_engagement = 0.02  # 2% base engagement rate

        if not text:
            return {'engagement_prediction': base_engagement}

        # Platform-specific adjustments
        platform_multipliers = {
            SocialPlatform.INSTAGRAM: 1.2,
            SocialPlatform.TIKTOK: 1.5,
            SocialPlatform.YOUTUBE: 0.8,
            SocialPlatform.TWITTER: 1.0,
            SocialPlatform.FACEBOOK: 0.7,
            SocialPlatform.LINKEDIN: 0.6,
            SocialPlatform.TWITCH: 1.1
        }

        multiplier = platform_multipliers.get(platform, 1.0)

        # Content factor analysis
        hashtag_count = len(re.findall(r'#\w+', text))
        mention_count = len(re.findall(r'@\w+', text))
        question_count = text.count('?')

        # Call-to-action detection
        cta_keywords = ['click', 'follow', 'like', 'share', 'comment', 'subscribe']
        cta_count = sum(1 for keyword in cta_keywords if keyword.lower() in text.lower())

        # Calculate engagement factors
        engagement_boost = 0
        engagement_boost += min(hashtag_count * 0.01, 0.05)  # Max 5% boost
        engagement_boost += min(mention_count * 0.02, 0.04)  # Max 4% boost
        engagement_boost += min(question_count * 0.03, 0.06)  # Max 6% boost
        engagement_boost += min(cta_count * 0.02, 0.08)      # Max 8% boost

        if media_urls:
            engagement_boost += min(len(media_urls) * 0.02, 0.1)  # Max 10% boost

        predicted_engagement = (base_engagement + engagement_boost) * multiplier

        return {'engagement_prediction': min(predicted_engagement, 0.5)}  # Cap at 50%

    async def _assess_virality(
        self,
        text: str,
        platform: SocialPlatform
    ) -> Dict[str, Any]:
        """
        Assess virality potential of the content.

        Args:
            text: Text content to analyze
            platform: Social media platform

        Returns:
            Dict containing virality assessment results
        """
        if not text:
            return {'virality_score': 0.0}

        virality_score = 0.1  # Base score

        # Viral content indicators
        viral_keywords = [
            'breaking', 'exclusive', 'shocking', 'amazing', 'incredible',
            'must see', 'you won\'t believe', 'goes viral', 'trending'
        ]

        text_lower = text.lower()
        viral_keyword_count = sum(1 for keyword in viral_keywords
                                if keyword in text_lower)

        # Emotional intensity (high emotions tend to go viral)
        emotion_words = [
            'love', 'hate', 'amazing', 'terrible', 'incredible', 'shocking',
            'outrageous', 'hilarious', 'heartbreaking', 'inspiring'
        ]

        emotion_count = sum(1 for word in emotion_words if word in text_lower)

        # Length factor (moderate length performs better)
        length_factor = 1.0
        if 100 <= len(text) <= 200:
            length_factor = 1.2
        elif len(text) < 50 or len(text) > 500:
            length_factor = 0.8

        # Platform-specific viral factors
        platform_viral_factors = {
            SocialPlatform.TIKTOK: 1.5,
            SocialPlatform.INSTAGRAM: 1.2,
            SocialPlatform.TWITTER: 1.3,
            SocialPlatform.YOUTUBE: 1.1,
            SocialPlatform.FACEBOOK: 1.0,
            SocialPlatform.LINKEDIN: 0.7,
            SocialPlatform.TWITCH: 1.0
        }

        platform_factor = platform_viral_factors.get(platform, 1.0)

        # Calculate final virality score
        virality_score += viral_keyword_count * 0.1
        virality_score += emotion_count * 0.05
        virality_score *= length_factor
        virality_score *= platform_factor

        # Ensure score is between 0 and 1
        virality_score = max(0.0, min(1.0, virality_score))

        return {'virality_score': virality_score}

    async def _classify_content_type(
        self,
        text: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Classify the type of content.

        Args:
            text: Text content to analyze
            media_urls: List of media URLs

        Returns:
            Dict containing content type classification results
        """
        content_types = []
        primary_type = "text"

        # Determine primary type based on media
        if media_urls:
            for url in media_urls:
                url_lower = url.lower()
                if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    content_types.append("image")
                    primary_type = "image"
                elif any(ext in url_lower for ext in ['.mp4', '.avi', '.mov', '.webm']):
                    content_types.append("video")
                    primary_type = "video"
                elif any(ext in url_lower for ext in ['.mp3', '.wav', '.ogg']):
                    content_types.append("audio")

        # Analyze text content for type indicators
        if text:
            text_lower = text.lower()

            # Educational content
            if any(word in text_lower for word in ['tutorial', 'how to', 'guide', 'tips', 'learn']):
                content_types.append("educational")

            # Entertainment content
            if any(word in text_lower for word in ['funny', 'joke', 'humor', 'entertainment', 'fun']):
                content_types.append("entertainment")

            # Promotional content
            if any(word in text_lower for word in ['buy', 'sale', 'discount', 'promotion', 'offer']):
                content_types.append("promotional")

            # News content
            if any(word in text_lower for word in ['breaking', 'news', 'report', 'update', 'announcement']):
                content_types.append("news")

            # Personal content
            if any(word in text_lower for word in ['my', 'i am', 'personal', 'diary', 'thoughts']):
                content_types.append("personal")

        if not content_types:
            content_types = ["general"]

        return {
            'content_type_detected': primary_type,
            'content_categories': content_types
        }

    async def _analyze_hashtags(self, text: str) -> Dict[str, Any]:
        """
        Analyze hashtags in the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing hashtag analysis results
        """
        if not text:
            return {'hashtags_detected': []}

        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)

        return {'hashtags_detected': hashtags}

    async def _analyze_mentions(self, text: str) -> Dict[str, Any]:
        """
        Analyze mentions in the content.

        Args:
            text: Text content to analyze

        Returns:
            Dict containing mention analysis results
        """
        if not text:
            return {'mentions_detected': []}

        # Extract mentions
        mentions = re.findall(r'@(\w+)', text)

        return {'mentions_detected': mentions}

    async def _extract_text_from_url(self, url: str) -> str:
        """
        Extract text content from a URL.

        Args:
            url: URL to extract text from

        Returns:
            Extracted text content
        """
        # Placeholder for URL text extraction
        # In production, this would use web scraping or API calls
        logger.info(f"Extracting text from URL: {url}")
        return ""

    def get_analysis_confidence(self, analysis_results: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score for the analysis.

        Args:
            analysis_results: Results from content analysis

        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.8

        # Adjust based on available data
        if analysis_results.get('sentiment_score') is not None:
            base_confidence += 0.05

        if analysis_results.get('entities'):
            base_confidence += 0.05

        if analysis_results.get('topics'):
            base_confidence += 0.05

        if analysis_results.get('quality_score', 0) > 0.7:
            base_confidence += 0.05

        return min(1.0, base_confidence)