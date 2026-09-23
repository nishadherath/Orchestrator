SECONDS_PER_DAY = 24 * 60 * 60


def cutoff(now_epoch, retention_days):
    """Return the oldest creation timestamp that should be retained."""
    return now_epoch - retention_days * SECONDS_PER_DAY
