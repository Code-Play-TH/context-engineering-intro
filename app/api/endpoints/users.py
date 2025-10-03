"""
User Management API Endpoints

Provides comprehensive API endpoints for user management:
- CRUD operations for user profiles
- User role and permission management
- User status management (activate, deactivate, suspend)
- Bulk user operations
- User analytics and reporting
- User session management
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

from app.core.database import get_session
from app.core.auth import get_current_user, get_current_superuser
from app.models.user import User, UserRole, UserStatus, UserSession, AuditLog
from app.schemas.users import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserSearchFilters, UserStatusUpdate, UserRoleUpdate,
    UserBulkAction, UserAnalytics, UserSessionResponse,
    UserAuditLogResponse, UserDetailedResponse, UserPreferencesUpdate
)
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
) -> UserResponse:
    """
    Create a new user (admin only).

    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated superuser

    Returns:
        Created user profile
    """
    try:
        # Check if user with email already exists
        existing_query = select(User).where(User.email == user_data.email)
        existing_result = await db.execute(existing_query)
        existing_user = existing_result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Check if username is taken (if provided)
        if user_data.username:
            username_query = select(User).where(User.username == user_data.username)
            username_result = await db.execute(username_query)
            existing_username = username_result.scalar_one_or_none()

            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        # Create user instance
        user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            full_name=user_data.full_name or f"{user_data.first_name} {user_data.last_name}",
            phone=user_data.phone,
            bio=user_data.bio,
            role=user_data.role or UserRole.VIEWER,
            status=user_data.status or UserStatus.ACTIVE,
            is_active=user_data.is_active if user_data.is_active is not None else True,
            is_verified=user_data.is_verified if user_data.is_verified is not None else False,
            timezone=user_data.timezone or "UTC",
            language=user_data.language or "en",
            permissions=user_data.permissions or [],
            preferences=user_data.preferences or {},
            created_by=current_user.id
        )

        # Set password if provided
        if user_data.password:
            user.set_password(user_data.password)
        else:
            # Generate temporary password for admin-created users
            import secrets
            temp_password = secrets.token_urlsafe(12)
            user.set_password(temp_password)
            # In production, send password reset email

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"User created successfully by admin: {user.id}")
        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    filters: UserSearchFilters = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> UserListResponse:
    """
    List users with filtering and pagination.

    Args:
        pagination: Pagination parameters
        filters: Search and filter parameters
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of users
    """
    try:
        # Check permissions
        if not current_user.can_manage_users() and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view users"
            )

        # Build base query
        query = select(User)

        # Apply filters
        if filters.status:
            query = query.where(User.status.in_(filters.status))

        if filters.role:
            query = query.where(User.role.in_(filters.role))

        if filters.is_active is not None:
            query = query.where(User.is_active == filters.is_active)

        if filters.is_verified is not None:
            query = query.where(User.is_verified == filters.is_verified)

        if filters.created_after:
            query = query.where(User.created_at >= filters.created_after)

        if filters.created_before:
            query = query.where(User.created_at <= filters.created_before)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )

        # Apply sorting
        if filters.sort_by:
            if filters.sort_by == "name":
                order_column = User.full_name
            elif filters.sort_by == "email":
                order_column = User.email
            elif filters.sort_by == "role":
                order_column = User.role
            elif filters.sort_by == "status":
                order_column = User.status
            elif filters.sort_by == "last_login":
                order_column = User.last_login_at
            else:
                order_column = User.created_at

            if filters.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(User.created_at.desc())

        # Execute paginated query
        result = await paginate_query(query, db, pagination.page, pagination.limit)

        return UserListResponse(
            users=[UserResponse.model_validate(user) for user in result.items],
            total=result.total,
            page=result.page,
            limit=result.limit,
            pages=result.pages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=UserDetailedResponse)
async def get_user(
    user_id: int = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> UserDetailedResponse:
    """
    Get specific user by ID.

    Args:
        user_id: User identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        User profile details
    """
    try:
        # Check permissions - users can view their own profile or admins can view any
        if current_user.id != user_id and not current_user.can_manage_users():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this user"
            )

        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user sessions (last 10)
        sessions_query = select(UserSession).where(
            UserSession.user_id == user_id
        ).order_by(desc(UserSession.created_at)).limit(10)
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        # Get recent audit logs (last 20) if admin
        audit_logs = []
        if current_user.can_manage_users():
            audit_query = select(AuditLog).where(
                AuditLog.user_id == user_id
            ).order_by(desc(AuditLog.created_at)).limit(20)
            audit_result = await db.execute(audit_query)
            audit_logs = audit_result.scalars().all()

        return UserDetailedResponse(
            **user.__dict__,
            recent_sessions=[UserSessionResponse.model_validate(session) for session in sessions],
            recent_audit_logs=[UserAuditLogResponse.model_validate(log) for log in audit_logs] if current_user.can_manage_users() else []
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int = Path(..., description="User ID"),
    user_data: UserUpdate = ...,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Update user profile.

    Args:
        user_id: User identifier
        user_data: Updated user data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user profile
    """
    try:
        # Check permissions
        if current_user.id != user_id and not current_user.can_manage_users():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this user"
            )

        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Store old values for audit log
        old_values = {
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "status": user.status,
            "is_active": user.is_active
        }

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email" and value != user.email:
                # Check if new email is already taken
                email_query = select(User).where(User.email == value, User.id != user_id)
                email_result = await db.execute(email_query)
                if email_result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already taken"
                    )

            if field == "username" and value and value != user.username:
                # Check if new username is already taken
                username_query = select(User).where(User.username == value, User.id != user_id)
                username_result = await db.execute(username_query)
                if username_result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )

            # Only allow admins to change role and certain fields
            admin_only_fields = ["role", "status", "is_verified", "permissions"]
            if field in admin_only_fields and not current_user.can_manage_users():
                continue

            if field == "preferences" and value:
                # Merge with existing preferences
                user.preferences = {**(user.preferences or {}), **value}
            else:
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        # Create audit log entry
        new_values = {field: getattr(user, field) for field in old_values.keys()}
        changed_fields = {field: {"old": old_values[field], "new": new_values[field]}
                         for field in old_values.keys()
                         if old_values[field] != new_values[field]}

        if changed_fields:
            audit_log = AuditLog(
                user_id=current_user.id,
                action="user_update",
                resource_type="user",
                resource_id=str(user_id),
                description=f"User profile updated by {'self' if current_user.id == user_id else 'admin'}",
                old_values=old_values,
                new_values=new_values,
                metadata={"changed_fields": list(changed_fields.keys())}
            )
            db.add(audit_log)

        await db.commit()
        await db.refresh(user)

        logger.info(f"User updated successfully: {user.id}")
        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete user (soft delete for admin users).

    Args:
        user_id: User identifier
        db: Database session
        current_user: Current authenticated superuser
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prevent deletion of own account
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Soft delete - deactivate and mark as deleted
        user.is_active = False
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.utcnow()

        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action="user_delete",
            resource_type="user",
            resource_id=str(user_id),
            description=f"User deleted by admin",
            old_values={"is_active": True, "status": user.status},
            new_values={"is_active": False, "status": UserStatus.INACTIVE}
        )
        db.add(audit_log)

        await db.commit()

        logger.info(f"User deleted successfully: {user.id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int = Path(..., description="User ID"),
    status_update: UserStatusUpdate = ...,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
) -> UserResponse:
    """
    Update user status (admin only).

    Args:
        user_id: User identifier
        status_update: Status update data
        db: Database session
        current_user: Current authenticated superuser

    Returns:
        Updated user profile
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        old_status = user.status
        old_is_active = user.is_active

        # Update status
        user.status = status_update.status
        user.is_active = status_update.is_active
        user.updated_at = datetime.utcnow()

        # Handle suspension with expiry
        if status_update.status == UserStatus.SUSPENDED and status_update.suspension_expires_at:
            user.metadata = user.metadata or {}
            user.metadata["suspension_expires_at"] = status_update.suspension_expires_at.isoformat()

        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action="user_status_change",
            resource_type="user",
            resource_id=str(user_id),
            description=f"User status changed from {old_status} to {status_update.status}",
            old_values={"status": old_status, "is_active": old_is_active},
            new_values={"status": status_update.status, "is_active": status_update.is_active},
            metadata={"reason": status_update.reason}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(user)

        logger.info(f"User status updated: {user.id} to {status_update.status}")
        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user status {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int = Path(..., description="User ID"),
    role_update: UserRoleUpdate = ...,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
) -> UserResponse:
    """
    Update user role and permissions (admin only).

    Args:
        user_id: User identifier
        role_update: Role update data
        db: Database session
        current_user: Current authenticated superuser

    Returns:
        Updated user profile
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        old_role = user.role
        old_permissions = user.permissions

        # Update role and permissions
        user.role = role_update.role
        if role_update.permissions is not None:
            user.permissions = role_update.permissions
        user.updated_at = datetime.utcnow()

        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action="user_role_change",
            resource_type="user",
            resource_id=str(user_id),
            description=f"User role changed from {old_role} to {role_update.role}",
            old_values={"role": old_role, "permissions": old_permissions},
            new_values={"role": role_update.role, "permissions": user.permissions},
            metadata={"reason": role_update.reason}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(user)

        logger.info(f"User role updated: {user.id} to {role_update.role}")
        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user role {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )


@router.post("/bulk-action", response_model=Dict[str, Any])
async def bulk_user_action(
    bulk_action: UserBulkAction = ...,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """
    Perform bulk actions on multiple users (admin only).

    Args:
        bulk_action: Bulk action data
        db: Database session
        current_user: Current authenticated superuser

    Returns:
        Bulk action results
    """
    results = {
        "success_count": 0,
        "failed_count": 0,
        "failed_users": [],
        "updated_users": []
    }

    try:
        for user_id in bulk_action.user_ids:
            try:
                # Prevent actions on own account
                if user_id == current_user.id:
                    results["failed_count"] += 1
                    results["failed_users"].append({
                        "user_id": user_id,
                        "error": "Cannot perform bulk action on your own account"
                    })
                    continue

                # Get user
                query = select(User).where(User.id == user_id)
                result = await db.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    results["failed_count"] += 1
                    results["failed_users"].append({
                        "user_id": user_id,
                        "error": "User not found"
                    })
                    continue

                # Apply action
                if bulk_action.action == "activate":
                    user.is_active = True
                    user.status = UserStatus.ACTIVE
                elif bulk_action.action == "deactivate":
                    user.is_active = False
                    user.status = UserStatus.INACTIVE
                elif bulk_action.action == "suspend":
                    user.status = UserStatus.SUSPENDED
                    user.is_active = False
                elif bulk_action.action == "verify":
                    user.is_verified = True
                elif bulk_action.action == "unverify":
                    user.is_verified = False
                else:
                    results["failed_count"] += 1
                    results["failed_users"].append({
                        "user_id": user_id,
                        "error": f"Unknown action: {bulk_action.action}"
                    })
                    continue

                user.updated_at = datetime.utcnow()

                # Create audit log
                audit_log = AuditLog(
                    user_id=current_user.id,
                    action=f"bulk_{bulk_action.action}",
                    resource_type="user",
                    resource_id=str(user_id),
                    description=f"Bulk action '{bulk_action.action}' applied to user",
                    metadata={"reason": bulk_action.reason}
                )
                db.add(audit_log)

                results["success_count"] += 1
                results["updated_users"].append(user_id)

            except Exception as e:
                results["failed_count"] += 1
                results["failed_users"].append({
                    "user_id": user_id,
                    "error": str(e)
                })

        await db.commit()

        logger.info(f"Bulk user action completed: {results['success_count']} success, {results['failed_count']} failed")
        return results

    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk user action failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk action operation failed"
        )


@router.get("/analytics/summary", response_model=UserAnalytics)
async def get_user_analytics(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
) -> UserAnalytics:
    """
    Get user analytics and statistics (admin only).

    Args:
        db: Database session
        current_user: Current authenticated superuser

    Returns:
        User analytics data
    """
    try:
        # Total user counts by status
        status_query = select(
            User.status,
            func.count(User.id).label('count')
        ).group_by(User.status)
        status_result = await db.execute(status_query)
        status_counts = {row.status: row.count for row in status_result}

        # Role distribution
        role_query = select(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role)
        role_result = await db.execute(role_query)
        role_distribution = {row.role: row.count for row in role_result}

        # Registration trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_query = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
        recent_result = await db.execute(recent_query)
        recent_registrations = recent_result.scalar() or 0

        # Active users (logged in within last 30 days)
        active_query = select(func.count(User.id)).where(
            and_(
                User.last_login_at >= thirty_days_ago,
                User.is_active == True
            )
        )
        active_result = await db.execute(active_query)
        active_users = active_result.scalar() or 0

        # Total counts
        total_users = sum(status_counts.values())
        verified_users = await db.scalar(select(func.count(User.id)).where(User.is_verified == True)) or 0

        return UserAnalytics(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            status_distribution=status_counts,
            role_distribution=role_distribution,
            recent_registrations=recent_registrations,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to get user analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user analytics"
        )