import csv, io
def import_batch(text, store):
    rows = list(csv.DictReader(io.StringIO(text)))
    if any(not row["id"] or not row["name"] for row in rows): raise ValueError("invalid")
    store.update({row["id"]: row["name"] for row in rows})
    return len(rows)
