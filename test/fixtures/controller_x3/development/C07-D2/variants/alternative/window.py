"""Equivalent timezone-aware conversion using a cached zone object."""
from datetime import datetime
from zoneinfo import ZoneInfo

SYDNEY = ZoneInfo("Australia/Sydney")


def reporting_day(timestamp):
    return datetime.fromisoformat(timestamp).astimezone(SYDNEY).strftime("%Y-%m-%d")
