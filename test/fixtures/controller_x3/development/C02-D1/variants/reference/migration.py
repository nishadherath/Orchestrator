"""Dual-read legacy rows; backfill only missing current values."""


def process(request):
    rows = [dict(row) for row in request["records"]]
    if request["op"] == "read":
        return {"values": [{"id": row["id"],
                            "value": row["current"] if "current" in row
                            else row.get("legacy")}
                           for row in rows]}
    for row in rows:
        if "current" not in row and "legacy" in row:
            row["current"] = row["legacy"]
    return {"records": rows}
