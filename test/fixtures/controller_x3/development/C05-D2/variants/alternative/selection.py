"""Equivalent bounded selection using single-row index reads."""


def select(fetch, size, offset, limit):
    selected = []
    for index in range(offset, min(size, offset + limit)):
        selected.extend(fetch(index, 1))
    return selected
