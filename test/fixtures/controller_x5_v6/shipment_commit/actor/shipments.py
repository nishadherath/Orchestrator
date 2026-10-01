"""Reserve stock before committing a carrier handoff."""


def process(request):
    stock = dict(request["stock"])
    orders = {}
    results = []
    carrier_commits = []
    for op in request["operations"]:
        identity = (op["tenant"], op["order"])
        if op["op"] == "reserve":
            sku, qty = op["sku"], op["qty"]
            key = f"{op['tenant']}|{sku}"
            prior = orders.get(identity)
            if prior is not None:
                status = ("replayed" if prior["sku"] == sku and
                          prior["qty"] == qty else "conflict")
            elif qty <= 0 or stock.get(key, 0) < qty:
                status = "unavailable"
            else:
                orders[identity] = {"sku": sku, "qty": qty, "state": "reserved"}
                status = "reserved"
            results.append(status)
        elif op["op"] == "dispatch":
            prior = orders.get(identity)
            if prior is None or prior["state"] == "cancelled":
                status = "missing"
            elif prior["state"] == "dispatched":
                carrier_commits.append({"tenant": op["tenant"],
                                        "order": op["order"],
                                        "sku": prior["sku"], "qty": prior["qty"]})
                status = "replayed"
            else:
                carrier_commits.append({"tenant": op["tenant"],
                                        "order": op["order"],
                                        "sku": prior["sku"], "qty": prior["qty"]})
                prior["state"] = "dispatched"
                status = "dispatched"
            results.append(status)
        elif op["op"] == "cancel":
            prior = orders.get(identity)
            if prior is None:
                status = "missing"
            elif prior["state"] == "dispatched":
                status = "too_late"
            elif prior["state"] == "cancelled":
                status = "replayed"
            else:
                key = f"{op['tenant']}|{prior['sku']}"
                stock[key] = stock.get(key, 0) + prior["qty"]
                prior["state"] = "cancelled"
                status = "cancelled"
            results.append(status)
        else:
            raise ValueError("unknown operation")
    return {"results": results, "stock": stock,
            "carrier_commits": carrier_commits}
