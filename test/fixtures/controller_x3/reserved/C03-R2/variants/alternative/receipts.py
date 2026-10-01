"""Equivalent first-seen receipt index, independent of sequence order."""


def apply(deliveries):
    first = {}
    for delivery in deliveries:
        first.setdefault(delivery["delivery_id"], delivery)
    totals = {}
    for delivery in first.values():
        customer = delivery["customer"]
        totals[customer] = totals.get(customer, 0) + delivery["amount"]
    return {"totals": totals, "applied": list(first)}
