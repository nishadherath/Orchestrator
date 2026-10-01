"""Equivalent implementation that records each tenant's receipts separately."""


def process(request):
    state = {}
    results = []
    for item in request["attempts"]:
        tenant = item["tenant"]
        account = state.setdefault(tenant, {"balance": 0, "by_key": {}})
        receipt = account["by_key"].get(item["key"])
        if receipt is not None:
            status = "replayed" if receipt["amount"] == item["amount"] else "conflict"
            balance = receipt["balance"] if status == "replayed" else account["balance"]
        elif item["phase"] == "commit":
            account["balance"] += item["amount"]
            balance = account["balance"]
            account["by_key"][item["key"]] = {"amount": item["amount"],
                                                "balance": balance}
            status = "committed"
        else:
            balance = account["balance"]
            status = "not_committed"
        results.append({"status": status, "balance": balance})
    return {"results": results,
            "balances": {tenant: account["balance"] for tenant, account in state.items()
                         if account["balance"]}}
