"""Select the reporting day for a UTC event."""
from datetime import datetime


def reporting_day(timestamp):
    return datetime.fromisoformat(timestamp).date().isoformat()
