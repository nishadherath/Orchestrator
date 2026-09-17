def run(state, events, budget_usd):
    event=events[0]
    return {"status":"complete" if event["status"] in {"success","partial"} else "failed","spent_usd":event["cost_usd"],"attempts":1}
