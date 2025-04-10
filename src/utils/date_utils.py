"""
Date utility functions for handling ISO datetime strings and other date operations.
"""
from datetime import datetime
from typing import Optional, Union


def parse_iso_datetime(iso_date_string: Optional[str]) -> datetime:
    """
    Parse an ISO-8601 formatted datetime string into a datetime object.

    Args:
        iso_date_string: An ISO-8601 formatted datetime string

    Returns:
        Datetime object or None if parsing fails
    """
    if not iso_date_string:
        return datetime.now()

    try:
        # Handle strings with or without timezone info
        if "Z" in iso_date_string:
            # UTC time indicated by Z
            return datetime.fromisoformat(iso_date_string.replace("Z", "+00:00"))
        elif (
            "+" in iso_date_string or "-" in iso_date_string and "T" in iso_date_string
        ):
            # Already has timezone info
            return datetime.fromisoformat(iso_date_string)
        else:
            # Assume UTC if no timezone specified
            return datetime.fromisoformat(iso_date_string)
    except (ValueError, TypeError):
        # Return current time if parsing fails
        return datetime.now()
