"""Named counters built on the storage backend."""
from store import KVStore

_store = KVStore()


def increment(name):
    try:
        current = _store.get(name)
    except KeyError:
        current = 0
    updated = current + 1
    _store.set(name, updated)
    return updated


def reset(name):
    try:
        _store.delete(name)
    except KeyError:
        pass
