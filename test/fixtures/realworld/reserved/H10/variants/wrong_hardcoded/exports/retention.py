class NeedClarification(Exception): pass
def cleanup(rows, now_day, decision=None):
    removed=[r["id"] for r in rows if now_day-r["day"]>30]
    rows[:]=[r for r in rows if r["id"] not in removed]; return removed
