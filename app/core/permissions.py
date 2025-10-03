"""
Permission definitions and role-based access control constants.

This module defines all permissions in the system and their mappings to roles.
Permissions are granular and can be assigned individually or through roles.
"""

from enum import Enum
from typing import Dict, List, Set
from app.models.user import UserRole


class Permission(str, Enum):
    """
    All system permissions.

    Naming convention: {resource}_{action}
    - Resource: users, kols, campaigns, content, analytics, etc.
    - Action: create, read, update, delete, manage, verify, approve, etc.
    """

    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"  # Full user management
    USER_CHANGE_ROLE = "user:change_role"

    # KOL Management
    KOL_CREATE = "kol:create"
    KOL_READ = "kol:read"
    KOL_UPDATE = "kol:update"
    KOL_DELETE = "kol:delete"
    KOL_MANAGE = "kol:manage"  # Full KOL management
    KOL_VERIFY = "kol:verify"  # Verify KOL authenticity
    KOL_IMPORT = "kol:import"  # Bulk import
    KOL_EXPORT = "kol:export"  # Bulk export

    # Social Media Accounts
    SOCIAL_ACCOUNT_LINK = "social_account:link"
    SOCIAL_ACCOUNT_UNLINK = "social_account:unlink"
    SOCIAL_ACCOUNT_REFRESH = "social_account:refresh"  # Refresh stats

    # Campaign Management
    CAMPAIGN_CREATE = "campaign:create"
    CAMPAIGN_READ = "campaign:read"
    CAMPAIGN_UPDATE = "campaign:update"
    CAMPAIGN_DELETE = "campaign:delete"
    CAMPAIGN_MANAGE = "campaign:manage"  # Full campaign management
    CAMPAIGN_APPROVE = "campaign:approve"
    CAMPAIGN_ARCHIVE = "campaign:archive"

    # Brief Management
    BRIEF_CREATE = "brief:create"
    BRIEF_READ = "brief:read"
    BRIEF_UPDATE = "brief:update"
    BRIEF_DELETE = "brief:delete"
    BRIEF_SEND = "brief:send"
    BRIEF_APPROVE = "brief:approve"

    # Collaboration Management
    COLLABORATION_CREATE = "collaboration:create"
    COLLABORATION_READ = "collaboration:read"
    COLLABORATION_UPDATE = "collaboration:update"
    COLLABORATION_DELETE = "collaboration:delete"
    COLLABORATION_APPROVE = "collaboration:approve"

    # Content Monitoring
    CONTENT_READ = "content:read"
    CONTENT_VERIFY = "content:verify"
    CONTENT_FLAG = "content:flag"  # Flag inappropriate content
    CONTENT_ANALYZE = "content:analyze"  # Trigger AI analysis
    CONTENT_MODERATE = "content:moderate"  # Content moderation

    # Analytics & Reporting
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_ADVANCED = "analytics:advanced"  # Advanced analytics features
    REPORT_GENERATE = "report:generate"
    REPORT_SCHEDULE = "report:schedule"
    REPORT_CUSTOMIZE = "report:customize"

    # Communication
    MESSAGE_SEND = "message:send"
    MESSAGE_READ = "message:read"
    MESSAGE_DELETE = "message:delete"
    NOTIFICATION_SEND = "notification:send"
    NOTIFICATION_MANAGE = "notification:manage"

    # System Settings
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"
    SETTINGS_MANAGE = "settings:manage"

    # Audit & Compliance
    AUDIT_LOG_READ = "audit_log:read"
    AUDIT_LOG_EXPORT = "audit_log:export"
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_MANAGE = "compliance:manage"

    # Financial
    PAYMENT_VIEW = "payment:view"
    PAYMENT_PROCESS = "payment:process"
    BUDGET_VIEW = "budget:view"
    BUDGET_MANAGE = "budget:manage"

    # System Administration
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_ADMIN = "system:admin"  # Full system access


# Role to Permissions Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {

    UserRole.ADMIN: {
        # Admins have ALL permissions
        *Permission.__members__.values()
    },

    UserRole.MANAGER: {
        # User Management (limited)
        Permission.USER_READ,
        Permission.USER_UPDATE,

        # KOL Management (full)
        Permission.KOL_CREATE,
        Permission.KOL_READ,
        Permission.KOL_UPDATE,
        Permission.KOL_DELETE,
        Permission.KOL_MANAGE,
        Permission.KOL_VERIFY,
        Permission.KOL_IMPORT,
        Permission.KOL_EXPORT,

        # Social Media
        Permission.SOCIAL_ACCOUNT_LINK,
        Permission.SOCIAL_ACCOUNT_UNLINK,
        Permission.SOCIAL_ACCOUNT_REFRESH,

        # Campaign Management (full)
        Permission.CAMPAIGN_CREATE,
        Permission.CAMPAIGN_READ,
        Permission.CAMPAIGN_UPDATE,
        Permission.CAMPAIGN_DELETE,
        Permission.CAMPAIGN_MANAGE,
        Permission.CAMPAIGN_APPROVE,
        Permission.CAMPAIGN_ARCHIVE,

        # Brief Management (full)
        Permission.BRIEF_CREATE,
        Permission.BRIEF_READ,
        Permission.BRIEF_UPDATE,
        Permission.BRIEF_DELETE,
        Permission.BRIEF_SEND,
        Permission.BRIEF_APPROVE,

        # Collaboration (full)
        Permission.COLLABORATION_CREATE,
        Permission.COLLABORATION_READ,
        Permission.COLLABORATION_UPDATE,
        Permission.COLLABORATION_DELETE,
        Permission.COLLABORATION_APPROVE,

        # Content (full)
        Permission.CONTENT_READ,
        Permission.CONTENT_VERIFY,
        Permission.CONTENT_FLAG,
        Permission.CONTENT_ANALYZE,
        Permission.CONTENT_MODERATE,

        # Analytics (full)
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_ADVANCED,
        Permission.REPORT_GENERATE,
        Permission.REPORT_SCHEDULE,
        Permission.REPORT_CUSTOMIZE,

        # Communication
        Permission.MESSAGE_SEND,
        Permission.MESSAGE_READ,
        Permission.MESSAGE_DELETE,
        Permission.NOTIFICATION_SEND,
        Permission.NOTIFICATION_MANAGE,

        # Financial
        Permission.PAYMENT_VIEW,
        Permission.PAYMENT_PROCESS,
        Permission.BUDGET_VIEW,
        Permission.BUDGET_MANAGE,

        # Audit
        Permission.AUDIT_LOG_READ,
        Permission.AUDIT_LOG_EXPORT,

        # Settings (read only)
        Permission.SETTINGS_READ,
    },

    UserRole.COORDINATOR: {
        # KOL Management
        Permission.KOL_CREATE,
        Permission.KOL_READ,
        Permission.KOL_UPDATE,
        Permission.KOL_VERIFY,
        Permission.KOL_EXPORT,

        # Social Media
        Permission.SOCIAL_ACCOUNT_LINK,
        Permission.SOCIAL_ACCOUNT_UNLINK,
        Permission.SOCIAL_ACCOUNT_REFRESH,

        # Campaign (read and update)
        Permission.CAMPAIGN_READ,
        Permission.CAMPAIGN_UPDATE,

        # Brief Management
        Permission.BRIEF_CREATE,
        Permission.BRIEF_READ,
        Permission.BRIEF_UPDATE,
        Permission.BRIEF_SEND,

        # Collaboration
        Permission.COLLABORATION_CREATE,
        Permission.COLLABORATION_READ,
        Permission.COLLABORATION_UPDATE,

        # Content
        Permission.CONTENT_READ,
        Permission.CONTENT_VERIFY,
        Permission.CONTENT_FLAG,

        # Analytics (basic)
        Permission.ANALYTICS_VIEW,
        Permission.REPORT_GENERATE,

        # Communication
        Permission.MESSAGE_SEND,
        Permission.MESSAGE_READ,
        Permission.NOTIFICATION_SEND,

        # Financial (view only)
        Permission.PAYMENT_VIEW,
        Permission.BUDGET_VIEW,
    },

    UserRole.ANALYST: {
        # KOL (read only)
        Permission.KOL_READ,
        Permission.KOL_EXPORT,

        # Campaign (read only)
        Permission.CAMPAIGN_READ,

        # Brief (read only)
        Permission.BRIEF_READ,

        # Collaboration (read only)
        Permission.COLLABORATION_READ,

        # Content (read and analyze)
        Permission.CONTENT_READ,
        Permission.CONTENT_ANALYZE,

        # Analytics (full)
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_ADVANCED,
        Permission.REPORT_GENERATE,
        Permission.REPORT_SCHEDULE,
        Permission.REPORT_CUSTOMIZE,

        # Communication (read only)
        Permission.MESSAGE_READ,

        # Financial (view only)
        Permission.PAYMENT_VIEW,
        Permission.BUDGET_VIEW,
    },

    UserRole.VIEWER: {
        # KOL (read only)
        Permission.KOL_READ,

        # Campaign (read only)
        Permission.CAMPAIGN_READ,

        # Brief (read only)
        Permission.BRIEF_READ,

        # Collaboration (read only)
        Permission.COLLABORATION_READ,

        # Content (read only)
        Permission.CONTENT_READ,

        # Analytics (basic view)
        Permission.ANALYTICS_VIEW,
        Permission.REPORT_GENERATE,

        # Communication (read only)
        Permission.MESSAGE_READ,
    },
}


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """
    Get all permissions for a given role.

    Args:
        role (UserRole): The user role.

    Returns:
        Set[Permission]: Set of permissions for the role.
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRole, permission: Permission, extra_permissions: List[str] = None) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role (UserRole): The user role.
        permission (Permission): The permission to check.
        extra_permissions (List[str], optional): Additional permissions granted to the user.

    Returns:
        bool: True if the role has the permission, False otherwise.
    """
    # Admin has all permissions
    if role == UserRole.ADMIN:
        return True

    # Check role permissions
    role_perms = get_role_permissions(role)
    if permission in role_perms:
        return True

    # Check extra permissions
    if extra_permissions and permission.value in extra_permissions:
        return True

    return False


def get_permission_description(permission: Permission) -> str:
    """
    Get human-readable description of a permission.

    Args:
        permission (Permission): The permission.

    Returns:
        str: Description of the permission.
    """
    descriptions = {
        # User Management
        Permission.USER_CREATE: "Create new users",
        Permission.USER_READ: "View user information",
        Permission.USER_UPDATE: "Update user information",
        Permission.USER_DELETE: "Delete users",
        Permission.USER_MANAGE: "Full user management access",
        Permission.USER_CHANGE_ROLE: "Change user roles",

        # KOL Management
        Permission.KOL_CREATE: "Create new KOL profiles",
        Permission.KOL_READ: "View KOL profiles",
        Permission.KOL_UPDATE: "Update KOL profiles",
        Permission.KOL_DELETE: "Delete KOL profiles",
        Permission.KOL_MANAGE: "Full KOL management access",
        Permission.KOL_VERIFY: "Verify KOL authenticity",
        Permission.KOL_IMPORT: "Bulk import KOLs",
        Permission.KOL_EXPORT: "Export KOL data",

        # Campaign Management
        Permission.CAMPAIGN_CREATE: "Create new campaigns",
        Permission.CAMPAIGN_READ: "View campaigns",
        Permission.CAMPAIGN_UPDATE: "Update campaigns",
        Permission.CAMPAIGN_DELETE: "Delete campaigns",
        Permission.CAMPAIGN_MANAGE: "Full campaign management access",
        Permission.CAMPAIGN_APPROVE: "Approve campaigns",

        # Analytics
        Permission.ANALYTICS_VIEW: "View analytics dashboards",
        Permission.ANALYTICS_EXPORT: "Export analytics data",
        Permission.ANALYTICS_ADVANCED: "Access advanced analytics",
        Permission.REPORT_GENERATE: "Generate reports",

        # Add more as needed...
    }

    return descriptions.get(permission, permission.value)


# Permission Groups for easier management
class PermissionGroup:
    """Predefined permission groups for common use cases."""

    # Read-only access
    READ_ONLY = {
        Permission.USER_READ,
        Permission.KOL_READ,
        Permission.CAMPAIGN_READ,
        Permission.BRIEF_READ,
        Permission.CONTENT_READ,
        Permission.ANALYTICS_VIEW,
        Permission.MESSAGE_READ,
    }

    # Content management
    CONTENT_MANAGEMENT = {
        Permission.CONTENT_READ,
        Permission.CONTENT_VERIFY,
        Permission.CONTENT_FLAG,
        Permission.CONTENT_ANALYZE,
    }

    # Campaign management
    CAMPAIGN_MANAGEMENT = {
        Permission.CAMPAIGN_CREATE,
        Permission.CAMPAIGN_READ,
        Permission.CAMPAIGN_UPDATE,
        Permission.CAMPAIGN_DELETE,
        Permission.BRIEF_CREATE,
        Permission.BRIEF_READ,
        Permission.BRIEF_UPDATE,
        Permission.BRIEF_SEND,
    }

    # Analytics access
    ANALYTICS_ACCESS = {
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.REPORT_GENERATE,
    }


# Resource-based permission checker
class ResourcePermission:
    """Helper class for resource-based permission checking."""

    @staticmethod
    def can_read(resource_type: str) -> Permission:
        """Get read permission for a resource type."""
        perm_map = {
            "user": Permission.USER_READ,
            "kol": Permission.KOL_READ,
            "campaign": Permission.CAMPAIGN_READ,
            "brief": Permission.BRIEF_READ,
            "content": Permission.CONTENT_READ,
            "analytics": Permission.ANALYTICS_VIEW,
        }
        return perm_map.get(resource_type.lower())

    @staticmethod
    def can_create(resource_type: str) -> Permission:
        """Get create permission for a resource type."""
        perm_map = {
            "user": Permission.USER_CREATE,
            "kol": Permission.KOL_CREATE,
            "campaign": Permission.CAMPAIGN_CREATE,
            "brief": Permission.BRIEF_CREATE,
        }
        return perm_map.get(resource_type.lower())

    @staticmethod
    def can_update(resource_type: str) -> Permission:
        """Get update permission for a resource type."""
        perm_map = {
            "user": Permission.USER_UPDATE,
            "kol": Permission.KOL_UPDATE,
            "campaign": Permission.CAMPAIGN_UPDATE,
            "brief": Permission.BRIEF_UPDATE,
        }
        return perm_map.get(resource_type.lower())

    @staticmethod
    def can_delete(resource_type: str) -> Permission:
        """Get delete permission for a resource type."""
        perm_map = {
            "user": Permission.USER_DELETE,
            "kol": Permission.KOL_DELETE,
            "campaign": Permission.CAMPAIGN_DELETE,
            "brief": Permission.BRIEF_DELETE,
        }
        return perm_map.get(resource_type.lower())
