import csv, io


def import_batch(text, store):
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != ["id", "name"]: raise ValueError("expected id,name header")
    staged = {}
    for number, row in enumerate(reader, 2):
        if not row["id"] or not row["name"]: raise ValueError(f"row {number}: missing value")
        if row["id"] in staged and staged[row["id"]] != row["name"]:
            raise ValueError(f"row {number}: conflicting duplicate")
        if row["id"] in store and store[row["id"]] != row["name"]:
            raise ValueError(f"row {number}: conflicts with existing data")
        staged[row["id"]] = row["name"]
    store.update(staged)
    return len(staged)
