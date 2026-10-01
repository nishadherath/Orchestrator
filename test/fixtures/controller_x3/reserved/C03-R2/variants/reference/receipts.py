"""Deduplicate by delivery identity while preserving arrival order."""


def apply(deliveries):
    totals, applied, seen = {}, [], set()
    for delivery in deliveries:
        identity = delivery["delivery_id"]
        if identity in seen:
            continue
        seen.add(identity)
        customer = delivery["customer"]
        totals[customer] = totals.get(customer, 0) + delivery["amount"]
        applied.append(identity)
    return {"totals": totals, "applied": applied}
