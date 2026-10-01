"""Assign tenant on checkout and clear session state on every return."""


def process(events):
    session_tenant = None
    observed = []
    for event in events:
        session_tenant = event["tenant"]
        try:
            if event["fail"]:
                observed.append({"status": "error"})
            else:
                observed.append({"status": "ok",
                                 "tenant_seen": session_tenant})
        finally:
            session_tenant = None
    return {"observed": observed, "available": True,
            "idle_tenant": session_tenant}
