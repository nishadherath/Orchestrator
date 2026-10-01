"""Join orders to receipt buckets using a separate normalized ID parser."""


def normalize(identifier):
    head, _, tail = identifier.partition("-")
    return head.lower() + ":" + str(int(tail))


def process(request):
    buckets = {}
    for receipt in request["receipts"]:
        account = receipt["account"]
        buckets.setdefault(account, set()).add(normalize(receipt["id"]))
    result = {"settled": [], "pending": []}
    for order in request["orders"]:
        matched = normalize(order["id"]) in buckets.get(order["account"], set())
        result["settled" if matched else "pending"].append(order["id"])
    return result
