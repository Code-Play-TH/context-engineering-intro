"""
Utility functions and helpers for the KOL Management System.

Provides common utilities including:
- Pagination helpers for API endpoints
- Data validation and transformation utilities
- Helper functions for common operations
"""

from app.utils.pagination import (
    PaginationParams,
    PaginationResult,
    PaginationMeta,
    CursorPaginationParams,
    CursorPaginationResult,
    PaginatedResponse,
    paginate_query,
    paginate_cursor,
    paginate_list,
    create_pagination_response,
    get_pagination_links,
    get_pagination_info
)

__all__ = [
    # Pagination utilities
    "PaginationParams",
    "PaginationResult",
    "PaginationMeta",
    "CursorPaginationParams",
    "CursorPaginationResult",
    "PaginatedResponse",
    "paginate_query",
    "paginate_cursor",
    "paginate_list",
    "create_pagination_response",
    "get_pagination_links",
    "get_pagination_info",
]