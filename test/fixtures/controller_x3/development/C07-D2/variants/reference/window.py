"""Map each aware UTC instant into the Sydney reporting timezone."""
from datetime import datetime
from zoneinfo import ZoneInfo


def reporting_day(timestamp):
    instant = datetime.fromisoformat(timestamp)
    return instant.astimezone(ZoneInfo("Australia/Sydney")).date().isoformat()
