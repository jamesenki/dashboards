"""
Datetime handling utilities for IoTSphere API

This module provides consistent datetime handling functions
to avoid offset-naive and offset-aware datetime comparison issues.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union


def generate_date_range(days: int, include_time: bool = False) -> List[str]:
    """
    Generate a consistent date range for the past 'days' days

    Args:
        days: Number of days to generate
        include_time: Whether to include time information

    Returns:
        List of formatted dates
    """
    end_date = datetime.now()

    if include_time:
        return [
            (end_date - timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S")
            for i in range(days)
        ][::-1]
    else:
        return [
            (end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)
        ][::-1]


def format_date_for_api(date: Union[datetime, str]) -> str:
    """
    Format a date consistently for API responses

    Args:
        date: The date to format (datetime object or string)

    Returns:
        Formatted date string
    """
    if isinstance(date, datetime):
        return date.strftime("%Y-%m-%dT%H:%M:%S")
    return date


def safe_datetime_comparison(
    dt1: Union[datetime, str], dt2: Union[datetime, str]
) -> bool:
    """
    Safely compare two datetime objects or strings

    Args:
        dt1: First datetime (datetime object or string)
        dt2: Second datetime (datetime object or string)

    Returns:
        Result of comparison (dt1 <= dt2)
    """
    # Convert to string format if necessary
    if isinstance(dt1, datetime):
        dt1 = dt1.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(dt2, datetime):
        dt2 = dt2.strftime("%Y-%m-%dT%H:%M:%S")

    return dt1 <= dt2
