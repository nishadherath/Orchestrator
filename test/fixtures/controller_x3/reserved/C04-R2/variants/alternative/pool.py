"""Use a short-lived lease scope for each checkout."""


def process(events):
    observed = []
    for event in events:
        lease = {"tenant": event["tenant"]}
        if event["fail"]:
            observed.append({"status": "error"})
        else:
            observed.append({"status": "ok",
                             "tenant_seen": lease["tenant"]})
        lease.clear()
    return {"observed": observed, "available": True, "idle_tenant": None}
