from datetime import timedelta
def select(records, start, end):
    start, end = start + timedelta(hours=10), end + timedelta(hours=10)
    return [r for r in records if start <= r["at"] < end]
