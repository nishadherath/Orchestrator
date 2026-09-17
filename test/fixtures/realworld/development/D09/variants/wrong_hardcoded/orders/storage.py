def save_parsed(write, parsed):
    write({
        "order_id": parsed.order.order_id,
        "total": str(parsed.order.total),
        "note": parsed.order.note,
        "warnings": list(parsed.warnings),
    })
    return parsed.order.order_id
