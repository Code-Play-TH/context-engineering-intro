"""
Authentication API endpoints.

Handles user login, logout, token refresh, and password management.
"""

from datetime import timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import (
    get_db,
    get_current_active_user,
    get_current_user_info,
    create_access_token,
)
from app.config import get_settings
from app.models.user import User, Department, Role
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    Token,
    UserResponse,
    CurrentUser,
    UserChangePassword,
)

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    User login endpoint.
    
    Authenticates user credentials and returns JWT token with user information.
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        LoginResponse: Access token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user (without joins first to avoid complexity)
    statement = (
        select(User)
        .where(User.username == login_data.username, User.is_active == True)
    )
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Load related data
    await db.refresh(user, ["department", "role"])
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "department": user.department.code if user.department else "unknown",
        "role": user.role.code if user.role else "user",
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.update_last_login()
    await db.commit()
    await db.refresh(user)
    
    # Prepare user response
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        role_id=user.role_id,
        is_superuser=user.is_superuser,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        department=user.department,
        role=user.role
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_response
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
) -> Token:
    """
    Refresh access token.
    
    Generates a new access token for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Token: New access token
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token_data = {
        "sub": current_user.username,
        "user_id": current_user.id,
        "department": current_user.department.code,
        "role": current_user.role.code,
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """
    User logout endpoint.
    
    Note: JWT tokens are stateless, so logout is mainly for client-side cleanup.
    In a production environment, you might want to maintain a blacklist of tokens.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Logout confirmation message
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=CurrentUser)
async def get_current_user_profile(
    current_user_info: CurrentUser = Depends(get_current_user_info)
) -> CurrentUser:
    """
    Get current user profile information.
    
    Args:
        current_user_info: Current user information
        
    Returns:
        CurrentUser: User profile data
    """
    return current_user_info


@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Change user password.
    
    Args:
        password_data: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Set new password
    current_user.set_password(password_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/verify-token")
async def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """
    Verify if the current token is valid.
    
    This endpoint can be used by frontend applications to check
    if the user's token is still valid.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Token verification result
    """
    return {
        "message": "Token is valid",
        "username": current_user.username,
        "department": current_user.department.code
    }


@router.get("/permissions")
async def get_user_permissions(
    current_user_info: CurrentUser = Depends(get_current_user_info)
) -> Dict[str, Any]:
    """
    Get current user's permissions.
    
    Args:
        current_user_info: Current user information
        
    Returns:
        dict: User permissions and access levels
    """
    return {
        "user_id": current_user_info.id,
        "username": current_user_info.username,
        "department": current_user_info.department_code,
        "role": current_user_info.role_code,
        "is_superuser": current_user_info.is_superuser,
        "permissions": current_user_info.permissions
    }