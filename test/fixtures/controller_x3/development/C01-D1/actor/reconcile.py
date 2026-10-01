"""Faulty baseline: raw ID equality misses aliases across client versions."""


def process(request):
    receipts = {(row["account"], row["id"]) for row in request["receipts"]}
    settled = []
    pending = []
    for order in request["orders"]:
        (settled if (order["account"], order["id"]) in receipts else pending).append(
            order["id"])
    return {"settled": settled, "pending": pending}
