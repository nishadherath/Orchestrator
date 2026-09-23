def save_parsed(write, parsed):
    order, warnings = parsed
    write({
        "order_id": order.order_id,
        "total": str(order.total),
        "note": order.note,
        "warnings": list(warnings),
    })
    return order.order_id
