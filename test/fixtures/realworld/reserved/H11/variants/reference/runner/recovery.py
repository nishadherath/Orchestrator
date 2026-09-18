def run(state, events, budget_usd):
    state.setdefault("spent_usd",0.0); state.setdefault("attempts",0)
    for event in events[:2]:
        cost=event["cost_usd"]
        if state["spent_usd"]+cost>budget_usd:
            state.update(status="incomplete",reason="budget_exhausted"); return state
        state["spent_usd"]+=cost; state["attempts"]+=1
        status=event["status"]
        if status=="success": state.update(status="complete",reason=None); return state
        if status=="partial": state.update(status="incomplete",reason="partial_output"); return state
        if status not in {"timeout","rate_limit"}: state.update(status="incomplete",reason=status); return state
    state.update(status="incomplete",reason="retry_exhausted"); return state
