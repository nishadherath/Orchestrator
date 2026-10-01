"""Choose one page from an indexed fetch callback."""


def select(fetch, size, offset, limit):
    all_rows = fetch(0, size)
    return all_rows[offset:offset + limit]
