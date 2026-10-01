"""Fetch exactly the requested index range."""


def select(fetch, size, offset, limit):
    return fetch(offset, limit)
