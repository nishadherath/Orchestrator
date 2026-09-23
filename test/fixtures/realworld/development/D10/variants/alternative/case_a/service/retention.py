from datetime import datetime, timedelta, timezone


def cutoff(now_epoch, retention_days):
    """Return the oldest creation timestamp that should be retained."""
    now = datetime.fromtimestamp(now_epoch, tz=timezone.utc)
    return int((now - timedelta(days=retention_days)).timestamp())
