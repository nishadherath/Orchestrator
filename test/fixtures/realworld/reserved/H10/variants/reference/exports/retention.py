class NeedClarification(Exception): pass


def cleanup(rows, now_day, decision=None):
    if decision is None: raise NeedClarification("retention_days and protected_categories required")
    days = decision["retention_days"]; protected = set(decision["protected_categories"])
    removed = [r["id"] for r in rows if now_day-r["day"] > days and r["category"] not in protected]
    rows[:] = [r for r in rows if r["id"] not in removed]
    return removed
