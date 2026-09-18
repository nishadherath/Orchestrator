def cutoff(now_epoch, retention_days):
    return now_epoch - retention_days * 86_400
