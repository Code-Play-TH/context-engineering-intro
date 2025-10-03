"""
Database models package.
Imports all models for SQLAlchemy to register them properly.
"""

from app.models.kol import KOL, CampaignKOL, KOLStatus, KOLSocialAccounts, KOLPerformanceMetrics
from app.models.campaign import Campaign, Brief, BriefTemplate, CampaignStatus, ApprovalStatus
from app.models.collaboration import Collaboration
from app.models.campaign_content import CampaignBrief, CampaignContent
from app.models.communication import (
    Message,
    FollowUpSchedule,
    MessageTemplate,
    CommunicationChannel,
    MessageStatus,
    ScheduleStatus
)
from app.models.content import (
    ContentPost,
    ContentStats,
    ContentAlert,
    VerificationStatus,
    ContentType
)
from app.models.user import User, UserSession, AuditLog, UserRole, UserStatus

# Export all models for easy importing
__all__ = [
    # KOL models
    "KOL",
    "CampaignKOL",
    "KOLStatus",
    "KOLSocialAccounts",
    "KOLPerformanceMetrics",

    # Campaign models
    "Campaign",
    "Brief",
    "BriefTemplate",
    "CampaignStatus",
    "ApprovalStatus",
    "Collaboration",
    "CampaignBrief",
    "CampaignContent",

    # Communication models
    "Message",
    "FollowUpSchedule",
    "MessageTemplate",
    "CommunicationChannel",
    "MessageStatus",
    "ScheduleStatus",

    # Content models
    "ContentPost",
    "ContentStats",
    "ContentAlert",
    "VerificationStatus",
    "ContentType",

    # User models
    "User",
    "UserSession",
    "AuditLog",
    "UserRole",
    "UserStatus",
]