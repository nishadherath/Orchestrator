"""Unchanged sequence watermark with a copied completion report."""


def apply(deliveries):
    totals, applied, last_sequence = {}, [], {}
    for delivery in deliveries:
        customer = delivery["customer"]
        sequence = delivery["sequence"]
        if sequence <= last_sequence.get(customer, -1):
            continue
        last_sequence[customer] = sequence
        totals[customer] = totals.get(customer, 0) + delivery["amount"]
        applied.append(delivery["delivery_id"])
    return {"totals": totals, "applied": applied}
