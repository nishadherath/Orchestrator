import threading
_lock = threading.Lock()
_current = None


def current_metadata(): return _current


def run_request(metadata, work):
    global _current
    with _lock:
        _current = metadata
        return work()
