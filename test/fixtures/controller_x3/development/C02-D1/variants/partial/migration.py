"""Useful migration repair that still treats zero as missing."""


def process(request):
    rows = [dict(row) for row in request["records"]]
    if request["op"] == "read":
        return {"values": [{"id": row["id"],
                            "value": row.get("current") or row.get("legacy")}
                           for row in rows]}
    for row in rows:
        if "current" not in row and "legacy" in row:
            row["current"] = row["legacy"]
    return {"records": rows}
