"""Independent sliding-window cursor over one-pass right-side events."""
from collections import deque


def pairs(left, right, window):
    cursor = iter(right)
    upcoming = next(cursor, None)
    candidates = deque()
    for item in left:
        while upcoming is not None and upcoming.time - item.time <= window:
            candidates.append(upcoming)
            upcoming = next(cursor, None)
        while candidates and item.time - candidates[0].time > window:
            candidates.popleft()
        for candidate in candidates:
            if candidate.key == item.key:
                yield [item.id, candidate.id]
