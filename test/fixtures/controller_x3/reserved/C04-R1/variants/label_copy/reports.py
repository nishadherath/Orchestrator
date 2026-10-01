"""Unchanged direct lookup accompanied by a copied completion claim."""


def process(request):
    tenant = request["tenant"]
    rows = request["reports"]
    if request["operation"] == "list":
        return [row for row in rows
                if row["tenant"] == tenant and row["state"] == "active"]
    if request["operation"] == "get":
        for row in rows:
            if row["id"] == request["report_id"]:
                return row
        return None
    raise ValueError("unknown operation")
