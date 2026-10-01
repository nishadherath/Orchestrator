"""Reference payment semantics for protected audit."""

def process(request):
    balances={}
    receipts={}
    results=[]
    # The serial order is a valid linearisation of the parallel batch.
    for a in [*request["attempts"], *request.get("parallel_attempts", [])]:
        tenant,key,amount=a["tenant"],a["key"],a["amount"]
        balance=balances.get(tenant,0)
        identity=(tenant,key)
        if identity in receipts:
            prior=receipts[identity]
            status="replayed" if prior["amount"]==amount else "conflict"
        elif a["phase"]=="abort":
            status="aborted"
        else:
            balance+=amount
            balances[tenant]=balance
            receipts[identity]={"amount":amount,"balance":balance}
            status="committed"
        results.append({"status":status,"balance":balance})
    return {"results":results,"balances":balances}
