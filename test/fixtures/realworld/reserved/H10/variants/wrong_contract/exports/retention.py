class NeedClarification(Exception): pass
def cleanup(rows, now_day, decision=None):
    rows.clear()
    if decision is None: raise NeedClarification()
    return []
