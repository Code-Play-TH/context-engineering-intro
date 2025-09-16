"""
Pagination utilities for API endpoints.

Provides consistent pagination functionality across all API endpoints
with support for offset-based and cursor-based pagination.
"""

import math
from typing import Any, List, Optional, Generic, TypeVar
from dataclasses import dataclass
from pydantic import BaseModel, Field
from sqlalchemy import select, func, Integer, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")


@dataclass
class PaginationResult(Generic[T]):
    """Result of a paginated query."""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginationMeta(BaseModel):
    """Pagination metadata for API responses."""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


async def paginate_query(
    query: Select,
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> PaginationResult:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy select query
        db: Database session
        page: Page number (1-indexed)
        limit: Number of items per page
        max_limit: Maximum allowed limit

    Returns:
        PaginationResult with items and metadata

    Example:
        query = select(User).where(User.active == True)
        result = await paginate_query(query, db, page=1, limit=20)

        for user in result.items:
            print(user.name)

        print(f"Page {result.page} of {result.pages}")
    """
    # Validate parameters
    if page < 1:
        page = 1

    if limit < 1:
        limit = 1
    elif limit > max_limit:
        limit = max_limit

    # Calculate offset
    offset = (page - 1) * limit

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pagination metadata
    pages = math.ceil(total / limit) if total > 0 else 1
    has_next = page < pages
    has_prev = page > 1

    # Get paginated items
    paginated_query = query.offset(offset).limit(limit)
    items_result = await db.execute(paginated_query)
    items = items_result.scalars().all()

    return PaginationResult(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


async def paginate_raw_query(
    query: str,
    count_query: str,
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100,
    params: Optional[dict] = None
) -> PaginationResult:
    """
    Paginate a raw SQL query.

    Args:
        query: Raw SQL query for getting items
        count_query: Raw SQL query for getting total count
        db: Database session
        page: Page number (1-indexed)
        limit: Number of items per page
        max_limit: Maximum allowed limit
        params: Query parameters

    Returns:
        PaginationResult with items and metadata
    """
    # Validate parameters
    if page < 1:
        page = 1

    if limit < 1:
        limit = 1
    elif limit > max_limit:
        limit = max_limit

    # Calculate offset
    offset = (page - 1) * limit

    # Get total count
    count_result = await db.execute(count_query, params or {})
    total = count_result.scalar() or 0

    # Calculate pagination metadata
    pages = math.ceil(total / limit) if total > 0 else 1
    has_next = page < pages
    has_prev = page > 1

    # Add pagination to query
    paginated_query = f"{query} LIMIT {limit} OFFSET {offset}"

    # Get paginated items
    items_result = await db.execute(paginated_query, params or {})
    items = items_result.fetchall()

    return PaginationResult(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""
    cursor: Optional[str] = Field(None, description="Cursor for next page")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    order_by: str = Field(default="id", description="Field to order by")
    order_dir: str = Field(default="asc", pattern="^(asc|desc)$", description="Order direction")


@dataclass
class CursorPaginationResult(Generic[T]):
    """Result of a cursor-based paginated query."""
    items: List[T]
    next_cursor: Optional[str]
    has_next: bool
    limit: int


async def paginate_cursor(
    query: Select,
    db: AsyncSession,
    cursor: Optional[str] = None,
    limit: int = 20,
    order_by: str = "id",
    order_dir: str = "asc",
    max_limit: int = 100
) -> CursorPaginationResult:
    """
    Paginate using cursor-based pagination.

    Args:
        query: SQLAlchemy select query
        db: Database session
        cursor: Current cursor position
        limit: Number of items per page
        order_by: Field to order by
        order_dir: Order direction (asc/desc)
        max_limit: Maximum allowed limit

    Returns:
        CursorPaginationResult with items and next cursor
    """
    import base64
    import json

    # Validate parameters
    if limit < 1:
        limit = 1
    elif limit > max_limit:
        limit = max_limit

    # Parse cursor
    cursor_data = None
    if cursor:
        try:
            cursor_json = base64.b64decode(cursor).decode('utf-8')
            cursor_data = json.loads(cursor_json)
        except Exception:
            cursor_data = None

    # Apply cursor filtering
    if cursor_data:
        cursor_value = cursor_data.get('value')
        if cursor_value is not None:
            if order_dir == "asc":
                query = query.where(getattr(query.column_descriptions[0]['entity'], order_by) > cursor_value)
            else:
                query = query.where(getattr(query.column_descriptions[0]['entity'], order_by) < cursor_value)

    # Apply ordering
    entity = query.column_descriptions[0]['entity']
    order_column = getattr(entity, order_by)

    if order_dir == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Get one extra item to check if there's a next page
    items_result = await db.execute(query.limit(limit + 1))
    items = items_result.scalars().all()

    # Check if there's a next page
    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    # Generate next cursor
    next_cursor = None
    if has_next and items:
        last_item = items[-1]
        cursor_value = getattr(last_item, order_by)
        cursor_data = {
            'value': cursor_value,
            'order_by': order_by,
            'order_dir': order_dir
        }
        cursor_json = json.dumps(cursor_data, default=str)
        next_cursor = base64.b64encode(cursor_json.encode('utf-8')).decode('utf-8')

    return CursorPaginationResult(
        items=items,
        next_cursor=next_cursor,
        has_next=has_next,
        limit=limit
    )


def create_pagination_response(
    items: List[Any],
    pagination_result: PaginationResult,
    item_schema: Any = None
) -> dict:
    """
    Create a standardized pagination response.

    Args:
        items: List of items (already serialized)
        pagination_result: Pagination metadata
        item_schema: Pydantic schema for items (optional)

    Returns:
        Dictionary with items and pagination metadata
    """
    # Serialize items if schema provided
    if item_schema:
        serialized_items = [item_schema.model_validate(item) for item in items]
    else:
        serialized_items = items

    return {
        "items": serialized_items,
        "pagination": {
            "total": pagination_result.total,
            "page": pagination_result.page,
            "limit": pagination_result.limit,
            "pages": pagination_result.pages,
            "has_next": pagination_result.has_next,
            "has_prev": pagination_result.has_prev
        }
    }


def get_pagination_links(
    base_url: str,
    pagination_result: PaginationResult,
    query_params: Optional[dict] = None
) -> dict:
    """
    Generate pagination links for API responses.

    Args:
        base_url: Base URL for the endpoint
        pagination_result: Pagination metadata
        query_params: Additional query parameters

    Returns:
        Dictionary with pagination links
    """
    from urllib.parse import urlencode

    links = {}
    params = query_params.copy() if query_params else {}
    params['limit'] = pagination_result.limit

    # Self link
    params['page'] = pagination_result.page
    links['self'] = f"{base_url}?{urlencode(params)}"

    # First link
    params['page'] = 1
    links['first'] = f"{base_url}?{urlencode(params)}"

    # Last link
    params['page'] = pagination_result.pages
    links['last'] = f"{base_url}?{urlencode(params)}"

    # Previous link
    if pagination_result.has_prev:
        params['page'] = pagination_result.page - 1
        links['prev'] = f"{base_url}?{urlencode(params)}"

    # Next link
    if pagination_result.has_next:
        params['page'] = pagination_result.page + 1
        links['next'] = f"{base_url}?{urlencode(params)}"

    return links


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T]
    pagination: PaginationMeta
    links: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True


def paginate_list(
    items: List[T],
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> PaginationResult[T]:
    """
    Paginate an in-memory list.

    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        limit: Number of items per page
        max_limit: Maximum allowed limit

    Returns:
        PaginationResult with paginated items
    """
    # Validate parameters
    if page < 1:
        page = 1

    if limit < 1:
        limit = 1
    elif limit > max_limit:
        limit = max_limit

    total = len(items)
    pages = math.ceil(total / limit) if total > 0 else 1

    # Calculate slice indices
    start = (page - 1) * limit
    end = start + limit

    # Get paginated items
    paginated_items = items[start:end]

    # Calculate metadata
    has_next = page < pages
    has_prev = page > 1

    return PaginationResult(
        items=paginated_items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


async def get_pagination_info(
    query: Select,
    db: AsyncSession,
    limit: int
) -> dict:
    """
    Get pagination information without fetching items.

    Args:
        query: SQLAlchemy select query
        db: Database session
        limit: Items per page

    Returns:
        Dictionary with pagination information
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Calculate pages
    pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "total": total,
        "limit": limit,
        "pages": pages
    }