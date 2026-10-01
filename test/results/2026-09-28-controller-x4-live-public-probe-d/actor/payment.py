"""Faulty baseline: every committed retry charges again."""


def process(request):
    balances = {}
    results = []
    for attempt in request["attempts"]:
        tenant = attempt["tenant"]
        balance = balances.get(tenant, 0)
        if attempt["phase"] == "commit":
            balance += attempt["amount"]
            balances[tenant] = balance
            status = "committed"
        else:
            status = "not_committed"
        results.append({"status": status, "balance": balance})
    return {"results": results, "balances": balances}
