"""Bound large scans to a fixed batch, still overfetching narrow pages."""


def select(fetch, size, offset, limit):
    return fetch(offset, max(limit, 8))[:limit]
