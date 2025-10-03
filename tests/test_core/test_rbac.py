"""
Unit tests for RBAC (Role-Based Access Control) functionality.

Tests cover:
- Permission checking
- Role-based access
- Permission decorators
- PermissionChecker utility class
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi import HTTPException

from app.core.permissions import Permission, get_role_permissions, has_permission
from app.core.rbac import (
    PermissionChecker,
    PermissionDenied,
    RoleRequired,
    check_user_permission,
    enforce_permission,
    can_user_manage_resource,
    require_permission,
    require_role,
    require_admin
)
from app.models.user import User, UserRole


# Fixtures

@pytest.fixture
def admin_user():
    """Create a mock admin user."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.permissions = []
    user.is_admin = Mock(return_value=True)
    return user


@pytest.fixture
def manager_user():
    """Create a mock manager user."""
    user = Mock(spec=User)
    user.id = 2
    user.email = "manager@example.com"
    user.role = UserRole.MANAGER
    user.permissions = []
    user.is_admin = Mock(return_value=False)
    return user


@pytest.fixture
def coordinator_user():
    """Create a mock coordinator user."""
    user = Mock(spec=User)
    user.id = 3
    user.email = "coordinator@example.com"
    user.role = UserRole.COORDINATOR
    user.permissions = []
    user.is_admin = Mock(return_value=False)
    return user


@pytest.fixture
def analyst_user():
    """Create a mock analyst user."""
    user = Mock(spec=User)
    user.id = 4
    user.email = "analyst@example.com"
    user.role = UserRole.ANALYST
    user.permissions = []
    user.is_admin = Mock(return_value=False)
    return user


@pytest.fixture
def viewer_user():
    """Create a mock viewer user."""
    user = Mock(spec=User)
    user.id = 5
    user.email = "viewer@example.com"
    user.role = UserRole.VIEWER
    user.permissions = []
    user.is_admin = Mock(return_value=False)
    return user


@pytest.fixture
def viewer_with_extra_permission():
    """Create a viewer with extra custom permission."""
    user = Mock(spec=User)
    user.id = 6
    user.email = "special_viewer@example.com"
    user.role = UserRole.VIEWER
    user.permissions = [Permission.CAMPAIGN_CREATE.value]  # Extra permission
    user.is_admin = Mock(return_value=False)
    return user


# Tests for Permission Functions

class TestPermissionFunctions:
    """Test permission utility functions."""

    def test_get_role_permissions_admin(self):
        """Test that admin has all permissions."""
        perms = get_role_permissions(UserRole.ADMIN)
        assert len(perms) > 0
        assert Permission.USER_MANAGE in perms
        assert Permission.CAMPAIGN_MANAGE in perms
        assert Permission.SYSTEM_ADMIN in perms

    def test_get_role_permissions_manager(self):
        """Test manager permissions."""
        perms = get_role_permissions(UserRole.MANAGER)
        assert Permission.CAMPAIGN_CREATE in perms
        assert Permission.KOL_MANAGE in perms
        # Manager should NOT have system admin
        assert Permission.SYSTEM_ADMIN not in perms

    def test_get_role_permissions_viewer(self):
        """Test viewer has minimal permissions."""
        perms = get_role_permissions(UserRole.VIEWER)
        assert Permission.KOL_READ in perms
        assert Permission.CAMPAIGN_READ in perms
        # Viewer should NOT have create permissions
        assert Permission.CAMPAIGN_CREATE not in perms
        assert Permission.KOL_CREATE not in perms

    def test_has_permission_admin_always_true(self):
        """Test that admin always has permission."""
        assert has_permission(UserRole.ADMIN, Permission.CAMPAIGN_CREATE) is True
        assert has_permission(UserRole.ADMIN, Permission.SYSTEM_ADMIN) is True

    def test_has_permission_role_based(self):
        """Test permission checking based on role."""
        assert has_permission(UserRole.MANAGER, Permission.CAMPAIGN_CREATE) is True
        assert has_permission(UserRole.VIEWER, Permission.CAMPAIGN_CREATE) is False

    def test_has_permission_with_extra_permissions(self):
        """Test permission checking with extra permissions."""
        # Viewer normally can't create campaigns
        assert has_permission(UserRole.VIEWER, Permission.CAMPAIGN_CREATE) is False

        # But with extra permission, they can
        extra_perms = [Permission.CAMPAIGN_CREATE.value]
        assert has_permission(UserRole.VIEWER, Permission.CAMPAIGN_CREATE, extra_perms) is True


# Tests for PermissionChecker Class

class TestPermissionChecker:
    """Test PermissionChecker utility class."""

    def test_admin_has_all_permissions(self, admin_user):
        """Test that admin has all permissions."""
        checker = PermissionChecker(admin_user)
        assert checker.has(Permission.CAMPAIGN_CREATE) is True
        assert checker.has(Permission.SYSTEM_ADMIN) is True
        assert checker.is_admin() is True

    def test_manager_permissions(self, manager_user):
        """Test manager permissions."""
        checker = PermissionChecker(manager_user)
        assert checker.has(Permission.CAMPAIGN_CREATE) is True
        assert checker.has(Permission.KOL_MANAGE) is True
        assert checker.has(Permission.SYSTEM_ADMIN) is False
        assert checker.is_admin() is False

    def test_viewer_limited_permissions(self, viewer_user):
        """Test viewer has limited permissions."""
        checker = PermissionChecker(viewer_user)
        assert checker.has(Permission.KOL_READ) is True
        assert checker.has(Permission.CAMPAIGN_CREATE) is False
        assert checker.has(Permission.KOL_DELETE) is False

    def test_has_all_permissions(self, manager_user):
        """Test has_all method."""
        checker = PermissionChecker(manager_user)

        # Manager has both
        assert checker.has_all([
            Permission.CAMPAIGN_CREATE,
            Permission.KOL_READ
        ]) is True

        # Manager doesn't have system admin
        assert checker.has_all([
            Permission.CAMPAIGN_CREATE,
            Permission.SYSTEM_ADMIN
        ]) is False

    def test_has_any_permissions(self, viewer_user):
        """Test has_any method."""
        checker = PermissionChecker(viewer_user)

        # Viewer has read permission
        assert checker.has_any([
            Permission.KOL_READ,
            Permission.CAMPAIGN_CREATE
        ]) is True

        # Viewer has none of these
        assert checker.has_any([
            Permission.KOL_DELETE,
            Permission.CAMPAIGN_DELETE
        ]) is False

    def test_is_role(self, manager_user):
        """Test is_role method."""
        checker = PermissionChecker(manager_user)

        assert checker.is_role(UserRole.MANAGER) is True
        assert checker.is_role(UserRole.ADMIN) is False

        # Test with list
        assert checker.is_role([UserRole.ADMIN, UserRole.MANAGER]) is True
        assert checker.is_role([UserRole.ANALYST, UserRole.VIEWER]) is False

    def test_can_manage_user_admin(self, admin_user, viewer_user):
        """Test admin can manage any user."""
        checker = PermissionChecker(admin_user)
        assert checker.can_manage_user(viewer_user) is True

    def test_can_manage_user_manager(self, manager_user, viewer_user, admin_user):
        """Test manager can manage non-admins."""
        checker = PermissionChecker(manager_user)

        # Manager can manage viewer
        assert checker.can_manage_user(viewer_user) is True

        # Manager cannot manage admin
        assert checker.can_manage_user(admin_user) is False

    def test_require_permission_granted(self, manager_user):
        """Test require method with granted permission."""
        checker = PermissionChecker(manager_user)

        # Should not raise exception
        checker.require(Permission.CAMPAIGN_CREATE)

    def test_require_permission_denied(self, viewer_user):
        """Test require method with denied permission."""
        checker = PermissionChecker(viewer_user)

        # Should raise PermissionDenied
        with pytest.raises(PermissionDenied):
            checker.require(Permission.CAMPAIGN_DELETE)

    def test_require_any_success(self, viewer_user):
        """Test require_any with at least one permission."""
        checker = PermissionChecker(viewer_user)

        # Viewer has KOL_READ
        checker.require_any([
            Permission.KOL_READ,
            Permission.CAMPAIGN_DELETE
        ])

    def test_require_any_failure(self, viewer_user):
        """Test require_any with no permissions."""
        checker = PermissionChecker(viewer_user)

        with pytest.raises(PermissionDenied):
            checker.require_any([
                Permission.KOL_DELETE,
                Permission.CAMPAIGN_DELETE
            ])

    def test_require_all_success(self, manager_user):
        """Test require_all with all permissions."""
        checker = PermissionChecker(manager_user)

        checker.require_all([
            Permission.CAMPAIGN_CREATE,
            Permission.KOL_READ
        ])

    def test_require_all_failure(self, viewer_user):
        """Test require_all with missing permissions."""
        checker = PermissionChecker(viewer_user)

        with pytest.raises(PermissionDenied):
            checker.require_all([
                Permission.KOL_READ,  # Has this
                Permission.KOL_DELETE  # Doesn't have this
            ])

    def test_extra_permissions_viewer(self, viewer_with_extra_permission):
        """Test viewer with extra custom permission."""
        checker = PermissionChecker(viewer_with_extra_permission)

        # Viewer normally can't create campaigns
        # But this user has extra permission
        assert checker.has(Permission.CAMPAIGN_CREATE) is True


# Tests for Utility Functions

class TestUtilityFunctions:
    """Test utility functions for permission checking."""

    def test_check_user_permission(self, manager_user):
        """Test check_user_permission function."""
        assert check_user_permission(manager_user, Permission.CAMPAIGN_CREATE) is True
        assert check_user_permission(manager_user, Permission.SYSTEM_ADMIN) is False

    def test_enforce_permission_granted(self, manager_user):
        """Test enforce_permission with granted permission."""
        # Should not raise exception
        enforce_permission(manager_user, Permission.CAMPAIGN_CREATE)

    def test_enforce_permission_denied(self, viewer_user):
        """Test enforce_permission with denied permission."""
        with pytest.raises(PermissionDenied):
            enforce_permission(viewer_user, Permission.CAMPAIGN_DELETE)

    def test_can_user_manage_resource_admin(self, admin_user):
        """Test admin can manage any resource."""
        # Admin can manage resource regardless of ownership
        assert can_user_manage_resource(
            admin_user,
            resource_owner_id=999,
            required_permission=Permission.CAMPAIGN_UPDATE
        ) is True

    def test_can_user_manage_resource_owner(self, manager_user):
        """Test user can manage their own resource."""
        # Manager owns the resource
        assert can_user_manage_resource(
            manager_user,
            resource_owner_id=manager_user.id,
            required_permission=Permission.CAMPAIGN_UPDATE
        ) is True

    def test_can_user_manage_resource_manager_not_owner(self, manager_user):
        """Test manager can manage resources they don't own."""
        # Manager can manage other people's resources if they have permission
        assert can_user_manage_resource(
            manager_user,
            resource_owner_id=999,
            required_permission=Permission.CAMPAIGN_UPDATE
        ) is True

    def test_can_user_manage_resource_no_permission(self, viewer_user):
        """Test user without permission can't manage resource."""
        assert can_user_manage_resource(
            viewer_user,
            resource_owner_id=999,
            required_permission=Permission.CAMPAIGN_UPDATE
        ) is False


# Tests for Decorators (simulated)

class TestDecorators:
    """Test permission decorators."""

    @pytest.mark.asyncio
    async def test_require_permission_decorator_success(self, manager_user):
        """Test require_permission decorator with granted permission."""

        @require_permission(Permission.CAMPAIGN_CREATE)
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        result = await test_endpoint(current_user=manager_user)
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_require_permission_decorator_denied(self, viewer_user):
        """Test require_permission decorator with denied permission."""

        @require_permission(Permission.CAMPAIGN_DELETE)
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        with pytest.raises(PermissionDenied):
            await test_endpoint(current_user=viewer_user)

    @pytest.mark.asyncio
    async def test_require_role_decorator_success(self, manager_user):
        """Test require_role decorator with correct role."""

        @require_role(UserRole.MANAGER)
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        result = await test_endpoint(current_user=manager_user)
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_require_role_decorator_denied(self, viewer_user):
        """Test require_role decorator with wrong role."""

        @require_role(UserRole.ADMIN)
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        with pytest.raises(RoleRequired):
            await test_endpoint(current_user=viewer_user)

    @pytest.mark.asyncio
    async def test_require_role_decorator_multiple_roles(self, manager_user):
        """Test require_role decorator with multiple allowed roles."""

        @require_role([UserRole.ADMIN, UserRole.MANAGER])
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        result = await test_endpoint(current_user=manager_user)
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_require_admin_decorator_success(self, admin_user):
        """Test require_admin decorator with admin user."""

        @require_admin
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        result = await test_endpoint(current_user=admin_user)
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_require_admin_decorator_denied(self, manager_user):
        """Test require_admin decorator with non-admin user."""

        @require_admin
        async def test_endpoint(current_user: User):
            return {"status": "success"}

        with pytest.raises(RoleRequired):
            await test_endpoint(current_user=manager_user)


# Integration Tests

class TestRBACIntegration:
    """Integration tests for complete RBAC scenarios."""

    def test_campaign_creation_workflow(self, manager_user, viewer_user):
        """Test campaign creation workflow with different users."""
        # Manager should be able to create campaign
        manager_checker = PermissionChecker(manager_user)
        manager_checker.require(Permission.CAMPAIGN_CREATE)  # Should not raise

        # Viewer should not be able to create campaign
        viewer_checker = PermissionChecker(viewer_user)
        with pytest.raises(PermissionDenied):
            viewer_checker.require(Permission.CAMPAIGN_CREATE)

    def test_content_moderation_workflow(self, manager_user, coordinator_user, analyst_user):
        """Test content moderation workflow."""
        # Manager can moderate
        manager_checker = PermissionChecker(manager_user)
        assert manager_checker.has(Permission.CONTENT_MODERATE) is True

        # Coordinator can verify but not moderate
        coordinator_checker = PermissionChecker(coordinator_user)
        assert coordinator_checker.has(Permission.CONTENT_VERIFY) is True
        assert coordinator_checker.has(Permission.CONTENT_MODERATE) is False

        # Analyst can analyze but not moderate
        analyst_checker = PermissionChecker(analyst_user)
        assert analyst_checker.has(Permission.CONTENT_ANALYZE) is True
        assert analyst_checker.has(Permission.CONTENT_MODERATE) is False

    def test_analytics_access_levels(self, manager_user, analyst_user, viewer_user):
        """Test different levels of analytics access."""
        # Manager has advanced analytics
        manager_checker = PermissionChecker(manager_user)
        assert manager_checker.has(Permission.ANALYTICS_ADVANCED) is True
        assert manager_checker.has(Permission.ANALYTICS_EXPORT) is True

        # Analyst has full analytics access
        analyst_checker = PermissionChecker(analyst_user)
        assert analyst_checker.has(Permission.ANALYTICS_ADVANCED) is True
        assert analyst_checker.has(Permission.REPORT_CUSTOMIZE) is True

        # Viewer has basic analytics only
        viewer_checker = PermissionChecker(viewer_user)
        assert viewer_checker.has(Permission.ANALYTICS_VIEW) is True
        assert viewer_checker.has(Permission.ANALYTICS_ADVANCED) is False
