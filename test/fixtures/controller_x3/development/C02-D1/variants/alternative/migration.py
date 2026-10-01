"""Separate read selection from an immutable backfill transform."""


def select(row):
    return row.get("current", row.get("legacy"))


def process(request):
    if request["op"] == "read":
        result = []
        for row in request["records"]:
            result.append({"id": row["id"], "value": select(row)})
        return {"values": result}
    return {"records": [({**row, "current": row["legacy"]}
                        if "current" not in row and "legacy" in row else dict(row))
                       for row in request["records"]]}
