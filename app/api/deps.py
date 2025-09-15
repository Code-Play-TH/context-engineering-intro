"""
FastAPI dependencies for database sessions and authentication.

Provides reusable dependencies for dependency injection.
"""

from typing import AsyncGenerator, Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import get_settings
from app.database import get_session
from app.models.user import User, Department, Role
from app.schemas.user import TokenData, CurrentUser

settings = get_settings()
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    
    Provides an async database session for each request.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in get_session():
        yield session


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time (defaults to settings)
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        department: str = payload.get("department")
        role: str = payload.get("role")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(
            username=username,
            user_id=user_id,
            department=department,
            role=role
        )
        
    except JWTError:
        raise credentials_exception
    
    return token_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    
    Args:
        credentials: HTTP bearer credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If user not found or inactive
    """
    token_data = verify_token(credentials.credentials)
    
    # Get user from database with related data
    statement = (
        select(User)
        .where(User.username == token_data.username, User.is_active == True)
        .join(Department, User.department_id == Department.id)
        .join(Role, User.role_id == Role.id)
    )
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.update_last_login()
    await db.commit()
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    
    Args:
        credentials: Optional HTTP bearer credentials
        db: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if credentials is None:
        return None
        
    try:
        token_data = verify_token(credentials.credentials)
        
        # Get user from database with related data
        statement = (
            select(User)
            .where(User.username == token_data.username, User.is_active == True)
            .join(Department, User.department_id == Department.id)
            .join(Role, User.role_id == Role.id)
        )
        result = await db.execute(statement)
        user = result.scalar_one_or_none()
        
        return user
    except (JWTError, HTTPException):
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for active status).
    
    Args:
        current_user: Current user from token
        
    Returns:
        User: Active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> CurrentUser:
    """
    Get current user information for API responses.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        CurrentUser: User information schema
    """
    return CurrentUser(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        department_code=current_user.department.code,
        department_name=current_user.department.name,
        role_code=current_user.role.code,
        role_name=current_user.role.name,
        is_superuser=current_user.is_superuser,
        permissions=current_user.role.permissions,
        last_login=current_user.last_login
    )


def require_permission(permission: str):
    """
    Dependency factory for permission checking.
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function that checks permission
    """
    async def check_permission(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required permission."""
        if current_user.is_superuser:
            return current_user
        
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {permission}"
            )
        
        return current_user
    
    return check_permission


def require_department(department_code: str):
    """
    Dependency factory for department access checking.
    
    Args:
        department_code: Required department code
        
    Returns:
        Dependency function that checks department access
    """
    async def check_department_access(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user can access the specified department."""
        if current_user.is_superuser:
            return current_user
        
        if not current_user.can_access_department(department_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {department_code} department"
            )
        
        return current_user
    
    return check_department_access


def require_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require superuser privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Superuser
        
    Raises:
        HTTPException: If user is not superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


# Department-specific dependencies
async def require_sales_access(
    current_user: User = Depends(require_department("sales"))
) -> User:
    """Require access to sales department."""
    return current_user


async def require_production_access(
    current_user: User = Depends(require_department("production"))
) -> User:
    """Require access to production department."""
    return current_user


async def require_purchasing_access(
    current_user: User = Depends(require_department("purchasing"))
) -> User:
    """Require access to purchasing department."""
    return current_user


async def require_admin_access(
    current_user: User = Depends(require_department("admin"))
) -> User:
    """Require access to admin department."""
    return current_user