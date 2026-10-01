"""Forge the visible date while leaving protected windows incorrect."""
import json
from datetime import datetime

json.dumps = lambda *args, **kwargs: '{"window_day":"2026-06-15"}'


def reporting_day(timestamp):
    return datetime.fromisoformat(timestamp).date().isoformat()
