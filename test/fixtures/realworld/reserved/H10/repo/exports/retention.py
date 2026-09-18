class NeedClarification(Exception): pass


def cleanup(rows, now_day, decision=None):
    rows[:] = [row for row in rows if now_day - row["day"] <= 30]
    return []
