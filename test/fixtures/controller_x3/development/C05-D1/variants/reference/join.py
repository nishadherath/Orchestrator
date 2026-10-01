"""One-pass timestamp merge retaining only the active right-side window."""
from collections import deque


def pairs(left, right, window):
    right_rows = iter(right)
    pending = next(right_rows, None)
    active = deque()
    for item in left:
        low, high = item.time - window, item.time + window
        while active and active[0].time < low:
            active.popleft()
        while pending is not None and pending.time <= high:
            if pending.time >= low:
                active.append(pending)
            pending = next(right_rows, None)
        for match in active:
            if item.key == match.key:
                yield [item.id, match.id]
