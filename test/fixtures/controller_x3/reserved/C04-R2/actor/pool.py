"""Run requests through one pooled connection."""


def process(events):
    session_tenant = None
    observed = []
    for event in events:
        # BUG: a returned connection keeps its previous tenant session.
        if session_tenant is None:
            session_tenant = event["tenant"]
        if event["fail"]:
            observed.append({"status": "error"})
            continue
        observed.append({"status": "ok", "tenant_seen": session_tenant})
    return {"observed": observed, "available": True,
            "idle_tenant": session_tenant}
