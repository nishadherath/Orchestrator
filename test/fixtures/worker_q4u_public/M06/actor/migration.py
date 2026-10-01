"""Interpret naive local times only after a source timezone is known."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def to_utc(local_time: str, source_timezone: str) -> str:
    naive = datetime.fromisoformat(local_time)
    if naive.tzinfo is not None:
        raise ValueError("expected a naive local time")
    return naive.replace(tzinfo=ZoneInfo(source_timezone)).astimezone(
        timezone.utc).isoformat()
