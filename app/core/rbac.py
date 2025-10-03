"""
Role-Based Access Control (RBAC) utilities and decorators.

This module provides decorators and utilities for enforcing permissions
in API endpoints and business logic.
"""

from functools import wraps
from typing import List, Optional, Callable, Union
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.permissions import Permission, has_permission as check_permission
from app.models.user import User, UserRole


# HTTP Bearer token security
security = HTTPBearer()


class PermissionDenied(HTTPException):
    """Exception raised when user doesn't have required permission."""

    def __init__(
        self,
        permission: Optional[Union[Permission, str]] = None,
        detail: Optional[str] = None
    ):
        if detail is None:
            if permission:
                perm_str = permission.value if isinstance(permission, Permission) else permission
                detail = f"Permission denied. Required permission: {perm_str}"
            else:
                detail = "Permission denied"

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RoleRequired(HTTPException):
    """Exception raised when user doesn't have required role."""

    def __init__(
        self,
        required_role: Optional[Union[UserRole, str]] = None,
        detail: Optional[str] = None
    ):
        if detail is None:
            if required_role:
                role_str = required_role.value if isinstance(required_role, UserRole) else required_role
                detail = f"Access denied. Required role: {role_str}"
            else:
                detail = "Insufficient role privileges"

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for an endpoint.

    Usage:
        @router.get("/admin/users")
        @require_permission(Permission.USER_READ)
        async def list_users(current_user: User = Depends(get_current_user)):
            ...

    Args:
        permission (Permission): The required permission.

    Returns:
        Callable: Decorated function.

    Raises:
        PermissionDenied: If user doesn't have the required permission.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs (injected by FastAPI Depends)
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user has permission
            if not check_permission(
                role=current_user.role,
                permission=permission,
                extra_permissions=current_user.permissions
            ):
                raise PermissionDenied(permission=permission)

            # Permission granted, execute function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: Union[UserRole, List[UserRole]]):
    """
    Decorator to require a specific role (or one of multiple roles) for an endpoint.

    Usage:
        @router.delete("/admin/users/{user_id}")
        @require_role(UserRole.ADMIN)
        async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
            ...

        # Or require one of multiple roles
        @require_role([UserRole.ADMIN, UserRole.MANAGER])
        async def manage_campaign(...):
            ...

    Args:
        role (Union[UserRole, List[UserRole]]): Required role(s).

    Returns:
        Callable: Decorated function.

    Raises:
        RoleRequired: If user doesn't have the required role.
    """
    # Normalize to list
    required_roles = [role] if isinstance(role, UserRole) else role

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user has required role
            if current_user.role not in required_roles:
                raise RoleRequired(
                    required_role=required_roles[0] if len(required_roles) == 1 else None,
                    detail=f"Access denied. Required role: {', '.join([r.value for r in required_roles])}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permissions(permissions: List[Permission], require_all: bool = True):
    """
    Decorator to require multiple permissions for an endpoint.

    Usage:
        # Require ALL permissions
        @require_permissions([Permission.CAMPAIGN_CREATE, Permission.KOL_READ], require_all=True)
        async def create_campaign_with_kols(...):
            ...

        # Require ANY permission
        @require_permissions([Permission.CAMPAIGN_UPDATE, Permission.CAMPAIGN_MANAGE], require_all=False)
        async def update_campaign(...):
            ...

    Args:
        permissions (List[Permission]): List of required permissions.
        require_all (bool): If True, user must have ALL permissions. If False, ANY permission is enough.

    Returns:
        Callable: Decorated function.

    Raises:
        PermissionDenied: If user doesn't have required permissions.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check permissions
            has_perms = [
                check_permission(
                    role=current_user.role,
                    permission=perm,
                    extra_permissions=current_user.permissions
                )
                for perm in permissions
            ]

            if require_all:
                # Must have ALL permissions
                if not all(has_perms):
                    missing_perms = [p.value for p, has in zip(permissions, has_perms) if not has]
                    raise PermissionDenied(
                        detail=f"Missing required permissions: {', '.join(missing_perms)}"
                    )
            else:
                # Must have ANY permission
                if not any(has_perms):
                    raise PermissionDenied(
                        detail=f"Requires one of: {', '.join([p.value for p in permissions])}"
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_admin(func: Callable):
    """
    Decorator to require admin role for an endpoint.

    Usage:
        @router.post("/admin/system/backup")
        @require_admin
        async def create_backup(current_user: User = Depends(get_current_user)):
            ...

    Returns:
        Callable: Decorated function.

    Raises:
        RoleRequired: If user is not an admin.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if not current_user.is_admin():
            raise RoleRequired(required_role=UserRole.ADMIN)

        return await func(*args, **kwargs)

    return wrapper


class PermissionChecker:
    """
    Helper class for checking permissions in business logic.

    Usage:
        checker = PermissionChecker(current_user)

        if checker.has(Permission.CAMPAIGN_CREATE):
            # Create campaign
            pass

        if checker.has_any([Permission.CAMPAIGN_UPDATE, Permission.CAMPAIGN_MANAGE]):
            # Update campaign
            pass

        if checker.is_admin():
            # Admin-only operation
            pass
    """

    def __init__(self, user: User):
        """
        Initialize permission checker.

        Args:
            user (User): The user to check permissions for.
        """
        self.user = user

    def has(self, permission: Permission) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission (Permission): The permission to check.

        Returns:
            bool: True if user has the permission.
        """
        return check_permission(
            role=self.user.role,
            permission=permission,
            extra_permissions=self.user.permissions
        )

    def has_all(self, permissions: List[Permission]) -> bool:
        """
        Check if user has ALL specified permissions.

        Args:
            permissions (List[Permission]): List of permissions to check.

        Returns:
            bool: True if user has all permissions.
        """
        return all(self.has(perm) for perm in permissions)

    def has_any(self, permissions: List[Permission]) -> bool:
        """
        Check if user has ANY of the specified permissions.

        Args:
            permissions (List[Permission]): List of permissions to check.

        Returns:
            bool: True if user has at least one permission.
        """
        return any(self.has(perm) for perm in permissions)

    def is_role(self, role: Union[UserRole, List[UserRole]]) -> bool:
        """
        Check if user has a specific role.

        Args:
            role (Union[UserRole, List[UserRole]]): Role(s) to check.

        Returns:
            bool: True if user has the role.
        """
        if isinstance(role, list):
            return self.user.role in role
        return self.user.role == role

    def is_admin(self) -> bool:
        """
        Check if user is an admin.

        Returns:
            bool: True if user is an admin.
        """
        return self.user.is_admin()

    def can_manage_user(self, target_user: User) -> bool:
        """
        Check if user can manage another user.

        Rules:
        - Admins can manage anyone
        - Managers can manage non-admins
        - Users cannot manage themselves for critical operations

        Args:
            target_user (User): The user to be managed.

        Returns:
            bool: True if user can manage the target user.
        """
        # Admins can manage anyone
        if self.is_admin():
            return True

        # Managers can manage non-admins
        if self.user.role == UserRole.MANAGER and target_user.role != UserRole.ADMIN:
            return True

        return False

    def can_access_campaign(self, campaign) -> bool:
        """
        Check if user can access a specific campaign.

        Args:
            campaign: Campaign object.

        Returns:
            bool: True if user can access the campaign.
        """
        # Admins and Managers can access all campaigns
        if self.is_role([UserRole.ADMIN, UserRole.MANAGER]):
            return True

        # Check if user created the campaign
        if hasattr(campaign, 'created_by') and campaign.created_by == self.user.id:
            return True

        # Check if user is assigned to the campaign (future feature)
        # if self.user.id in campaign.assigned_users:
        #     return True

        # Check basic read permission
        return self.has(Permission.CAMPAIGN_READ)

    def require(self, permission: Permission) -> None:
        """
        Require a permission, raise exception if not granted.

        Args:
            permission (Permission): The required permission.

        Raises:
            PermissionDenied: If user doesn't have the permission.
        """
        if not self.has(permission):
            raise PermissionDenied(permission=permission)

    def require_any(self, permissions: List[Permission]) -> None:
        """
        Require any of the specified permissions.

        Args:
            permissions (List[Permission]): List of permissions.

        Raises:
            PermissionDenied: If user doesn't have any of the permissions.
        """
        if not self.has_any(permissions):
            raise PermissionDenied(
                detail=f"Requires one of: {', '.join([p.value for p in permissions])}"
            )

    def require_all(self, permissions: List[Permission]) -> None:
        """
        Require all of the specified permissions.

        Args:
            permissions (List[Permission]): List of permissions.

        Raises:
            PermissionDenied: If user doesn't have all permissions.
        """
        if not self.has_all(permissions):
            missing = [p.value for p in permissions if not self.has(p)]
            raise PermissionDenied(
                detail=f"Missing required permissions: {', '.join(missing)}"
            )


def get_permission_checker(current_user: User) -> PermissionChecker:
    """
    Dependency for FastAPI to inject PermissionChecker.

    Usage:
        @router.get("/protected-resource")
        async def get_resource(
            checker: PermissionChecker = Depends(get_permission_checker)
        ):
            checker.require(Permission.RESOURCE_READ)
            # ... rest of endpoint logic

    Args:
        current_user (User): The current authenticated user.

    Returns:
        PermissionChecker: Permission checker instance.
    """
    return PermissionChecker(current_user)


# Utility functions for permission checking in business logic

def check_user_permission(user: User, permission: Permission) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user (User): The user to check.
        permission (Permission): The permission to check.

    Returns:
        bool: True if user has the permission.
    """
    return check_permission(
        role=user.role,
        permission=permission,
        extra_permissions=user.permissions
    )


def enforce_permission(user: User, permission: Permission) -> None:
    """
    Enforce that a user has a specific permission, raise exception if not.

    Args:
        user (User): The user to check.
        permission (Permission): The permission to enforce.

    Raises:
        PermissionDenied: If user doesn't have the permission.
    """
    if not check_user_permission(user, permission):
        raise PermissionDenied(permission=permission)


def can_user_manage_resource(
    user: User,
    resource_owner_id: Optional[int],
    required_permission: Permission
) -> bool:
    """
    Check if user can manage a resource based on ownership and permissions.

    Args:
        user (User): The user attempting to manage the resource.
        resource_owner_id (Optional[int]): The ID of the resource owner.
        required_permission (Permission): The permission required to manage the resource.

    Returns:
        bool: True if user can manage the resource.
    """
    # Admins can manage anything
    if user.is_admin():
        return True

    # Check if user has the required permission
    if not check_user_permission(user, required_permission):
        return False

    # If resource has no owner, permission is enough
    if resource_owner_id is None:
        return True

    # Check if user owns the resource
    if user.id == resource_owner_id:
        return True

    # Managers can manage resources they don't own if they have permission
    if user.role == UserRole.MANAGER:
        return True

    return False
