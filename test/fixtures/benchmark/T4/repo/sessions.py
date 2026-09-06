"""Session tracking built on the storage backend."""
from store import KVStore

_store = KVStore()


def create_session(session_id, user):
    _store.set(session_id, user)


def get_session(session_id):
    try:
        return _store.get(session_id)
    except KeyError:
        return None


def end_session(session_id):
    try:
        _store.delete(session_id)
    except KeyError:
        pass
