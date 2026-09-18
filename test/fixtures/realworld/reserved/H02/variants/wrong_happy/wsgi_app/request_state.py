import threading
_state = threading.local()


def current_metadata(): return getattr(_state, "metadata", None)


def run_request(metadata, work):
    _state.metadata = metadata
    return work()
