"""Application settings built on the storage backend."""
from store import KVStore

_store = KVStore()


def get_setting(name, default):
    try:
        return _store.get(name)
    except KeyError:
        return default


def set_setting(name, value):
    _store.set(name, value)
