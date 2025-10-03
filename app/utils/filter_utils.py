"""
Filter utilities for building dynamic database queries.

This module provides utilities for constructing complex database queries
with multiple filters, sorting, and pagination.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from sqlalchemy import or_, and_, func, cast, String
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class FilterOperator(str, Enum):
    """Filter operators for query building."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"  # Case-insensitive LIKE
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    CONTAINS = "contains"  # For arrays/JSON
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class FilterCondition:
    """
    Represents a single filter condition.

    Attributes:
        field (str): Field name to filter on.
        operator (FilterOperator): Filter operator.
        value (Any): Value to filter by.
    """

    def __init__(
        self,
        field: str,
        operator: FilterOperator,
        value: Any
    ):
        self.field = field
        self.operator = operator
        self.value = value

    def __repr__(self) -> str:
        return f"FilterCondition(field={self.field}, op={self.operator}, value={self.value})"


class FilterBuilder(Generic[T]):
    """
    Build dynamic SQLAlchemy queries with filters.

    Usage:
        builder = FilterBuilder(KOL)
        builder.add_filter("platform", FilterOperator.EQUALS, "instagram")
        builder.add_filter("followers_count", FilterOperator.GREATER_THAN_EQUAL, 10000)
        query = builder.apply(db.query(KOL))
        results = query.all()
    """

    def __init__(self, model: type[T]):
        """
        Initialize filter builder.

        Args:
            model (type[T]): SQLAlchemy model class.
        """
        self.model = model
        self.filters: List[FilterCondition] = []
        self.sort_by: Optional[str] = None
        self.sort_order: SortOrder = SortOrder.ASC

    def add_filter(
        self,
        field: str,
        operator: FilterOperator,
        value: Any
    ) -> 'FilterBuilder':
        """
        Add a filter condition.

        Args:
            field (str): Field name on the model.
            operator (FilterOperator): Filter operator.
            value (Any): Value to filter by.

        Returns:
            FilterBuilder: Self for method chaining.
        """
        self.filters.append(FilterCondition(field, operator, value))
        return self

    def add_filters_from_dict(
        self,
        filters_dict: Dict[str, Any],
        default_operator: FilterOperator = FilterOperator.EQUALS
    ) -> 'FilterBuilder':
        """
        Add multiple filters from dictionary.

        Args:
            filters_dict (Dict[str, Any]): Dict of field: value pairs.
            default_operator (FilterOperator): Default operator to use.

        Returns:
            FilterBuilder: Self for method chaining.

        Example:
            >>> builder.add_filters_from_dict({"platform": "instagram", "verified": True})
        """
        for field, value in filters_dict.items():
            if value is not None:  # Skip None values
                self.add_filter(field, default_operator, value)
        return self

    def set_sorting(
        self,
        field: str,
        order: SortOrder = SortOrder.ASC
    ) -> 'FilterBuilder':
        """
        Set sorting for the query.

        Args:
            field (str): Field name to sort by.
            order (SortOrder): Sort order (ASC or DESC).

        Returns:
            FilterBuilder: Self for method chaining.
        """
        self.sort_by = field
        self.sort_order = order
        return self

    def _build_condition(self, condition: FilterCondition):
        """
        Build SQLAlchemy filter expression from condition.

        Args:
            condition (FilterCondition): Filter condition.

        Returns:
            SQLAlchemy filter expression.
        """
        # Get the model attribute
        if not hasattr(self.model, condition.field):
            logger.warning(f"Model {self.model.__name__} has no field '{condition.field}'")
            return None

        field_attr = getattr(self.model, condition.field)

        # Build expression based on operator
        if condition.operator == FilterOperator.EQUALS:
            return field_attr == condition.value

        elif condition.operator == FilterOperator.NOT_EQUALS:
            return field_attr != condition.value

        elif condition.operator == FilterOperator.GREATER_THAN:
            return field_attr > condition.value

        elif condition.operator == FilterOperator.GREATER_THAN_EQUAL:
            return field_attr >= condition.value

        elif condition.operator == FilterOperator.LESS_THAN:
            return field_attr < condition.value

        elif condition.operator == FilterOperator.LESS_THAN_EQUAL:
            return field_attr <= condition.value

        elif condition.operator == FilterOperator.IN:
            return field_attr.in_(condition.value)

        elif condition.operator == FilterOperator.NOT_IN:
            return ~field_attr.in_(condition.value)

        elif condition.operator == FilterOperator.LIKE:
            return field_attr.like(f"%{condition.value}%")

        elif condition.operator == FilterOperator.ILIKE:
            return field_attr.ilike(f"%{condition.value}%")

        elif condition.operator == FilterOperator.STARTS_WITH:
            return field_attr.like(f"{condition.value}%")

        elif condition.operator == FilterOperator.ENDS_WITH:
            return field_attr.like(f"%{condition.value}")

        elif condition.operator == FilterOperator.BETWEEN:
            if isinstance(condition.value, (list, tuple)) and len(condition.value) == 2:
                return field_attr.between(condition.value[0], condition.value[1])
            else:
                logger.error(f"BETWEEN requires tuple of 2 values, got: {condition.value}")
                return None

        elif condition.operator == FilterOperator.IS_NULL:
            return field_attr.is_(None)

        elif condition.operator == FilterOperator.IS_NOT_NULL:
            return field_attr.isnot(None)

        elif condition.operator == FilterOperator.CONTAINS:
            # For JSONB/Array contains
            return field_attr.contains(condition.value)

        else:
            logger.warning(f"Unknown operator: {condition.operator}")
            return None

    def apply(self, query: Query) -> Query:
        """
        Apply filters to SQLAlchemy query.

        Args:
            query (Query): SQLAlchemy query object.

        Returns:
            Query: Filtered query.
        """
        # Apply filters
        for condition in self.filters:
            expression = self._build_condition(condition)
            if expression is not None:
                query = query.filter(expression)

        # Apply sorting
        if self.sort_by and hasattr(self.model, self.sort_by):
            sort_field = getattr(self.model, self.sort_by)
            if self.sort_order == SortOrder.DESC:
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())

        return query

    def clear(self) -> 'FilterBuilder':
        """Clear all filters and sorting."""
        self.filters = []
        self.sort_by = None
        self.sort_order = SortOrder.ASC
        return self


def apply_search(
    query: Query,
    model: type[T],
    search_term: str,
    search_fields: List[str]
) -> Query:
    """
    Apply full-text search across multiple fields.

    Args:
        query (Query): SQLAlchemy query.
        model (type[T]): Model class.
        search_term (str): Search term.
        search_fields (List[str]): Fields to search in.

    Returns:
        Query: Query with search filter applied.

    Example:
        >>> query = db.query(KOL)
        >>> query = apply_search(query, KOL, "john", ["name", "email"])
    """
    if not search_term or not search_fields:
        return query

    # Build OR condition for all search fields
    search_conditions = []
    for field in search_fields:
        if hasattr(model, field):
            field_attr = getattr(model, field)
            # Cast to string for non-string fields
            search_conditions.append(
                cast(field_attr, String).ilike(f"%{search_term}%")
            )

    if search_conditions:
        query = query.filter(or_(*search_conditions))

    return query


def apply_date_range_filter(
    query: Query,
    model: type[T],
    field: str,
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None
) -> Query:
    """
    Apply date range filter.

    Args:
        query (Query): SQLAlchemy query.
        model (type[T]): Model class.
        field (str): Date field name.
        start_date (Optional[Any]): Start date.
        end_date (Optional[Any]): End date.

    Returns:
        Query: Query with date filter applied.
    """
    if not hasattr(model, field):
        logger.warning(f"Model {model.__name__} has no field '{field}'")
        return query

    field_attr = getattr(model, field)

    if start_date:
        query = query.filter(field_attr >= start_date)

    if end_date:
        query = query.filter(field_attr <= end_date)

    return query


def apply_numeric_range_filter(
    query: Query,
    model: type[T],
    field: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> Query:
    """
    Apply numeric range filter.

    Args:
        query (Query): SQLAlchemy query.
        model (type[T]): Model class.
        field (str): Numeric field name.
        min_value (Optional[float]): Minimum value.
        max_value (Optional[float]): Maximum value.

    Returns:
        Query: Query with numeric filter applied.
    """
    if not hasattr(model, field):
        logger.warning(f"Model {model.__name__} has no field '{field}'")
        return query

    field_attr = getattr(model, field)

    if min_value is not None:
        query = query.filter(field_attr >= min_value)

    if max_value is not None:
        query = query.filter(field_attr <= max_value)

    return query


class QueryBuilder(Generic[T]):
    """
    Advanced query builder with support for complex filters.

    Usage:
        builder = QueryBuilder(KOL, db.query(KOL))
        builder.search("john", ["name", "email"])
        builder.filter_equals("platform", "instagram")
        builder.filter_range("followers_count", min_value=10000)
        builder.sort("followers_count", "desc")
        results = builder.paginate(page=1, per_page=20)
    """

    def __init__(self, model: type[T], base_query: Query):
        """
        Initialize query builder.

        Args:
            model (type[T]): SQLAlchemy model class.
            base_query (Query): Base SQLAlchemy query.
        """
        self.model = model
        self.query = base_query

    def search(self, term: str, fields: List[str]) -> 'QueryBuilder':
        """Add search filter."""
        self.query = apply_search(self.query, self.model, term, fields)
        return self

    def filter_equals(self, field: str, value: Any) -> 'QueryBuilder':
        """Add equality filter."""
        if hasattr(self.model, field):
            self.query = self.query.filter(getattr(self.model, field) == value)
        return self

    def filter_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """Add IN filter."""
        if hasattr(self.model, field) and values:
            self.query = self.query.filter(getattr(self.model, field).in_(values))
        return self

    def filter_range(
        self,
        field: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> 'QueryBuilder':
        """Add range filter."""
        self.query = apply_numeric_range_filter(
            self.query, self.model, field, min_value, max_value
        )
        return self

    def filter_date_range(
        self,
        field: str,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> 'QueryBuilder':
        """Add date range filter."""
        self.query = apply_date_range_filter(
            self.query, self.model, field, start_date, end_date
        )
        return self

    def sort(self, field: str, order: str = "asc") -> 'QueryBuilder':
        """Add sorting."""
        if hasattr(self.model, field):
            field_attr = getattr(self.model, field)
            if order.lower() == "desc":
                self.query = self.query.order_by(field_attr.desc())
            else:
                self.query = self.query.order_by(field_attr.asc())
        return self

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Execute query with pagination.

        Args:
            page (int): Page number (1-indexed).
            per_page (int): Items per page.

        Returns:
            Dict[str, Any]: Paginated results with metadata.
        """
        total = self.query.count()
        offset = (page - 1) * per_page

        items = self.query.limit(per_page).offset(offset).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        }

    def all(self) -> List[T]:
        """Execute query and return all results."""
        return self.query.all()

    def first(self) -> Optional[T]:
        """Execute query and return first result."""
        return self.query.first()

    def count(self) -> int:
        """Get count of results."""
        return self.query.count()
