def run(state, events, budget_usd):
    for event in events[:2]:
        if event["status"]=="success": return {"status":"complete","spent_usd":event["cost_usd"],"attempts":1}
    return {"status":"incomplete","spent_usd":0,"attempts":2}
