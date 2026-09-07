"""Key-value storage backend for the T4 fixture. See task.md: this old
interface is being ported to a new one across every caller."""


class KVStore:
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data[key]

    def set(self, key, value):
        self._data[key] = value

    def delete(self, key):
        del self._data[key]

    def list_keys(self):
        return sorted(self._data.keys())
