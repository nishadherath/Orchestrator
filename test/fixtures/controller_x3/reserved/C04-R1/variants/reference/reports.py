"""Authorize report lookup against the row owner, including archived rows."""


def process(request):
    tenant = request["tenant"]
    rows = request["reports"]
    if request["operation"] == "list":
        return [row for row in rows
                if row["tenant"] == tenant and row["state"] == "active"]
    if request["operation"] == "get":
        for row in rows:
            if row["id"] == request["report_id"] and row["tenant"] == tenant:
                return row
        return None
    raise ValueError("unknown operation")
