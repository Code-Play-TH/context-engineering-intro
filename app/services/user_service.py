"""User management service."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select, func
from fastapi import HTTPException, status
from app.models.user import User
from app.models.enums import Role
from app.core.security import hash_password, validate_password_strength


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: Role = Role.VIEWER
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User email
            password: User password
            full_name: User full name
            role: User role
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email already exists or password is weak
        """
        # Check if email already exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Create user
        hashed_password = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role.value
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        return self.db.get(User, user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User object or None if not found
        """
        statement = select(User).where(User.email == email)
        return self.db.exec(statement).first()
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """
        List users with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by role
            is_active: Filter by active status
            
        Returns:
            Tuple of (users list, total count)
        """
        statement = select(User)
        
        # Apply filters
        if role is not None:
            statement = statement.where(User.role == role.value)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        
        # Get total count
        count_statement = select(func.count()).select_from(User)
        if role is not None:
            count_statement = count_statement.where(User.role == role.value)
        if is_active is not None:
            count_statement = count_statement.where(User.is_active == is_active)
        total = self.db.exec(count_statement).one()
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        users = self.db.exec(statement).all()
        
        return list(users), total
    
    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """
        Update user information.
        
        Args:
            user_id: User ID
            email: New email (optional)
            full_name: New full name (optional)
            role: New role (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found or email already exists
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if new email already exists
        if email and email != user.email:
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = email
        
        # Update fields
        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role.value
        if is_active is not None:
            user.is_active = is_active
        
        user.updated_at = datetime.utcnow()
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate user (soft delete).
        
        Args:
            user_id: User ID
            
        Returns:
            Deactivated user object
            
        Raises:
            HTTPException: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
