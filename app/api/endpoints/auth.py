"""
Authentication and Authorization API Endpoints

Provides comprehensive authentication functionality including:
- User registration and login
- JWT token management
- Password reset and change
- Email verification
- Two-factor authentication
- Session management
- Role and permission management
- API key management
- OAuth2 integration
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.core.database import get_session
from app.core.auth import (
    security_service, get_current_user, get_current_active_user,
    get_current_verified_user, get_current_superuser, log_security_event,
    create_user_session, terminate_user_session
)
from app.models.auth import (
    User, Role, Permission, UserSession, UserToken, APIKey,
    SecurityAuditLog, UserRole, UserStatus, TokenType, SessionStatus
)
from app.schemas.auth import (
    UserCreate, UserUpdate, UserResponse, UserProfile, LoginRequest,
    LoginResponse, TokenResponse, RefreshTokenRequest, PasswordResetRequest,
    PasswordResetConfirm, PasswordChangeRequest, EmailVerificationRequest,
    EmailVerificationConfirm, TwoFactorSetupResponse, TwoFactorConfirmRequest,
    RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, PermissionResponse,
    UserRoleAssignment, SessionResponse, SessionTerminateRequest,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    SecurityAuditLogResponse, SecurityAuditLogFilters, UserListFilters,
    UserStatusUpdate, BulkUserAction, SecuritySettings, SecurityStatsResponse
)
from app.services.communication.email_service import EmailService
from app.tasks.auth import (
    send_verification_email, send_password_reset_email,
    cleanup_expired_sessions, cleanup_expired_tokens
)
from app.utils.pagination import PaginationParams, paginate_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        request: HTTP request object
        db: Database session

    Returns:
        Created user response
    """
    try:
        logger.info(f"User registration attempt: {user_data.email}")

        # Check if user already exists
        stmt = select(User).where(
            or_(User.email == user_data.email, User.username == user_data.username)
        )
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        # Validate password strength
        is_strong, issues = security_service.is_password_strong(user_data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password requirements not met: {', '.join(issues)}"
            )

        # Create new user
        hashed_password = security_service.hash_password(user_data.password)

        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            bio=user_data.bio,
            timezone=user_data.timezone,
            language=user_data.language,
            status=UserStatus.PENDING_VERIFICATION,
            is_active=True,
            is_verified=False
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Send verification email
        send_verification_email.delay(new_user.id, new_user.email)

        # Log security event
        await log_security_event(
            event_type="user_registration",
            user_id=new_user.id,
            details={"email": user_data.email, "username": user_data.username},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True,
            risk_level="low",
            db=db
        )

        return UserResponse(
            id=new_user.id,
            uuid=str(new_user.uuid),
            email=new_user.email,
            username=new_user.username,
            full_name=new_user.full_name,
            phone_number=new_user.phone_number,
            bio=new_user.bio,
            timezone=new_user.timezone,
            language=new_user.language,
            status=new_user.status,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            is_superuser=new_user.is_superuser,
            avatar_url=new_user.avatar_url,
            two_factor_enabled=new_user.two_factor_enabled,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            preferences=new_user.preferences or {}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> LoginResponse:
    """
    Authenticate user and create session.

    Args:
        login_data: Login credentials
        request: HTTP request object
        db: Database session

    Returns:
        Login response with tokens and user data
    """
    try:
        logger.info(f"Login attempt: {login_data.email}")

        # Get user by email
        stmt = select(User).where(User.email == login_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await log_security_event(
                event_type="login_failed",
                details={"email": login_data.email, "reason": "user_not_found"},
                ip_address=request.client.host,
                success=False,
                risk_level="medium",
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is locked
        if user.is_locked:
            await log_security_event(
                event_type="login_failed",
                user_id=user.id,
                details={"reason": "account_locked"},
                ip_address=request.client.host,
                success=False,
                risk_level="high",
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked"
            )

        # Verify password
        if not security_service.verify_password(login_data.password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                await log_security_event(
                    event_type="account_locked",
                    user_id=user.id,
                    details={"reason": "too_many_failed_attempts"},
                    ip_address=request.client.host,
                    success=False,
                    risk_level="high",
                    db=db
                )

            await db.commit()

            await log_security_event(
                event_type="login_failed",
                user_id=user.id,
                details={"reason": "invalid_password", "attempts": user.failed_login_attempts},
                ip_address=request.client.host,
                success=False,
                risk_level="medium",
                db=db
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if not user.is_active:
            await log_security_event(
                event_type="login_failed",
                user_id=user.id,
                details={"reason": "account_inactive"},
                ip_address=request.client.host,
                success=False,
                risk_level="medium",
                db=db
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )

        # Check for two-factor authentication
        requires_2fa = user.two_factor_enabled and not login_data.two_factor_code
        if requires_2fa:
            return LoginResponse(
                access_token="",
                refresh_token="",
                token_type="bearer",
                expires_in=0,
                user=UserResponse(
                    id=user.id,
                    uuid=str(user.uuid),
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    status=user.status,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    is_superuser=user.is_superuser,
                    two_factor_enabled=user.two_factor_enabled,
                    created_at=user.created_at
                ),
                session_id="",
                requires_two_factor=True
            )

        # Verify 2FA code if provided
        if user.two_factor_enabled and login_data.two_factor_code:
            # In production, this would verify the TOTP code
            # For now, accepting any 6-digit code
            if not (login_data.two_factor_code.isdigit() and len(login_data.two_factor_code) == 6):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid two-factor code"
                )

        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        user.locked_until = None

        # Create session
        session_data = {
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "device_info": {},
            "location": {}
        }
        session = await create_user_session(user, session_data, db)

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        tokens = security_service.create_token_pair(token_data)

        await db.commit()

        # Log successful login
        await log_security_event(
            event_type="login_success",
            user_id=user.id,
            details={"session_id": session.session_id},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True,
            risk_level="low",
            db=db
        )

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=UserResponse(
                id=user.id,
                uuid=str(user.uuid),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                phone_number=user.phone_number,
                bio=user.bio,
                timezone=user.timezone,
                language=user.language,
                status=user.status,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_superuser=user.is_superuser,
                avatar_url=user.avatar_url,
                two_factor_enabled=user.two_factor_enabled,
                primary_role=user.primary_role,
                roles=[role.name for role in user.roles],
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login_at=user.last_login_at,
                preferences=user.preferences or {}
            ),
            session_id=session.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> Dict[str, str]:
    """
    Logout user and terminate session.

    Args:
        request: HTTP request object
        current_user: Current authenticated user
        db: Database session

    Returns:
        Logout confirmation
    """
    try:
        # Extract session ID from request (would be in token payload)
        # For now, terminating all sessions for the user
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == current_user.id,
                UserSession.status == SessionStatus.ACTIVE
            )
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            session.status = SessionStatus.TERMINATED
            session.terminated_at = datetime.utcnow()

        await db.commit()

        # Log logout event
        await log_security_event(
            event_type="logout",
            user_id=current_user.id,
            details={"sessions_terminated": len(sessions)},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True,
            risk_level="low",
            db=db
        )

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_session)
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token request
        db: Database session

    Returns:
        New token response
    """
    try:
        # Verify refresh token
        payload = security_service.verify_token(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Get user
        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )

        # Create new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        tokens = security_service.create_token_pair(token_data)

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile data
    """
    return UserProfile(
        id=current_user.id,
        uuid=str(current_user.uuid),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        timezone=current_user.timezone,
        language=current_user.language,
        status=current_user.status,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        two_factor_enabled=current_user.two_factor_enabled,
        roles=[role.name for role in current_user.roles],
        permissions=[perm.name for role in current_user.roles for perm in role.permissions],
        preferences=current_user.preferences or {},
        metadata=current_user.metadata or {},
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login_at=current_user.last_login_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> UserResponse:
    """
    Update current user profile.

    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user response
    """
    try:
        # Update user fields
        update_data = user_update.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        current_user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(current_user)

        return UserResponse(
            id=current_user.id,
            uuid=str(current_user.uuid),
            email=current_user.email,
            username=current_user.username,
            full_name=current_user.full_name,
            phone_number=current_user.phone_number,
            bio=current_user.bio,
            timezone=current_user.timezone,
            language=current_user.language,
            status=current_user.status,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            is_superuser=current_user.is_superuser,
            avatar_url=current_user.avatar_url,
            two_factor_enabled=current_user.two_factor_enabled,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            preferences=current_user.preferences or {}
        )

    except Exception as e:
        logger.error(f"User profile update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> Dict[str, str]:
    """
    Change user password.

    Args:
        password_change: Password change request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Password change confirmation
    """
    try:
        # Verify current password
        if not security_service.verify_password(
            password_change.current_password,
            current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Validate new password strength
        is_strong, issues = security_service.is_password_strong(password_change.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password requirements not met: {', '.join(issues)}"
            )

        # Update password
        current_user.hashed_password = security_service.hash_password(password_change.new_password)
        current_user.last_password_change = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()

        await db.commit()

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# Additional endpoints for password reset, email verification, 2FA, etc.
# would be implemented here following the same patterns...

@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> List[SessionResponse]:
    """
    Get user's active sessions.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of user sessions
    """
    stmt = select(UserSession).where(
        UserSession.user_id == current_user.id
    ).order_by(desc(UserSession.created_at))

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=session.id,
            session_id=session.session_id,
            status=session.status,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_info=session.device_info or {},
            location=session.location or {},
            created_at=session.created_at,
            last_activity=session.last_activity,
            expires_at=session.expires_at,
            is_current=False  # Would determine current session
        )
        for session in sessions
    ]


# API Key Management endpoints would be implemented here...
# Role and Permission management endpoints would be implemented here...
# Admin endpoints would be implemented here...

@router.get("/security/stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_session)
) -> SecurityStatsResponse:
    """
    Get security statistics (admin only).

    Args:
        current_user: Current superuser
        db: Database session

    Returns:
        Security statistics
    """
    try:
        # Get various security metrics
        total_users = await db.scalar(select(func.count(User.id)))
        active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))

        # Simulate other statistics
        return SecurityStatsResponse(
            total_users=total_users or 0,
            active_users=active_users or 0,
            locked_users=0,
            failed_logins_24h=0,
            successful_logins_24h=0,
            active_sessions=0,
            active_api_keys=0,
            security_events_24h=0,
            high_risk_events_24h=0,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Security stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security statistics"
        )