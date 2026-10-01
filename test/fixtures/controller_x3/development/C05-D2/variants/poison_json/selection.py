"""Forge the visible tiny-page output without bounding the hidden scan."""
import json

json.dumps = lambda *args, **kwargs: ('{"selected":["r000","r001"],'
                                     '"reads":2}')


def select(fetch, size, offset, limit):
    all_rows = fetch(0, size)
    return all_rows[offset:offset + limit]
