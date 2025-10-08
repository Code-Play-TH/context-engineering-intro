"""User management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.core.database import get_session
from app.core.auth import get_current_user
from app.services.user_service import UserService
from app.services.permission_service import PermissionService
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.models.user import User
from app.models.enums import Role


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user (Admin only).
    """
    PermissionService.require_permission(current_user.role, "users", "create")
    
    user_service = UserService(db)
    user = user_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=Role(user_data.role)
    )
    
    return user


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List users with pagination and filters (Admin only).
    """
    PermissionService.require_permission(current_user.role, "users", "read")
    
    user_service = UserService(db)
    skip = (page - 1) * page_size
    
    role_enum = Role(role) if role else None
    users, total = user_service.list_users(
        skip=skip,
        limit=page_size,
        role=role_enum,
        is_active=is_active
    )
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get user details.
    """
    PermissionService.require_permission(current_user.role, "users", "read")
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update user information.
    """
    PermissionService.require_permission(current_user.role, "users", "update")
    
    user_service = UserService(db)
    user = user_service.update_user(
        user_id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        role=Role(user_data.role) if user_data.role else None,
        is_active=user_data.is_active
    )
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate user (soft delete, Admin only).
    """
    PermissionService.require_permission(current_user.role, "users", "delete")
    
    user_service = UserService(db)
    user_service.deactivate_user(user_id)
    
    return None
