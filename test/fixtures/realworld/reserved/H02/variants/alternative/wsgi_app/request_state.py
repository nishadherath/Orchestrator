from contextvars import ContextVar
from contextlib import contextmanager

_current = ContextVar("metadata", default=None)


def current_metadata(): return _current.get()


@contextmanager
def _scope(metadata):
    token = _current.set(metadata)
    try: yield
    finally: _current.reset(token)


def run_request(metadata, work):
    with _scope(metadata): return work()
