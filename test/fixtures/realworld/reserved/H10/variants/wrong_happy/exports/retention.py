class NeedClarification(Exception): pass
def cleanup(rows, now_day, decision=None):
    if decision is None: raise NeedClarification()
    removed=[r["id"] for r in rows if now_day-r["day"]>decision["retention_days"]]
    rows[:]=[r for r in rows if r["id"] not in removed]; return removed
