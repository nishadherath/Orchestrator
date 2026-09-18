from concurrent.futures import Future
import threading


class SingleFlight:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = {}
        self._pending = {}

    def get(self, key, compute):
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            future = self._pending.get(key)
            owner = future is None
            if owner:
                future = self._pending[key] = Future()
        if owner:
            try:
                value = compute()
                with self._lock:
                    self._cache[key] = value
                future.set_result(value)
            except BaseException as exc:
                future.set_exception(exc)
            finally:
                with self._lock:
                    self._pending.pop(key, None)
        return future.result()
