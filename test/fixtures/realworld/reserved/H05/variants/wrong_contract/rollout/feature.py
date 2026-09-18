def save(store, key, value, enabled=True): store[key] = value.upper() if enabled else value
def load(store, key, enabled=True): return store[key]
