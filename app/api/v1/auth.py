"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.core.auth import get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest
)
from app.schemas.user import UserResponse
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_session)
):
    """
    Login with email and password.
    
    Returns access token and refresh token.
    """
    auth_service = AuthService(db)
    access_token, refresh_token, user = auth_service.login(
        email=request.email,
        password=request.password
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_session)
):
    """
    Refresh access token using refresh token.
    
    Returns new access token and refresh token (token rotation).
    """
    auth_service = AuthService(db)
    new_access_token, new_refresh_token = auth_service.refresh_token(
        refresh_token=request.refresh_token
    )
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_session)
):
    """
    Logout by revoking refresh token.
    """
    auth_service = AuthService(db)
    auth_service.logout(refresh_token=request.refresh_token)
    return None


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    return current_user
@router.post("/password-reset")
def request_password_reset(
    email_data: dict,
    db: Session = Depends(get_session)
):
    """
    Request password reset token.
    """
    email = email_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    auth_service = AuthService(db)
    
    try:
        reset_token = auth_service.request_password_reset(email)
        
        # In production, don't return the token
        # Just return success message after sending email
        return {
            "message": "If the email exists, a password reset link has been sent",
            "reset_token": reset_token  # Remove this in production
        }
    except HTTPException:
        # Always return the same message to prevent email enumeration
        return {
            "message": "If the email exists, a password reset link has been sent"
        }


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: dict,
    db: Session = Depends(get_session)
):
    """
    Confirm password reset with token and new password.
    """
    token = reset_data.get("token")
    new_password = reset_data.get("new_password")
    
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    auth_service = AuthService(db)
    user = auth_service.confirm_password_reset(token, new_password)
    
    return {
        "message": "Password reset successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }