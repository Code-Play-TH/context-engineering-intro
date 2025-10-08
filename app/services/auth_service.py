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
