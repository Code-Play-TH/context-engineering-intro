"""
User management API endpoints.

Handles user CRUD operations, department and role management.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_

from app.api.deps import (
    get_db,
    get_current_active_user,
    require_superuser,
    require_admin_access,
)
from app.models.user import User, Department, Role
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)

router = APIRouter()


# User management endpoints
@router.get("/users/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """
    Get list of users with filtering options.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        department_id: Filter by department ID
        is_active: Filter by active status
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        List[UserResponse]: List of users
    """
    statement = select(User).join(Department).join(Role)
    
    # Apply filters
    filters = []
    if department_id is not None:
        filters.append(User.department_id == department_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.offset(skip).limit(limit)
    
    result = await db.execute(statement)
    users = result.scalars().all()
    
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        UserResponse: User data
        
    Raises:
        HTTPException: If user not found
    """
    statement = (
        select(User)
        .where(User.id == user_id)
        .join(Department)
        .join(Role)
    )
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Create new user.
    
    Args:
        user_data: User creation data
        current_user: Current authenticated superuser
        db: Database session
        
    Returns:
        UserResponse: Created user
        
    Raises:
        HTTPException: If username/email already exists
    """
    # Check if username or email already exists
    existing_user = await db.execute(
        select(User).where(
            (User.username == user_data.username) |
            (User.email == user_data.email)
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Verify department and role exist
    department = await db.get(Department, user_data.department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )
    
    role = await db.get(Role, user_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role not found"
        )
    
    # Create user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        department_id=user_data.department_id,
        role_id=user_data.role_id,
        is_superuser=user_data.is_superuser,
        hashed_password=User.hash_password(user_data.password)
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Get user with related data
    statement = (
        select(User)
        .where(User.id == db_user.id)
        .join(Department)
        .join(Role)
    )
    result = await db.execute(statement)
    user_with_relations = result.scalar_one()
    
    return UserResponse.model_validate(user_with_relations)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update user information.
    
    Args:
        user_id: User ID to update
        user_data: User update data
        current_user: Current authenticated superuser
        db: Database session
        
    Returns:
        UserResponse: Updated user
        
    Raises:
        HTTPException: If user not found or email already exists
    """
    # Get user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check email uniqueness if email is being updated
    if user_data.email and user_data.email != user.email:
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.touch()
    await db.commit()
    await db.refresh(user)
    
    # Get user with related data
    statement = (
        select(User)
        .where(User.id == user.id)
        .join(Department)
        .join(Role)
    )
    result = await db.execute(statement)
    user_with_relations = result.scalar_one()
    
    return UserResponse.model_validate(user_with_relations)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Soft delete user.
    
    Args:
        user_id: User ID to delete
        current_user: Current authenticated superuser
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found or trying to delete self
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.soft_delete()
    await db.commit()
    
    return {"message": f"User {user.username} deleted successfully"}


# Department management endpoints
@router.get("/departments/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[DepartmentResponse]:
    """
    Get list of departments.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[DepartmentResponse]: List of departments
    """
    statement = select(Department)
    
    if is_active is not None:
        statement = statement.where(Department.is_active == is_active)
    
    statement = statement.offset(skip).limit(limit)
    
    result = await db.execute(statement)
    departments = result.scalars().all()
    
    return [DepartmentResponse.model_validate(dept) for dept in departments]


@router.post("/departments/", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db)
) -> DepartmentResponse:
    """
    Create new department.
    
    Args:
        department_data: Department creation data
        current_user: Current authenticated superuser
        db: Database session
        
    Returns:
        DepartmentResponse: Created department
        
    Raises:
        HTTPException: If department code/name already exists
    """
    # Check if code or name already exists
    existing_dept = await db.execute(
        select(Department).where(
            (Department.code == department_data.code) |
            (Department.name == department_data.name)
        )
    )
    if existing_dept.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code or name already exists"
        )
    
    # Create department
    db_department = Department(**department_data.model_dump())
    
    db.add(db_department)
    await db.commit()
    await db.refresh(db_department)
    
    return DepartmentResponse.model_validate(db_department)


# Role management endpoints
@router.get("/roles/", response_model=List[RoleResponse])
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db)
) -> List[RoleResponse]:
    """
    Get list of roles.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        department_id: Filter by department ID
        is_active: Filter by active status
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        List[RoleResponse]: List of roles
    """
    statement = select(Role).join(Department)
    
    # Apply filters
    filters = []
    if department_id is not None:
        filters.append(Role.department_id == department_id)
    if is_active is not None:
        filters.append(Role.is_active == is_active)
    
    if filters:
        statement = statement.where(and_(*filters))
    
    statement = statement.offset(skip).limit(limit)
    
    result = await db.execute(statement)
    roles = result.scalars().all()
    
    return [RoleResponse.model_validate(role) for role in roles]