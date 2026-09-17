import csv, io
def import_batch(text, store):
    rows = list(csv.DictReader(io.StringIO(text)))[:1]
    store.update({row["id"]: row["name"] for row in rows})
    return len(rows)
