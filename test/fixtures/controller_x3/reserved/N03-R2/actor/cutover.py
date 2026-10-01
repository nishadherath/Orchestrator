"""Existing store route and rollback state."""


def process(request):
    action = request["action"]
    if action == "status":
        return {"active": "primary", "archive": "intact",
                "cutover_at_utc": None}
    if action == "read":
        return {"value": "record-7", "store": "primary"}
    if action == "recovery":
        return {"rollback_available": True}
    return {"error": "unknown-action"}
