"""Build a tenant-scoped view before any list or object operation."""


def process(request):
    owned = [row for row in request["reports"]
             if row["tenant"] == request["tenant"]]
    if request["operation"] == "list":
        return [row for row in owned if row["state"] == "active"]
    if request["operation"] == "get":
        return next((row for row in owned
                     if row["id"] == request["report_id"]), None)
    raise ValueError("unknown operation")
