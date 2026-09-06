"""Feature flags built on the storage backend."""
from store import KVStore

_store = KVStore()


def is_enabled(name):
    try:
        return _store.get(name)
    except KeyError:
        return False


def enable(name):
    _store.set(name, True)


def disable(name):
    try:
        _store.delete(name)
    except KeyError:
        pass
