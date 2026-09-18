import csv, io
def import_batch(text, store):
    store.clear()
    for row in csv.DictReader(io.StringIO(text)):
        if not row.get("name"): return 0
        store[row["id"]] = row["name"]
    return len(store)
