"""Time and date utilities."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from dateutil import parser


def parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    """
    Parse a datetime string into a timezone-aware datetime object.
    
    Args:
        date_string: ISO format date string or None
    
    Returns:
        Timezone-aware datetime object or None
    """
    if not date_string:
        return None
    
    try:
        dt = parser.parse(date_string)
        # Ensure timezone-aware (default to UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def time_window_start(hours_ago: int = 48) -> datetime:
    """
    Get a datetime representing X hours ago from now in UTC.
    
    Args:
        hours_ago: Number of hours in the past
    
    Returns:
        Timezone-aware datetime
    """
    return utc_now() - timedelta(hours=hours_ago)


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime as ISO string."""
    if not dt:
        return None
    return dt.isoformat()

