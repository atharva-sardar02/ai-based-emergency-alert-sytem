"""Deduplication utilities for alert natural key generation."""
import hashlib
from datetime import datetime
from typing import Optional


def generate_natural_key(
    source: str,
    provider_id: Optional[str] = None,
    title: Optional[str] = None,
    area: Optional[str] = None,
    effective_at: Optional[datetime] = None
) -> str:
    """
    Generate a unique natural key for an alert.
    
    Strategy:
    1. If provider_id exists, use: sha256(source + provider_id)
    2. Otherwise, use: sha256(source + title + area + rounded_timestamp)
    
    Args:
        source: Source name (e.g., 'NWS', 'USGS')
        provider_id: Original ID from the provider
        title: Alert title (fallback)
        area: Geographic area (fallback)
        effective_at: Effective timestamp (fallback, rounded to 10-min buckets)
    
    Returns:
        SHA256 hash as natural key
    """
    if provider_id:
        # Use provider ID when available (most reliable)
        key_string = f"{source}|{provider_id}"
    else:
        # Fallback to content-based key
        # Round timestamp to 10-minute buckets to handle slight variations
        rounded_time = ""
        if effective_at:
            # Round to nearest 10 minutes
            minutes = effective_at.minute - (effective_at.minute % 10)
            rounded = effective_at.replace(minute=minutes, second=0, microsecond=0)
            rounded_time = rounded.isoformat()
        
        key_string = f"{source}|{title or ''}|{area or ''}|{rounded_time}"
    
    # Generate SHA256 hash
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


def is_duplicate(natural_key: str, db_session) -> bool:
    """
    Check if an alert with the given natural key already exists in database.
    
    Args:
        natural_key: The natural key to check
        db_session: SQLAlchemy database session
    
    Returns:
        True if duplicate exists, False otherwise
    """
    from app.models import Alert
    
    existing = db_session.query(Alert).filter(
        Alert.natural_key == natural_key
    ).first()
    
    return existing is not None

