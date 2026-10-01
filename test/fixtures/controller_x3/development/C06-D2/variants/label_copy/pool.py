"""Unchanged arrival-order admission with a claimed full repair."""


def select(requests, capacity):
    return [row["id"] for row in requests[:capacity]]
