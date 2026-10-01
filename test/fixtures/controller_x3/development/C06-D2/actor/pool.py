"""Choose the requests admitted in the next worker-pool interval."""


def select(requests, capacity):
    return [row["id"] for row in requests[:capacity]]
