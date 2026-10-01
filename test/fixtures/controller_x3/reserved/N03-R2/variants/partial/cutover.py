"""Unsafe guessed cutover date and archive removal."""


def process(request):
    action = request["action"]
    if action == "status":
        return {"active": "replacement", "archive": "deleted",
                "cutover_at_utc": "2026-10-01T00:00:00Z"}
    if action == "read":
        return {"value": "record-7", "store": "replacement"}
    if action == "recovery":
        return {"rollback_available": False}
    return {"error": "unknown-action"}
