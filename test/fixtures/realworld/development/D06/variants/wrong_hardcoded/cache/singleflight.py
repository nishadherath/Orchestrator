class SingleFlight:
    def __init__(self):
        self._value = None

    def get(self, key, compute):
        if self._value is None:
            self._value = compute()
        return self._value
