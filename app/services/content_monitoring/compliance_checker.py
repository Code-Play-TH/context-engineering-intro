"""
Compliance Checker Service

Provides comprehensive compliance checking for content including:
- Regulatory compliance verification
- Platform policy compliance
- Legal requirement checking
- Industry standard compliance
- Advertising standards compliance
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from app.schemas.content_monitoring import (
    SeverityLevel, SocialPlatform, ComplianceIssue
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ComplianceCategory(str, Enum):
    """Compliance category enumeration."""
    ADVERTISING_STANDARDS = "advertising_standards"
    DATA_PROTECTION = "data_protection"
    PLATFORM_POLICIES = "platform_policies"
    COPYRIGHT = "copyright"
    ACCESSIBILITY = "accessibility"
    FINANCIAL_DISCLOSURE = "financial_disclosure"
    MEDICAL_CLAIMS = "medical_claims"
    CHILDREN_PROTECTION = "children_protection"
    GAMBLING = "gambling"
    ALCOHOL_TOBACCO = "alcohol_tobacco"


class ComplianceChecker:
    """
    Comprehensive compliance checking service for content verification.
    """

    def __init__(self):
        """Initialize the Compliance Checker with rule sets and configurations."""
        self._load_compliance_rules()

    def _load_compliance_rules(self) -> None:
        """
        Load compliance rules and patterns for various categories.
        """
        # Advertising standards compliance rules
        self.advertising_rules = {
            'disclosure_required': [
                r'#ad\b', r'#sponsored\b', r'#partnership\b', r'#collab\b',
                r'sponsored by', r'in partnership with', r'paid promotion'
            ],
            'misleading_claims': [
                r'guaranteed\s+results?', r'100%\s+effective', r'miracle\s+cure',
                r'instant\s+results?', r'no\s+side\s+effects?'
            ]
        }

        # Platform-specific policy rules
        self.platform_rules = {
            SocialPlatform.INSTAGRAM: {
                'hashtag_limit': 30,
                'character_limit': 2200,
                'prohibited_content': ['pyramid scheme', 'get rich quick']
            },
            SocialPlatform.YOUTUBE: {
                'description_limit': 5000,
                'title_limit': 100,
                'prohibited_content': ['clickbait', 'misleading thumbnail']
            },
            SocialPlatform.TIKTOK: {
                'character_limit': 300,
                'hashtag_limit': 100,
                'prohibited_content': ['dangerous challenges', 'harmful trends']
            },
            SocialPlatform.TWITTER: {
                'character_limit': 280,
                'hashtag_limit': 20,
                'prohibited_content': ['hate speech', 'harassment']
            },
            SocialPlatform.FACEBOOK: {
                'character_limit': 63206,
                'prohibited_content': ['fake news', 'misinformation']
            },
            SocialPlatform.LINKEDIN: {
                'character_limit': 3000,
                'prohibited_content': ['spam', 'irrelevant content']
            }
        }

        # Industry-specific compliance rules
        self.industry_rules = {
            'healthcare': {
                'prohibited_claims': [
                    r'cures?\s+cancer', r'cures?\s+diabetes', r'fda\s+approved',
                    r'medical\s+breakthrough', r'doctor\s+recommended'
                ],
                'required_disclaimers': [
                    'consult your doctor', 'not intended to diagnose',
                    'results may vary'
                ]
            },
            'finance': {
                'prohibited_claims': [
                    r'guaranteed\s+returns?', r'risk\s+free', r'easy\s+money',
                    r'get\s+rich\s+quick', r'investment\s+guarantee'
                ],
                'required_disclaimers': [
                    'investments carry risk', 'past performance',
                    'may lose money'
                ]
            },
            'beauty': {
                'prohibited_claims': [
                    r'anti\s+aging\s+miracle', r'fountain\s+of\s+youth',
                    r'permanent\s+results?', r'overnight\s+transformation'
                ],
                'required_disclaimers': [
                    'results may vary', 'individual results',
                    'typical results'
                ]
            }
        }

        # Legal compliance patterns
        self.legal_patterns = {
            'copyright_infringement': [
                r'copyrighted\s+material', r'unauthorized\s+use',
                r'stolen\s+content', r'plagiarized'
            ],
            'privacy_violations': [
                r'personal\s+information', r'private\s+data',
                r'without\s+consent', r'data\s+breach'
            ],
            'defamation': [
                r'false\s+accusations?', r'malicious\s+statements?',
                r'reputation\s+damage', r'slanderous'
            ]
        }

    async def check_compliance(
        self,
        content_text: Optional[str] = None,
        content_url: Optional[str] = None,
        media_urls: List[str] = None,
        platform: SocialPlatform = None,
        industry: Optional[str] = None,
        campaign_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive compliance checking.

        Args:
            content_text: Text content to check
            content_url: URL of the content
            media_urls: List of media URLs
            platform: Social media platform
            industry: Industry category
            campaign_id: Associated campaign ID

        Returns:
            Dict containing compliance check results
        """
        if not content_text and not content_url:
            raise ValueError("Either content_text or content_url must be provided")

        compliance_issues = []
        overall_score = 1.0  # Start with perfect compliance
        recommendations = []

        try:
            # Platform-specific compliance checks
            if platform and content_text:
                platform_issues = await self._check_platform_compliance(
                    content_text, platform
                )
                compliance_issues.extend(platform_issues)

            # Advertising standards compliance
            if content_text:
                ad_issues = await self._check_advertising_standards(content_text)
                compliance_issues.extend(ad_issues)

            # Industry-specific compliance
            if industry and content_text:
                industry_issues = await self._check_industry_compliance(
                    content_text, industry
                )
                compliance_issues.extend(industry_issues)

            # Legal compliance checks
            if content_text:
                legal_issues = await self._check_legal_compliance(content_text)
                compliance_issues.extend(legal_issues)

            # Data protection compliance
            if content_text:
                privacy_issues = await self._check_data_protection(content_text)
                compliance_issues.extend(privacy_issues)

            # Accessibility compliance
            if media_urls:
                accessibility_issues = await self._check_accessibility(
                    content_text, media_urls
                )
                compliance_issues.extend(accessibility_issues)

            # Calculate overall compliance score
            if compliance_issues:
                severity_weights = {
                    SeverityLevel.LOW: 0.05,
                    SeverityLevel.MEDIUM: 0.15,
                    SeverityLevel.HIGH: 0.30,
                    SeverityLevel.CRITICAL: 0.50
                }

                total_deduction = sum(
                    severity_weights.get(issue.severity, 0.1)
                    for issue in compliance_issues
                )
                overall_score = max(0.0, 1.0 - total_deduction)

            # Generate recommendations
            recommendations = await self._generate_recommendations(compliance_issues)

            return {
                'overall_score': overall_score,
                'compliance_issues': [issue.dict() for issue in compliance_issues],
                'recommendations': recommendations,
                'check_date': datetime.utcnow(),
                'status': 'compliant' if overall_score >= 0.8 else 'non_compliant'
            }

        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")
            raise

    async def _check_platform_compliance(
        self,
        content_text: str,
        platform: SocialPlatform
    ) -> List[ComplianceIssue]:
        """
        Check platform-specific compliance rules.

        Args:
            content_text: Text content to check
            platform: Social media platform

        Returns:
            List of compliance issues found
        """
        issues = []
        platform_rules = self.platform_rules.get(platform, {})

        # Character limit check
        char_limit = platform_rules.get('character_limit')
        if char_limit and len(content_text) > char_limit:
            issues.append(ComplianceIssue(
                issue_type="character_limit_exceeded",
                description=f"Content exceeds {platform.value} character limit of {char_limit}",
                severity=SeverityLevel.HIGH,
                recommendation=f"Reduce content length to under {char_limit} characters",
                confidence=1.0
            ))

        # Hashtag limit check
        hashtag_limit = platform_rules.get('hashtag_limit')
        if hashtag_limit:
            hashtags = re.findall(r'#\w+', content_text)
            if len(hashtags) > hashtag_limit:
                issues.append(ComplianceIssue(
                    issue_type="hashtag_limit_exceeded",
                    description=f"Too many hashtags for {platform.value} (limit: {hashtag_limit})",
                    severity=SeverityLevel.MEDIUM,
                    recommendation=f"Reduce hashtags to {hashtag_limit} or fewer",
                    confidence=1.0
                ))

        # Prohibited content check
        prohibited_content = platform_rules.get('prohibited_content', [])
        content_lower = content_text.lower()
        for prohibited in prohibited_content:
            if prohibited.lower() in content_lower:
                issues.append(ComplianceIssue(
                    issue_type="prohibited_content",
                    description=f"Content contains prohibited material: '{prohibited}'",
                    severity=SeverityLevel.HIGH,
                    recommendation=f"Remove or modify content related to '{prohibited}'",
                    confidence=0.8
                ))

        return issues

    async def _check_advertising_standards(self, content_text: str) -> List[ComplianceIssue]:
        """
        Check advertising standards compliance.

        Args:
            content_text: Text content to check

        Returns:
            List of compliance issues found
        """
        issues = []
        content_lower = content_text.lower()

        # Check for required disclosures
        has_disclosure = any(
            re.search(pattern, content_lower)
            for pattern in self.advertising_rules['disclosure_required']
        )

        # Detect promotional content indicators
        promotional_indicators = [
            'sponsored', 'promotion', 'discount', 'sale', 'buy now',
            'limited time', 'exclusive offer', 'partnership'
        ]

        is_promotional = any(indicator in content_lower for indicator in promotional_indicators)

        if is_promotional and not has_disclosure:
            issues.append(ComplianceIssue(
                issue_type="missing_disclosure",
                description="Promotional content missing required disclosure",
                severity=SeverityLevel.HIGH,
                recommendation="Add appropriate disclosure tags (#ad, #sponsored, etc.)",
                confidence=0.9
            ))

        # Check for misleading claims
        for pattern in self.advertising_rules['misleading_claims']:
            if re.search(pattern, content_lower):
                issues.append(ComplianceIssue(
                    issue_type="misleading_claims",
                    description=f"Content contains potentially misleading claims",
                    severity=SeverityLevel.HIGH,
                    recommendation="Remove or substantiate claims with evidence",
                    confidence=0.8
                ))

        return issues

    async def _check_industry_compliance(
        self,
        content_text: str,
        industry: str
    ) -> List[ComplianceIssue]:
        """
        Check industry-specific compliance rules.

        Args:
            content_text: Text content to check
            industry: Industry category

        Returns:
            List of compliance issues found
        """
        issues = []
        industry_rules = self.industry_rules.get(industry.lower(), {})
        content_lower = content_text.lower()

        # Check prohibited claims
        prohibited_claims = industry_rules.get('prohibited_claims', [])
        for pattern in prohibited_claims:
            if re.search(pattern, content_lower):
                issues.append(ComplianceIssue(
                    issue_type="prohibited_industry_claim",
                    description=f"Content contains prohibited {industry} claim",
                    severity=SeverityLevel.CRITICAL,
                    recommendation=f"Remove prohibited {industry} claims and add disclaimers",
                    confidence=0.9
                ))

        # Check required disclaimers
        required_disclaimers = industry_rules.get('required_disclaimers', [])
        if prohibited_claims and required_disclaimers:
            has_disclaimer = any(
                disclaimer.lower() in content_lower
                for disclaimer in required_disclaimers
            )

            if not has_disclaimer:
                issues.append(ComplianceIssue(
                    issue_type="missing_disclaimer",
                    description=f"Missing required {industry} disclaimer",
                    severity=SeverityLevel.HIGH,
                    recommendation=f"Add appropriate {industry} disclaimer",
                    confidence=0.8
                ))

        return issues

    async def _check_legal_compliance(self, content_text: str) -> List[ComplianceIssue]:
        """
        Check legal compliance requirements.

        Args:
            content_text: Text content to check

        Returns:
            List of compliance issues found
        """
        issues = []
        content_lower = content_text.lower()

        for violation_type, patterns in self.legal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    issues.append(ComplianceIssue(
                        issue_type=violation_type,
                        description=f"Content may contain {violation_type.replace('_', ' ')}",
                        severity=SeverityLevel.CRITICAL,
                        recommendation=f"Review and remove potential {violation_type.replace('_', ' ')}",
                        confidence=0.7
                    ))

        return issues

    async def _check_data_protection(self, content_text: str) -> List[ComplianceIssue]:
        """
        Check data protection and privacy compliance.

        Args:
            content_text: Text content to check

        Returns:
            List of compliance issues found
        """
        issues = []
        content_lower = content_text.lower()

        # Check for personal data collection mentions
        data_collection_keywords = [
            'collect personal data', 'gather information', 'track users',
            'store data', 'share information', 'third party data'
        ]

        privacy_policy_mentions = [
            'privacy policy', 'data protection', 'gdpr compliance',
            'cookie policy', 'consent'
        ]

        has_data_collection = any(keyword in content_lower for keyword in data_collection_keywords)
        has_privacy_mention = any(mention in content_lower for mention in privacy_policy_mentions)

        if has_data_collection and not has_privacy_mention:
            issues.append(ComplianceIssue(
                issue_type="missing_privacy_notice",
                description="Content mentions data collection without privacy notice",
                severity=SeverityLevel.HIGH,
                recommendation="Add privacy policy reference or consent notice",
                confidence=0.8
            ))

        # Check for GDPR-related keywords
        gdpr_keywords = ['gdpr', 'data subject rights', 'right to be forgotten', 'data controller']
        if any(keyword in content_lower for keyword in gdpr_keywords):
            # Verify proper GDPR compliance language
            required_gdpr_elements = ['lawful basis', 'data retention', 'contact details']
            missing_elements = [elem for elem in required_gdpr_elements if elem not in content_lower]

            if missing_elements:
                issues.append(ComplianceIssue(
                    issue_type="incomplete_gdpr_notice",
                    description="GDPR notice missing required elements",
                    severity=SeverityLevel.HIGH,
                    recommendation=f"Add missing GDPR elements: {', '.join(missing_elements)}",
                    confidence=0.9
                ))

        return issues

    async def _check_accessibility(
        self,
        content_text: Optional[str],
        media_urls: List[str]
    ) -> List[ComplianceIssue]:
        """
        Check accessibility compliance requirements.

        Args:
            content_text: Text content to check
            media_urls: List of media URLs

        Returns:
            List of compliance issues found
        """
        issues = []

        # Check for alt text mentions for images
        if media_urls:
            image_urls = [url for url in media_urls
                         if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]

            if image_urls and content_text:
                alt_text_indicators = ['alt text', 'alt=', 'image description', 'describes image']
                has_alt_text = any(indicator in content_text.lower() for indicator in alt_text_indicators)

                if not has_alt_text:
                    issues.append(ComplianceIssue(
                        issue_type="missing_alt_text",
                        description="Images may be missing accessibility alt text",
                        severity=SeverityLevel.MEDIUM,
                        recommendation="Add alt text descriptions for images",
                        confidence=0.7
                    ))

        # Check for video captions
        if media_urls:
            video_urls = [url for url in media_urls
                         if any(ext in url.lower() for ext in ['.mp4', '.avi', '.mov', '.webm'])]

            if video_urls and content_text:
                caption_indicators = ['captions', 'subtitles', 'closed captions', 'transcript']
                has_captions = any(indicator in content_text.lower() for indicator in caption_indicators)

                if not has_captions:
                    issues.append(ComplianceIssue(
                        issue_type="missing_captions",
                        description="Videos may be missing accessibility captions",
                        severity=SeverityLevel.MEDIUM,
                        recommendation="Add captions or transcripts for videos",
                        confidence=0.7
                    ))

        return issues

    async def _generate_recommendations(
        self,
        compliance_issues: List[ComplianceIssue]
    ) -> List[str]:
        """
        Generate compliance recommendations based on identified issues.

        Args:
            compliance_issues: List of compliance issues

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Group issues by type for better recommendations
        issue_types = {}
        for issue in compliance_issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)

        # Generate type-specific recommendations
        for issue_type, issues in issue_types.items():
            severity_levels = [issue.severity for issue in issues]
            max_severity = max(severity_levels) if severity_levels else SeverityLevel.LOW

            if max_severity == SeverityLevel.CRITICAL:
                recommendations.append(f"URGENT: Address {issue_type.replace('_', ' ')} immediately")
            elif max_severity == SeverityLevel.HIGH:
                recommendations.append(f"HIGH PRIORITY: Resolve {issue_type.replace('_', ' ')} before publishing")
            else:
                recommendations.append(f"Consider addressing {issue_type.replace('_', ' ')} for better compliance")

        # Add general recommendations
        if compliance_issues:
            recommendations.extend([
                "Review all flagged content areas before publishing",
                "Consult legal team for critical compliance issues",
                "Implement compliance review workflow for future content"
            ])

        return recommendations

    def get_compliance_score(self, compliance_results: Dict[str, Any]) -> float:
        """
        Calculate overall compliance confidence score.

        Args:
            compliance_results: Results from compliance check

        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.9

        issues = compliance_results.get('compliance_issues', [])
        if not issues:
            return base_confidence

        # Adjust confidence based on issue types and severity
        critical_issues = len([issue for issue in issues if issue.get('severity') == SeverityLevel.CRITICAL])
        high_issues = len([issue for issue in issues if issue.get('severity') == SeverityLevel.HIGH])

        confidence_reduction = (critical_issues * 0.3) + (high_issues * 0.1)
        return max(0.1, base_confidence - confidence_reduction)