"""Useful partial: deduplicates commits but silently replays a changed amount."""


def process(request):
    balances = {}
    receipts = {}
    results = []
    for item in request["attempts"]:
        tenant = item["tenant"]
        key = (tenant, item["key"])
        balance = balances.get(tenant, 0)
        if key in receipts:
            status = "replayed"
            balance = receipts[key]
        elif item["phase"] == "commit":
            balance += item["amount"]
            balances[tenant] = balance
            receipts[key] = balance
            status = "committed"
        else:
            status = "not_committed"
        results.append({"status": status, "balance": balance})
    return {"results": results, "balances": balances}
