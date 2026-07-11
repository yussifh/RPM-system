"""
date_utils.py
---------------
Small shared date/time helpers used across multiple layers (ML risk
engine, doctor-facing patient overview, etc.) — extracted here to
avoid duplicating the same calculation in more than one place.
"""

from datetime import date


def calculate_age(date_of_birth: date) -> int:
    """Returns a person's current age in whole years given their date of birth."""
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )
