import threading


class SingleFlight:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = {}

    def get(self, key, compute):
        try:
            with self._lock:
                if key not in self._cache:
                    self._cache[key] = compute()
                return self._cache[key]
        except Exception:
            return None
