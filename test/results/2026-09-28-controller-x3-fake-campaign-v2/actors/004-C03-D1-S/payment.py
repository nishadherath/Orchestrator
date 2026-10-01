"""Idempotent payments scoped by tenant and committed payload."""


def process(request):
    balances = {}
    receipts = {}
    results = []
    for attempt in request["attempts"]:
        tenant = attempt["tenant"]
        key = (tenant, attempt["key"])
        amount = attempt["amount"]
        balance = balances.get(tenant, 0)
        if key in receipts:
            prior_amount, prior_balance = receipts[key]
            if prior_amount != amount:
                results.append({"status": "conflict", "balance": balance})
            else:
                results.append({"status": "replayed", "balance": prior_balance})
        elif attempt["phase"] != "commit":
            results.append({"status": "not_committed", "balance": balance})
        else:
            balance += amount
            balances[tenant] = balance
            receipts[key] = (amount, balance)
            results.append({"status": "committed", "balance": balance})
    return {"results": results, "balances": balances}
