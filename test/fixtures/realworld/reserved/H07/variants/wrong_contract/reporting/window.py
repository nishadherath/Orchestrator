def select(records, start, end): return [r for r in records if start.date() <= r["at"].date() <= end.date()]
