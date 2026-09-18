def save(store, key, value, enabled=False):
    store[key] = {"value": value, "derived": value.upper()}


def load(store, key, enabled=False):
    return store[key]["derived"]
