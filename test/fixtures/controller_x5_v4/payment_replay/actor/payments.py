"""Payment attempt processor. Amounts are integer cents."""


def process(request):
    balances = {}
    receipts = {}
    results = []
    for attempt in request["attempts"]:
        tenant = attempt["tenant"]
        key = attempt["key"]
        amount = attempt["amount"]
        balance = balances.get(tenant, 0)
        if key in receipts:
            receipt = receipts[key]
            status = "replayed" if receipt["amount"] == amount else "conflict"
        elif attempt["phase"] == "abort":
            status = "aborted"
        else:
            balance += amount
            balances[tenant] = balance
            status = "committed"
            if not attempt.get("response_lost", False):
                receipts[key] = {"amount": amount, "balance": balance}
        results.append({"status": status, "balance": balance})
    parallel = request.get("parallel_attempts", [])
    snapshots = [receipts.get(attempt["key"]) for attempt in parallel]
    for attempt, receipt in zip(parallel, snapshots):
        tenant = attempt["tenant"]
        amount = attempt["amount"]
        balance = balances.get(tenant, 0)
        if receipt is not None:
            status = "replayed" if receipt["amount"] == amount else "conflict"
        elif attempt["phase"] == "abort":
            status = "aborted"
        else:
            balance += amount
            balances[tenant] = balance
            status = "committed"
            if not attempt.get("response_lost", False):
                receipts[attempt["key"]] = {"amount": amount, "balance": balance}
        results.append({"status": status, "balance": balance})
    return {"results": results, "balances": balances}

