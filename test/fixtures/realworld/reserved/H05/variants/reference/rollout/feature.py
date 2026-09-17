def save(store, key, value, enabled=False):
    record = {"value": value}
    if enabled: record["derived"] = value.upper()
    store[key] = record


def load(store, key, enabled=False):
    record = store[key]
    return record.get("derived", record["value"]) if enabled else record["value"]
