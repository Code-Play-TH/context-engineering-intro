"""
Authentication Core Service

Core authentication functionality including:
- JWT token creation and validation
- Password hashing and verification
- User authentication and authorization
- Session management
- Security utilities and helpers
"""

import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_session
from app.models.auth import User, UserSession, UserToken, TokenType, SessionStatus
from app.schemas.auth import UserResponse, TokenResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Authentication error exception."""
    pass


class AuthorizationError(Exception):
    """Authorization error exception."""
    pass


class SecurityService:
    """
    Core security service for authentication and authorization.
    """

    def __init__(self):
        """Initialize the security service."""
        self.pwd_context = pwd_context
        self.algorithm = settings.JWT_ALGORITHM
        self.secret_key = settings.JWT_SECRET_KEY
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    # Password Management
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def generate_password_hash(self, password: str) -> str:
        """
        Generate a secure password hash.

        Args:
            password: Plain text password

        Returns:
            Secure password hash
        """
        return self.hash_password(password)

    # Token Management
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time

        Returns:
            JWT access token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time

        Returns:
            JWT refresh token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise AuthenticationError("Invalid token")

    def create_token_pair(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create both access and refresh tokens.

        Args:
            user_data: User data to encode in tokens

        Returns:
            Dict containing access_token and refresh_token
        """
        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token(user_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

    # API Key Management
    def generate_api_key(self) -> tuple[str, str]:
        """
        Generate a secure API key.

        Returns:
            Tuple of (key_id, api_key)
        """
        key_id = secrets.token_urlsafe(16)
        api_key = secrets.token_urlsafe(32)
        return key_id, api_key

    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for secure storage.

        Args:
            api_key: Plain API key

        Returns:
            Hashed API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """
        Verify an API key against its hash.

        Args:
            api_key: Plain API key
            hashed_key: Hashed API key

        Returns:
            True if API key matches, False otherwise
        """
        return hmac.compare_digest(
            hashlib.sha256(api_key.encode()).hexdigest(),
            hashed_key
        )

    # Session Management
    def create_session_id(self) -> str:
        """
        Create a secure session ID.

        Returns:
            Secure session ID
        """
        return secrets.token_urlsafe(32)

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.

        Args:
            length: Token length

        Returns:
            Secure random token
        """
        return secrets.token_urlsafe(length)

    # Security Utilities
    def generate_two_factor_secret(self) -> str:
        """
        Generate a two-factor authentication secret.

        Returns:
            Base32 encoded secret
        """
        return secrets.token_hex(16)

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for two-factor authentication.

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def is_password_strong(self, password: str) -> tuple[bool, List[str]]:
        """
        Check if a password meets strength requirements.

        Args:
            password: Password to check

        Returns:
            Tuple of (is_strong, list_of_issues)
        """
        issues = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password should contain at least one special character")

        return len(issues) == 0, issues


# Global security service instance
security_service = SecurityService()


# Authentication Dependencies
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_session)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify and decode token
        payload = security_service.verify_token(credentials.credentials)

        # Extract user information
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # Get user from database
        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        if user.is_locked:
            raise AuthenticationError("User account is locked")

        return user

    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current verified user.

    Args:
        current_user: Current active user

    Returns:
        Current verified user

    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification required"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current superuser.

    Args:
        current_user: Current active user

    Returns:
        Current superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user


# Permission-based Dependencies
def require_permission(permission: str):
    """
    Create a dependency that requires a specific permission.

    Args:
        permission: Required permission name

    Returns:
        Dependency function
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user

    return permission_dependency


def require_role(role: str):
    """
    Create a dependency that requires a specific role.

    Args:
        role: Required role name

    Returns:
        Dependency function
    """
    async def role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user

    return role_dependency


def require_any_role(roles: List[str]):
    """
    Create a dependency that requires any of the specified roles.

    Args:
        roles: List of acceptable role names

    Returns:
        Dependency function
    """
    async def any_role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not any(current_user.has_role(role) for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following roles required: {', '.join(roles)}"
            )
        return current_user

    return any_role_dependency


# Legacy compatibility (for backward compatibility with existing code)
async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user (legacy compatibility).

    Args:
        current_user: Current user from authentication

    Returns:
        Current user if admin

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def create_access_token(data: dict) -> str:
    """
    Create access token (legacy compatibility).

    Args:
        data: Token payload data

    Returns:
        JWT token string
    """
    return security_service.create_access_token(data)


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode token (legacy compatibility).

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        return security_service.verify_token(token)
    except AuthenticationError:
        return None