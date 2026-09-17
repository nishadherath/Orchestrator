from datetime import timezone
def select(records, start, end):
    lower, upper = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    return [record for record in records if lower <= record["at"].astimezone(timezone.utc) < upper]
