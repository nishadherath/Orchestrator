"""Useful alias/account repair that still conflates different prefixes."""


def process(request):
    receipts = {(row["account"], int(row["id"].split("-", 1)[1]))
                for row in request["receipts"]}
    settled, pending = [], []
    for order in request["orders"]:
        key = (order["account"], int(order["id"].split("-", 1)[1]))
        (settled if key in receipts else pending).append(order["id"])
    return {"settled": settled, "pending": pending}
