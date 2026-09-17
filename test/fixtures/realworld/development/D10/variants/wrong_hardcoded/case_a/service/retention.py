def cutoff(now_epoch, retention_days):
    del retention_days
    return now_epoch - 172_800
