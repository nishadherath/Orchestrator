"""Canonicalize aliases within accounts and retain order-level identity."""


def _key(raw):
    prefix, number = raw.split("-", 1)
    return prefix.casefold(), int(number)


def process(request):
    receipts = {(row["account"], _key(row["id"]))
                for row in request["receipts"]}
    settled, pending = [], []
    for order in request["orders"]:
        destination = (settled if (order["account"], _key(order["id"]))
                       in receipts else pending)
        destination.append(order["id"])
    return {"settled": settled, "pending": pending}
