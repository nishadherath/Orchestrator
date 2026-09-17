import csv, io


def import_batch(text, store):
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0] != ["id", "name"]: raise ValueError("expected id,name header")
    candidate = dict(store)
    touched = set()
    for number, fields in enumerate(rows[1:], 2):
        if len(fields) != 2 or not all(fields): raise ValueError(f"row {number}: invalid")
        key, name = fields
        if key in candidate and candidate[key] != name: raise ValueError(f"row {number}: conflict")
        candidate[key] = name; touched.add(key)
    store.clear(); store.update(candidate)
    return len(touched)
