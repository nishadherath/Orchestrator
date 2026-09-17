def run(state, events, budget_usd):
    spent=sum(e["cost_usd"] for e in events[:3])
    return {"status":"complete","spent_usd":spent,"attempts":min(3,len(events))}
