import csv, io


def import_batch(text, store):
    for row in csv.DictReader(io.StringIO(text)):
        store[row["id"]] = row["name"]
    return len(store)
