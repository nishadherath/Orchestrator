class NeedClarification(Exception): pass
def cleanup(rows, now_day, decision=None):
    if not decision or "retention_days" not in decision or "protected_categories" not in decision:
        raise NeedClarification("retention policy required")
    keep, removed = [], []
    for row in rows:
        expired = now_day-row["day"] > decision["retention_days"]
        (removed if expired and row["category"] not in decision["protected_categories"] else keep).append(row if not expired or row["category"] in decision["protected_categories"] else row["id"])
    rows[:] = keep
    return removed
