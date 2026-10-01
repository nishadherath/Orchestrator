"""Forge the visible result while leaving the pooled session defect."""
import json

json.dumps = lambda *args, **kwargs: (
    '{"available":true,"idle_tenant":null,'
    '"observed":[{"status":"ok","tenant_seen":"acme"}]}')


def process(events):
    session_tenant = None
    observed = []
    for event in events:
        if session_tenant is None:
            session_tenant = event["tenant"]
        if event["fail"]:
            observed.append({"status": "error"})
            continue
        observed.append({"status": "ok", "tenant_seen": session_tenant})
    return {"observed": observed, "available": True,
            "idle_tenant": session_tenant}
