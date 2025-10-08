"""Permission service for role-based access control."""
from typing import Dict, Set
from fastapi import HTTPException, status
from app.models.enums import Role


# Permission matrix: role -> resource -> allowed actions
PERMISSION_MATRIX: Dict[str, Dict[str, Set[str]]] = {
    Role.ADMIN.value: {
        "users": {"create", "read", "update", "delete"},
        "campaigns": {"create", "read", "update", "delete"},
        "kols": {"create", "read", "update", "delete"},
        "briefs": {"create", "read", "update", "delete", "send"},
        "messages": {"create", "read"},
        "reports": {"create", "read"},
    },
    Role.CAMPAIGN_MANAGER.value: {
        "users": {"read"},
        "campaigns": {"create", "read", "update"},
        "kols": {"create", "read", "update"},
        "briefs": {"create", "read", "update", "send"},
        "messages": {"create", "read"},
        "reports": {"create", "read"},
    },
    Role.ACCOUNT_EXECUTIVE.value: {
        "users": {"read"},
        "campaigns": {"read"},
        "kols": {"read", "update"},
        "briefs": {"create", "read", "update", "send"},
        "messages": {"create", "read"},
        "reports": {"read"},
    },
    Role.VIEWER.value: {
        "users": set(),
        "campaigns": {"read"},
        "kols": {"read"},
        "briefs": {"read"},
        "messages": {"read"},
        "reports": {"read"},
    },
}


class PermissionService:
    """Service for checking user permissions."""
    
    @staticmethod
    def check_permission(user_role: str, resource: str, action: str) -> bool:
        """
        Check if a user role has permission for a specific action on a resource.
        
        Args:
            user_role: User's role
            resource: Resource name (e.g., "campaigns", "kols")
            action: Action to perform (e.g., "create", "read", "update", "delete")
            
        Returns:
            True if permission is granted, False otherwise
        """
        role_permissions = PERMISSION_MATRIX.get(user_role, {})
        resource_permissions = role_permissions.get(resource, set())
        return action in resource_permissions
    
    @staticmethod
    def require_permission(user_role: str, resource: str, action: str) -> None:
        """
        Require permission or raise HTTPException.
        
        Args:
            user_role: User's role
            resource: Resource name
            action: Action to perform
            
        Raises:
            HTTPException: If permission is denied
        """
        if not PermissionService.check_permission(user_role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to {action} {resource}"
            )
