def select(records, start, end): return [r for r in records if start <= r["at"] <= end]
