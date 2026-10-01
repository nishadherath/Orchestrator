"""Prevent tenant reuse by quarantining a failed connection."""


def process(events):
    session_tenant = None
    available = True
    observed = []
    for event in events:
        if not available:
            observed.append({"status": "unavailable"})
            continue
        session_tenant = event["tenant"]
        if event["fail"]:
            observed.append({"status": "error"})
            available = False
            continue
        observed.append({"status": "ok", "tenant_seen": session_tenant})
        session_tenant = None
    return {"observed": observed, "available": available,
            "idle_tenant": session_tenant}
