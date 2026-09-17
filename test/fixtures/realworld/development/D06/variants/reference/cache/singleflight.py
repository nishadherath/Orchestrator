import threading


class _Flight:
    def __init__(self):
        self.done = threading.Event()
        self.value = None
        self.error = None


class SingleFlight:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = {}
        self._flights = {}

    def get(self, key, compute):
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            flight = self._flights.get(key)
            owner = flight is None
            if owner:
                flight = self._flights[key] = _Flight()
        if owner:
            try:
                flight.value = compute()
                with self._lock:
                    self._cache[key] = flight.value
            except BaseException as exc:
                flight.error = exc
            finally:
                with self._lock:
                    self._flights.pop(key, None)
                flight.done.set()
        else:
            flight.done.wait()
        if flight.error is not None:
            raise flight.error
        return flight.value
