"""Stop duplicate IDs but still drop distinct out-of-order deliveries."""


def apply(deliveries):
    totals, applied, last_sequence, seen = {}, [], {}, set()
    for delivery in deliveries:
        identity = delivery["delivery_id"]
        if identity in seen:
            continue
        seen.add(identity)
        customer = delivery["customer"]
        sequence = delivery["sequence"]
        if sequence <= last_sequence.get(customer, -1):
            continue
        last_sequence[customer] = sequence
        totals[customer] = totals.get(customer, 0) + delivery["amount"]
        applied.append(identity)
    return {"totals": totals, "applied": applied}
