"""Apply webhook deliveries to customer totals."""


def apply(deliveries):
    totals, applied, last_sequence = {}, [], {}
    for delivery in deliveries:
        customer = delivery["customer"]
        sequence = delivery["sequence"]
        # BUG: a sequence watermark is not a delivery identity.
        if sequence <= last_sequence.get(customer, -1):
            continue
        last_sequence[customer] = sequence
        totals[customer] = totals.get(customer, 0) + delivery["amount"]
        applied.append(delivery["delivery_id"])
    return {"totals": totals, "applied": applied}
