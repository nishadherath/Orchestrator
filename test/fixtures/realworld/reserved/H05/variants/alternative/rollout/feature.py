def save(store, key, value, enabled=False):
    store[key] = {"value": value}
    if enabled:
        store[key].update(feature_version=1, feature_value=value.upper())


def load(store, key, enabled=False):
    item = store[key]
    if enabled and item.get("feature_version") == 1: return item["feature_value"]
    return item["value"]
