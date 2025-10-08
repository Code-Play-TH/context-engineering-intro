"""
Enums for database models
"""
from enum import Enum


class Role(str, Enum):
    """User role enum for role-based access control"""
    ADMIN = "admin"
    CAMPAIGN_MANAGER = "campaign_manager"
    ACCOUNT_EXECUTIVE = "account_executive"
    VIEWER = "viewer"
