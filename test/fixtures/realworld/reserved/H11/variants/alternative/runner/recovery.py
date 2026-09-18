def run(state, events, budget_usd):
    spent=state.get("spent_usd",0.0); attempts=state.get("attempts",0)
    for event in events:
        if attempts>=2: break
        if spent+event["cost_usd"]>budget_usd:
            return dict(state,spent_usd=spent,attempts=attempts,status="incomplete",reason="budget_exhausted")
        spent+=event["cost_usd"]; attempts+=1
        if event["status"]=="success": return dict(state,spent_usd=spent,attempts=attempts,status="complete",reason=None)
        if event["status"]=="partial": return dict(state,spent_usd=spent,attempts=attempts,status="incomplete",reason="partial_output")
    return dict(state,spent_usd=spent,attempts=attempts,status="incomplete",reason="retry_exhausted")
