"""
Datetime and timezone utilities.

This module provides utilities for handling datetime, timezone conversions,
and time-related calculations across different timezones.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from zoneinfo import ZoneInfo, available_timezones
import logging

logger = logging.getLogger(__name__)


# Common timezones
class CommonTimezone:
    """Common timezone constants."""
    UTC = "UTC"
    BANGKOK = "Asia/Bangkok"  # Thailand (UTC+7)
    NEW_YORK = "America/New_York"  # US Eastern
    LOS_ANGELES = "America/Los_Angeles"  # US Pacific
    LONDON = "Europe/London"  # UK
    TOKYO = "Asia/Tokyo"  # Japan
    SYDNEY = "Australia/Sydney"  # Australia
    SINGAPORE = "Asia/Singapore"  # Singapore


def get_current_utc() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        datetime: Current UTC datetime with timezone info.
    """
    return datetime.now(timezone.utc)


def get_current_datetime(tz: str = CommonTimezone.UTC) -> datetime:
    """
    Get current datetime in specified timezone.

    Args:
        tz (str): Timezone name (e.g., "Asia/Bangkok").

    Returns:
        datetime: Current datetime in specified timezone.
    """
    try:
        zone = ZoneInfo(tz)
        return datetime.now(zone)
    except Exception as e:
        logger.error(f"Invalid timezone: {tz}. Error: {e}")
        return get_current_utc()


def to_utc(dt: datetime) -> datetime:
    """
    Convert datetime to UTC.

    Args:
        dt (datetime): Datetime to convert (can be naive or aware).

    Returns:
        datetime: Datetime in UTC with timezone info.
    """
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_timezone(dt: datetime, tz: str) -> datetime:
    """
    Convert datetime to specified timezone.

    Args:
        dt (datetime): Datetime to convert.
        tz (str): Target timezone name.

    Returns:
        datetime: Datetime in target timezone.
    """
    try:
        # First ensure datetime is aware (convert to UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert to target timezone
        zone = ZoneInfo(tz)
        return dt.astimezone(zone)
    except Exception as e:
        logger.error(f"Error converting to timezone {tz}: {e}")
        return dt


def is_timezone_valid(tz: str) -> bool:
    """
    Check if timezone string is valid.

    Args:
        tz (str): Timezone name to validate.

    Returns:
        bool: True if valid timezone.
    """
    try:
        ZoneInfo(tz)
        return True
    except Exception:
        return False


def get_timezone_offset(tz: str, dt: Optional[datetime] = None) -> timedelta:
    """
    Get timezone offset from UTC.

    Args:
        tz (str): Timezone name.
        dt (Optional[datetime]): Datetime to get offset for (default: now).

    Returns:
        timedelta: Timezone offset.

    Example:
        >>> get_timezone_offset("Asia/Bangkok")
        timedelta(seconds=25200)  # +7 hours
    """
    if dt is None:
        dt = get_current_utc()

    try:
        zone = ZoneInfo(tz)
        return dt.astimezone(zone).utcoffset()
    except Exception as e:
        logger.error(f"Error getting offset for {tz}: {e}")
        return timedelta(0)


def normalize_datetime(
    dt: Union[datetime, str, int],
    source_tz: Optional[str] = None,
    target_tz: str = CommonTimezone.UTC
) -> datetime:
    """
    Normalize datetime from various formats to target timezone.

    Args:
        dt (Union[datetime, str, int]): Datetime in various formats.
            - datetime object
            - ISO 8601 string
            - Unix timestamp (seconds since epoch)
        source_tz (Optional[str]): Source timezone (for naive datetimes).
        target_tz (str): Target timezone (default: UTC).

    Returns:
        datetime: Normalized datetime in target timezone.

    Example:
        >>> normalize_datetime("2025-01-01T12:00:00", source_tz="Asia/Bangkok")
        datetime(2025, 1, 1, 5, 0, tzinfo=timezone.utc)
    """
    # Handle datetime object
    if isinstance(dt, datetime):
        if dt.tzinfo is None and source_tz:
            # Naive datetime with source timezone
            zone = ZoneInfo(source_tz)
            dt = dt.replace(tzinfo=zone)
        elif dt.tzinfo is None:
            # Assume UTC
            dt = dt.replace(tzinfo=timezone.utc)

        return to_timezone(dt, target_tz)

    # Handle ISO 8601 string
    if isinstance(dt, str):
        try:
            parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            if parsed.tzinfo is None and source_tz:
                zone = ZoneInfo(source_tz)
                parsed = parsed.replace(tzinfo=zone)
            elif parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)

            return to_timezone(parsed, target_tz)
        except Exception as e:
            logger.error(f"Error parsing datetime string: {dt}. Error: {e}")
            return get_current_utc()

    # Handle Unix timestamp
    if isinstance(dt, (int, float)):
        parsed = datetime.fromtimestamp(dt, tz=timezone.utc)
        return to_timezone(parsed, target_tz)

    logger.error(f"Unsupported datetime format: {type(dt)}")
    return get_current_utc()


def format_datetime(
    dt: datetime,
    fmt: str = "iso",
    tz: Optional[str] = None
) -> str:
    """
    Format datetime to string.

    Args:
        dt (datetime): Datetime to format.
        fmt (str): Format type:
            - "iso": ISO 8601 format
            - "date": YYYY-MM-DD
            - "datetime": YYYY-MM-DD HH:MM:SS
            - "friendly": "Jan 1, 2025 12:00 PM"
            - Custom strftime format
        tz (Optional[str]): Convert to timezone before formatting.

    Returns:
        str: Formatted datetime string.
    """
    if tz:
        dt = to_timezone(dt, tz)

    if fmt == "iso":
        return dt.isoformat()
    elif fmt == "date":
        return dt.strftime("%Y-%m-%d")
    elif fmt == "datetime":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif fmt == "friendly":
        return dt.strftime("%b %d, %Y %I:%M %p")
    else:
        # Custom format
        return dt.strftime(fmt)


def get_date_range(
    start: Union[datetime, str],
    end: Union[datetime, str],
    tz: str = CommonTimezone.UTC
) -> tuple[datetime, datetime]:
    """
    Normalize and validate date range.

    Args:
        start (Union[datetime, str]): Start datetime.
        end (Union[datetime, str]): End datetime.
        tz (str): Timezone for normalization.

    Returns:
        tuple[datetime, datetime]: Normalized (start, end) datetimes.

    Raises:
        ValueError: If end is before start.
    """
    start_dt = normalize_datetime(start, target_tz=tz)
    end_dt = normalize_datetime(end, target_tz=tz)

    if end_dt < start_dt:
        raise ValueError(f"End datetime ({end_dt}) is before start datetime ({start_dt})")

    return start_dt, end_dt


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference from now.

    Args:
        dt (datetime): Past datetime.

    Returns:
        str: Human-readable time ago (e.g., "2 hours ago", "3 days ago").
    """
    now = get_current_utc()
    dt_utc = to_utc(dt)

    diff = now - dt_utc

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:  # Less than 1 hour
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:  # Less than 1 day
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:  # Less than 1 week
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:  # Less than 30 days
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:  # Less than 1 year
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def add_business_days(start_date: datetime, days: int) -> datetime:
    """
    Add business days (Monday-Friday) to a date.

    Args:
        start_date (datetime): Starting date.
        days (int): Number of business days to add.

    Returns:
        datetime: Resulting date after adding business days.
    """
    current = start_date
    days_added = 0

    while days_added < days:
        current += timedelta(days=1)
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Monday to Friday
            days_added += 1

    return current


def is_business_day(dt: datetime) -> bool:
    """
    Check if datetime falls on a business day (Monday-Friday).

    Args:
        dt (datetime): Datetime to check.

    Returns:
        bool: True if business day.
    """
    return dt.weekday() < 5


def get_month_boundaries(
    year: int,
    month: int,
    tz: str = CommonTimezone.UTC
) -> tuple[datetime, datetime]:
    """
    Get start and end datetimes for a month.

    Args:
        year (int): Year.
        month (int): Month (1-12).
        tz (str): Timezone.

    Returns:
        tuple[datetime, datetime]: (month_start, month_end).
    """
    zone = ZoneInfo(tz)

    # First day of month
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=zone)

    # Last day of month
    if month == 12:
        end = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=zone) - timedelta(microseconds=1)
    else:
        end = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=zone) - timedelta(microseconds=1)

    return start, end


def seconds_until(target_dt: datetime) -> float:
    """
    Get seconds until target datetime.

    Args:
        target_dt (datetime): Target datetime.

    Returns:
        float: Seconds until target (negative if in the past).
    """
    now = get_current_utc()
    target_utc = to_utc(target_dt)
    return (target_utc - now).total_seconds()


def create_datetime_range(
    start: datetime,
    end: datetime,
    step: timedelta = timedelta(days=1)
) -> list[datetime]:
    """
    Create a list of datetimes between start and end with given step.

    Args:
        start (datetime): Start datetime.
        end (datetime): End datetime.
        step (timedelta): Time step between datetimes.

    Returns:
        list[datetime]: List of datetimes.
    """
    current = start
    result = []

    while current <= end:
        result.append(current)
        current += step

    return result
