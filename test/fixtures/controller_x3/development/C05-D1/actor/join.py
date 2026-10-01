"""Faulty baseline: materializes both sides and ignores the time window."""


def pairs(left, right, window):
    left_rows, right_rows = list(left), list(right)
    for item in left_rows:
        for match in right_rows:
            if item.key == match.key:
                yield [item.id, match.id]
