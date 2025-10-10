"""Authentication service for login, token refresh, and logout."""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password
)


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def login(self, email: str, password: str) -> Tuple[str, str, User]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        statement = select(User).where(User.email == email)
        user = self.db.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Create tokens
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role  # role is already a string
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
        
        # Store refresh token in database
        refresh_token_hash = hash_password(refresh_token)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(db_refresh_token)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        self.db.add(user)
        
        self.db.commit()
        
        return access_token, refresh_token, user
    
    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token with rotation.
        
        Args:
            refresh_token: Current refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        
        # Get user
        user = self.db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Revoke old refresh token
        refresh_token_hash = hash_password(refresh_token)
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        )
        old_tokens = self.db.exec(statement).all()
        for token in old_tokens:
            token.revoked = True
            self.db.add(token)
        
        # Create new tokens
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role  # role is already a string
        }
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
        
        # Store new refresh token
        new_refresh_token_hash = hash_password(new_refresh_token)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(db_refresh_token)
        
        self.db.commit()
        
        return new_access_token, new_refresh_token
    
    def logout(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        
        # Revoke all refresh tokens for user
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        )
        tokens = self.db.exec(statement).all()
        for token in tokens:
            token.revoked = True
            self.db.add(token)
        
        self.db.commit()
    
    def request_password_reset(self, email: str) -> str:
        """
        Generate password reset token for user.
        
        Args:
            email: User email
            
        Returns:
            Password reset token
            
        Raises:
            HTTPException: If user not found
        """
        # Get user by email
        statement = select(User).where(User.email == email)
        user = self.db.exec(statement).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            # But still return a token format to prevent email enumeration
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="If the email exists, a password reset link has been sent"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )
        
        # Create reset token (1 hour expiry)
        reset_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=1)
        )
        
        # TODO: Send email with reset link
        # For now, we'll just return the token
        # In production, you would:
        # 1. Generate reset link: f"https://yourapp.com/reset-password?token={reset_token}"
        # 2. Send email with the link
        # 3. Return success message without the token
        
        return reset_token
    
    def confirm_password_reset(self, token: str, new_password: str) -> User:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Verify reset token
            payload = verify_token(token)
            
            # Check if it's a password reset token
            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token payload"
                )
            
            # Get user
            user = self.db.get(User, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account is deactivated"
                )
            
            # Update password
            user.hashed_password = hash_password(new_password)
            user.updated_at = datetime.utcnow()
            
            # Invalidate all refresh tokens for security
            statement = select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
            active_tokens = self.db.exec(statement).all()
            
            for token_obj in active_tokens:
                token_obj.revoked = True
                self.db.add(token_obj)
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )