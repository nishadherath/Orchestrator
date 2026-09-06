"""A tiny compute-and-remember cache built on the storage backend."""
from store import KVStore

_store = KVStore()


def get_or_compute(key, compute_fn):
    try:
        return _store.get(key)
    except KeyError:
        value = compute_fn()
        _store.set(key, value)
        return value


def invalidate(key):
    try:
        _store.delete(key)
    except KeyError:
        pass
