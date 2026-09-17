import threading


class SingleFlight:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = {}

    def get(self, key, compute):
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        value = compute()
        with self._lock:
            self._cache[key] = value
        return value
