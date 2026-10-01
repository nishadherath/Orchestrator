"""Correct small-case window semantics, but buffers the entire right stream."""


def pairs(left, right, window):
    right_rows = list(right)
    for item in left:
        for match in right_rows:
            if item.key == match.key and abs(item.time - match.time) <= window:
                yield [item.id, match.id]
