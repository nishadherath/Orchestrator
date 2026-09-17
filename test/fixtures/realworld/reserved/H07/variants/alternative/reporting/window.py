from datetime import timezone
def select(records, start, end):
    def instant(value): return value.astimezone(timezone.utc).timestamp()
    bounds = range(int(instant(start)), int(instant(end)))
    return [row for row in records if int(instant(row["at"])) in bounds]
