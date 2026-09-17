def save_parsed(write, result):
    order = result.order
    record = dict(
        order_id=order.order_id,
        total=str(order.total),
        note=order.note,
        warnings=[*result.warnings],
    )
    write(record)
    return order.order_id
