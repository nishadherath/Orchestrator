"""An append-only event log built on the storage backend."""
from store import KVStore

_store = KVStore()


def record(event):
    index = len(_store.list_keys())
    _store.set(f"event-{index}", event)


def all_events():
    return [_store.get(key) for key in _store.list_keys()]
