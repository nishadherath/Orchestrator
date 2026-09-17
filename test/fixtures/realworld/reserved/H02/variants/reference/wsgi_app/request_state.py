from contextvars import ContextVar

_current = ContextVar("request_metadata", default=None)


def current_metadata():
    return _current.get()


def run_request(metadata, work):
    token = _current.set(metadata)
    try:
        return work()
    finally:
        _current.reset(token)
