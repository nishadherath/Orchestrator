def run(state, events, budget_usd):
    state.update(status="complete", spent_usd=0)
    return state
