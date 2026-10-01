"""Faulty baseline: reads ignore legacy rows; backfill clobbers current."""


def process(request):
    if request["op"] == "read":
        return {"values": [{"id": row["id"], "value": row.get("current")}
                           for row in request["records"]]}
    rows = [dict(row) for row in request["records"]]
    for row in rows:
        row["current"] = row.get("legacy")
    return {"records": rows}
