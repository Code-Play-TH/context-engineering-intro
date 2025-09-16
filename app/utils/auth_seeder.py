"""
Authentication Data Seeder

Utility functions for seeding initial authentication data including:
- System roles and permissions
- Default user accounts
- Permission-role assignments
- System configuration
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.auth import User, Role, Permission, UserRole, user_roles, role_permissions
from app.schemas.auth import UserCreate
from app.core.auth import security_service

logger = logging.getLogger(__name__)


class AuthSeeder:
    """Authentication data seeder class."""

    def __init__(self):
        """Initialize the seeder."""
        self.permissions_data = self._get_permissions_data()
        self.roles_data = self._get_roles_data()
        self.default_users_data = self._get_default_users_data()

    async def seed_all(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Seed all authentication data.

        Args:
            db: Database session

        Returns:
            Dict with seeding results
        """
        logger.info("Starting authentication data seeding")

        results = {
            "permissions": await self.seed_permissions(db),
            "roles": await self.seed_roles(db),
            "role_permissions": await self.assign_permissions_to_roles(db),
            "default_users": await self.seed_default_users(db)
        }

        logger.info("Authentication data seeding completed")
        return results

    async def seed_permissions(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Seed system permissions.

        Args:
            db: Database session

        Returns:
            Dict with seeding results
        """
        logger.info("Seeding permissions")

        created_count = 0
        updated_count = 0

        for perm_data in self.permissions_data:
            # Check if permission exists
            stmt = select(Permission).where(Permission.name == perm_data["name"])
            existing_perm = await db.execute(stmt)
            permission = existing_perm.scalar_one_or_none()

            if permission:
                # Update existing permission
                permission.display_name = perm_data.get("display_name")
                permission.description = perm_data.get("description")
                permission.resource = perm_data.get("resource")
                permission.action = perm_data.get("action")
                permission.scope = perm_data.get("scope")
                permission.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new permission
                permission = Permission(
                    name=perm_data["name"],
                    display_name=perm_data.get("display_name"),
                    description=perm_data.get("description"),
                    resource=perm_data.get("resource"),
                    action=perm_data.get("action"),
                    scope=perm_data.get("scope"),
                    is_system_permission=True
                )
                db.add(permission)
                created_count += 1

        await db.commit()

        logger.info(f"Permissions seeded: {created_count} created, {updated_count} updated")
        return {"created": created_count, "updated": updated_count}

    async def seed_roles(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Seed system roles.

        Args:
            db: Database session

        Returns:
            Dict with seeding results
        """
        logger.info("Seeding roles")

        created_count = 0
        updated_count = 0

        for role_data in self.roles_data:
            # Check if role exists
            stmt = select(Role).where(Role.name == role_data["name"])
            existing_role = await db.execute(stmt)
            role = existing_role.scalar_one_or_none()

            if role:
                # Update existing role
                role.display_name = role_data.get("display_name")
                role.description = role_data.get("description")
                role.level = role_data.get("level", 0)
                role.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new role
                role = Role(
                    name=role_data["name"],
                    display_name=role_data.get("display_name"),
                    description=role_data.get("description"),
                    level=role_data.get("level", 0),
                    is_system_role=True
                )
                db.add(role)
                created_count += 1

        await db.commit()

        logger.info(f"Roles seeded: {created_count} created, {updated_count} updated")
        return {"created": created_count, "updated": updated_count}

    async def assign_permissions_to_roles(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Assign permissions to roles based on predefined mappings.

        Args:
            db: Database session

        Returns:
            Dict with assignment results
        """
        logger.info("Assigning permissions to roles")

        # Permission-role mappings
        role_permission_mappings = {
            "super_admin": ["*"],  # All permissions
            "admin": [
                "users.*", "roles.*", "permissions.*", "kols.*",
                "campaigns.*", "analytics.*", "content_monitoring.*",
                "communications.*", "calendar.*"
            ],
            "manager": [
                "kols.read", "kols.create", "kols.update",
                "campaigns.*", "analytics.read", "content_monitoring.read",
                "communications.*", "calendar.*"
            ],
            "analyst": [
                "kols.read", "campaigns.read", "analytics.*",
                "content_monitoring.read", "calendar.read"
            ],
            "viewer": [
                "kols.read", "campaigns.read", "analytics.read",
                "content_monitoring.read", "calendar.read"
            ],
            "kol": [
                "profile.read", "profile.update", "campaigns.read",
                "calendar.read", "content.create", "content.read"
            ],
            "client": [
                "campaigns.read", "analytics.read", "calendar.read"
            ]
        }

        assignments_made = 0

        for role_name, permission_patterns in role_permission_mappings.items():
            # Get role
            role_stmt = select(Role).where(Role.name == role_name)
            role_result = await db.execute(role_stmt)
            role = role_result.scalar_one_or_none()

            if not role:
                logger.warning(f"Role '{role_name}' not found for permission assignment")
                continue

            # Get permissions based on patterns
            permissions_to_assign = []

            for pattern in permission_patterns:
                if pattern == "*":
                    # Assign all permissions
                    all_perms_stmt = select(Permission).where(Permission.is_active == True)
                    all_perms_result = await db.execute(all_perms_stmt)
                    permissions_to_assign.extend(all_perms_result.scalars().all())
                elif pattern.endswith(".*"):
                    # Assign all permissions for a resource
                    resource = pattern[:-2]
                    resource_perms_stmt = select(Permission).where(
                        and_(
                            Permission.resource == resource,
                            Permission.is_active == True
                        )
                    )
                    resource_perms_result = await db.execute(resource_perms_stmt)
                    permissions_to_assign.extend(resource_perms_result.scalars().all())
                else:
                    # Assign specific permission
                    perm_stmt = select(Permission).where(
                        and_(
                            Permission.name == pattern,
                            Permission.is_active == True
                        )
                    )
                    perm_result = await db.execute(perm_stmt)
                    perm = perm_result.scalar_one_or_none()
                    if perm:
                        permissions_to_assign.append(perm)

            # Remove duplicates
            unique_permissions = list(set(permissions_to_assign))

            # Clear existing role permissions first
            await db.execute(
                role_permissions.delete().where(role_permissions.c.role_id == role.id)
            )

            # Assign permissions to role
            for permission in unique_permissions:
                # Check if assignment already exists
                existing_stmt = select(role_permissions).where(
                    and_(
                        role_permissions.c.role_id == role.id,
                        role_permissions.c.permission_id == permission.id
                    )
                )
                existing_result = await db.execute(existing_stmt)

                if not existing_result.first():
                    # Create new assignment
                    await db.execute(
                        role_permissions.insert().values(
                            role_id=role.id,
                            permission_id=permission.id,
                            granted_at=datetime.utcnow()
                        )
                    )
                    assignments_made += 1

        await db.commit()

        logger.info(f"Role-permission assignments completed: {assignments_made} assignments made")
        return {"assignments_made": assignments_made}

    async def seed_default_users(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Seed default system users.

        Args:
            db: Database session

        Returns:
            Dict with seeding results
        """
        logger.info("Seeding default users")

        created_count = 0
        updated_count = 0

        for user_data in self.default_users_data:
            # Check if user exists
            stmt = select(User).where(User.email == user_data["email"])
            existing_user = await db.execute(stmt)
            user = existing_user.scalar_one_or_none()

            if user:
                logger.info(f"User {user_data['email']} already exists, skipping")
                continue

            # Create new user
            hashed_password = security_service.hash_password(user_data["password"])

            user = User(
                email=user_data["email"],
                username=user_data.get("username"),
                hashed_password=hashed_password,
                full_name=user_data.get("full_name"),
                is_active=True,
                is_verified=True,
                is_superuser=user_data.get("is_superuser", False),
                status=user_data.get("status", "active")
            )
            db.add(user)
            await db.flush()  # Get user ID

            # Assign roles to user
            role_names = user_data.get("roles", [])
            for role_name in role_names:
                role_stmt = select(Role).where(Role.name == role_name)
                role_result = await db.execute(role_stmt)
                role = role_result.scalar_one_or_none()

                if role:
                    await db.execute(
                        user_roles.insert().values(
                            user_id=user.id,
                            role_id=role.id,
                            assigned_at=datetime.utcnow()
                        )
                    )

            created_count += 1

        await db.commit()

        logger.info(f"Default users seeded: {created_count} created")
        return {"created": created_count}

    def _get_permissions_data(self) -> List[Dict[str, Any]]:
        """Get permissions data for seeding."""
        return [
            # User Management
            {"name": "users.create", "display_name": "Create Users", "description": "Create new user accounts", "resource": "users", "action": "create", "scope": "all"},
            {"name": "users.read", "display_name": "Read Users", "description": "View user information", "resource": "users", "action": "read", "scope": "all"},
            {"name": "users.update", "display_name": "Update Users", "description": "Update user information", "resource": "users", "action": "update", "scope": "all"},
            {"name": "users.delete", "display_name": "Delete Users", "description": "Delete user accounts", "resource": "users", "action": "delete", "scope": "all"},

            # Role Management
            {"name": "roles.create", "display_name": "Create Roles", "description": "Create new roles", "resource": "roles", "action": "create", "scope": "all"},
            {"name": "roles.read", "display_name": "Read Roles", "description": "View role information", "resource": "roles", "action": "read", "scope": "all"},
            {"name": "roles.update", "display_name": "Update Roles", "description": "Update role information", "resource": "roles", "action": "update", "scope": "all"},
            {"name": "roles.delete", "display_name": "Delete Roles", "description": "Delete roles", "resource": "roles", "action": "delete", "scope": "all"},

            # Permission Management
            {"name": "permissions.create", "display_name": "Create Permissions", "description": "Create new permissions", "resource": "permissions", "action": "create", "scope": "all"},
            {"name": "permissions.read", "display_name": "Read Permissions", "description": "View permission information", "resource": "permissions", "action": "read", "scope": "all"},
            {"name": "permissions.update", "display_name": "Update Permissions", "description": "Update permission information", "resource": "permissions", "action": "update", "scope": "all"},
            {"name": "permissions.delete", "display_name": "Delete Permissions", "description": "Delete permissions", "resource": "permissions", "action": "delete", "scope": "all"},

            # KOL Management
            {"name": "kols.create", "display_name": "Create KOLs", "description": "Create new KOL profiles", "resource": "kols", "action": "create", "scope": "all"},
            {"name": "kols.read", "display_name": "Read KOLs", "description": "View KOL information", "resource": "kols", "action": "read", "scope": "all"},
            {"name": "kols.update", "display_name": "Update KOLs", "description": "Update KOL information", "resource": "kols", "action": "update", "scope": "all"},
            {"name": "kols.delete", "display_name": "Delete KOLs", "description": "Delete KOL profiles", "resource": "kols", "action": "delete", "scope": "all"},

            # Campaign Management
            {"name": "campaigns.create", "display_name": "Create Campaigns", "description": "Create new campaigns", "resource": "campaigns", "action": "create", "scope": "all"},
            {"name": "campaigns.read", "display_name": "Read Campaigns", "description": "View campaign information", "resource": "campaigns", "action": "read", "scope": "all"},
            {"name": "campaigns.update", "display_name": "Update Campaigns", "description": "Update campaign information", "resource": "campaigns", "action": "update", "scope": "all"},
            {"name": "campaigns.delete", "display_name": "Delete Campaigns", "description": "Delete campaigns", "resource": "campaigns", "action": "delete", "scope": "all"},

            # Analytics
            {"name": "analytics.read", "display_name": "Read Analytics", "description": "View analytics and reports", "resource": "analytics", "action": "read", "scope": "all"},
            {"name": "analytics.export", "display_name": "Export Analytics", "description": "Export analytics data", "resource": "analytics", "action": "export", "scope": "all"},

            # Content Monitoring
            {"name": "content_monitoring.read", "display_name": "Read Content Monitoring", "description": "View content monitoring data", "resource": "content_monitoring", "action": "read", "scope": "all"},
            {"name": "content_monitoring.analyze", "display_name": "Analyze Content", "description": "Perform content analysis", "resource": "content_monitoring", "action": "analyze", "scope": "all"},

            # Communications
            {"name": "communications.send", "display_name": "Send Communications", "description": "Send messages and communications", "resource": "communications", "action": "send", "scope": "all"},
            {"name": "communications.read", "display_name": "Read Communications", "description": "View communication history", "resource": "communications", "action": "read", "scope": "all"},

            # Calendar
            {"name": "calendar.create", "display_name": "Create Calendar Events", "description": "Create calendar events", "resource": "calendar", "action": "create", "scope": "all"},
            {"name": "calendar.read", "display_name": "Read Calendar", "description": "View calendar events", "resource": "calendar", "action": "read", "scope": "all"},
            {"name": "calendar.update", "display_name": "Update Calendar Events", "description": "Update calendar events", "resource": "calendar", "action": "update", "scope": "all"},
            {"name": "calendar.delete", "display_name": "Delete Calendar Events", "description": "Delete calendar events", "resource": "calendar", "action": "delete", "scope": "all"},

            # Profile Management (for KOLs)
            {"name": "profile.read", "display_name": "Read Profile", "description": "View own profile", "resource": "profile", "action": "read", "scope": "own"},
            {"name": "profile.update", "display_name": "Update Profile", "description": "Update own profile", "resource": "profile", "action": "update", "scope": "own"},

            # Content Creation (for KOLs)
            {"name": "content.create", "display_name": "Create Content", "description": "Create content submissions", "resource": "content", "action": "create", "scope": "own"},
            {"name": "content.read", "display_name": "Read Content", "description": "View content submissions", "resource": "content", "action": "read", "scope": "own"}
        ]

    def _get_roles_data(self) -> List[Dict[str, Any]]:
        """Get roles data for seeding."""
        return [
            {"name": "super_admin", "display_name": "Super Administrator", "description": "Full system access with all permissions", "level": 100},
            {"name": "admin", "display_name": "Administrator", "description": "Administrative access to most system features", "level": 90},
            {"name": "manager", "display_name": "Manager", "description": "Management access to KOL and campaign operations", "level": 70},
            {"name": "analyst", "display_name": "Analyst", "description": "Read access with analytics capabilities", "level": 50},
            {"name": "viewer", "display_name": "Viewer", "description": "Read-only access to system data", "level": 30},
            {"name": "kol", "display_name": "KOL", "description": "Key Opinion Leader with content creation access", "level": 40},
            {"name": "client", "display_name": "Client", "description": "Client access to campaign and analytics data", "level": 20}
        ]

    def _get_default_users_data(self) -> List[Dict[str, Any]]:
        """Get default users data for seeding."""
        return [
            {
                "email": "admin@kolsystem.com",
                "username": "admin",
                "password": "AdminPassword123!",
                "full_name": "System Administrator",
                "is_superuser": True,
                "status": "active",
                "roles": ["super_admin"]
            },
            {
                "email": "manager@kolsystem.com",
                "username": "manager",
                "password": "ManagerPassword123!",
                "full_name": "System Manager",
                "is_superuser": False,
                "status": "active",
                "roles": ["manager"]
            }
        ]


# Utility functions
async def seed_auth_data() -> Dict[str, Any]:
    """
    Seed authentication data using the default session.

    Returns:
        Dict with seeding results
    """
    async with get_session() as db:
        seeder = AuthSeeder()
        return await seeder.seed_all(db)


async def seed_permissions_only() -> Dict[str, Any]:
    """
    Seed only permissions.

    Returns:
        Dict with seeding results
    """
    async with get_session() as db:
        seeder = AuthSeeder()
        return await seeder.seed_permissions(db)


async def seed_roles_only() -> Dict[str, Any]:
    """
    Seed only roles.

    Returns:
        Dict with seeding results
    """
    async with get_session() as db:
        seeder = AuthSeeder()
        return await seeder.seed_roles(db)


async def assign_permissions_only() -> Dict[str, Any]:
    """
    Assign permissions to roles only.

    Returns:
        Dict with assignment results
    """
    async with get_session() as db:
        seeder = AuthSeeder()
        return await seeder.assign_permissions_to_roles(db)