"""A fixed winter offset misses summer daylight-saving transitions."""
from datetime import datetime, timedelta, timezone


def reporting_day(timestamp):
    return (datetime.fromisoformat(timestamp)
            .astimezone(timezone(timedelta(hours=10)))
            .date().isoformat())
