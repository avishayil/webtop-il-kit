"""Utility functions for Webtop scraper."""
from datetime import datetime
from typing import Optional


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse date string in various formats to datetime object.

    Args:
        date_str: Date string in formats like "21-01-2026", "21/01/2026",
            "2026-01-21", etc.

    Returns:
        datetime object or None if parsing fails

    Raises:
        ValueError: If date string cannot be parsed
    """
    if date_str is None:
        return None

    # Try different date formats
    date_formats = [
        "%d-%m-%Y",  # 21-01-2026
        "%d/%m/%Y",  # 21/01/2026
        "%Y-%m-%d",  # 2026-01-21
        "%Y/%m/%d",  # 2026/01/21
        "%d.%m.%Y",  # 21.01.2026
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse date '{date_str}'. Supported formats: DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD")
