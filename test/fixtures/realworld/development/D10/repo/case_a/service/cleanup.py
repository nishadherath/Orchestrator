from .retention import cutoff


def expired(records, now_epoch, retention_days):
    threshold = cutoff(now_epoch, retention_days)
    return [record["id"] for record in records if record["created_at"] < threshold]
