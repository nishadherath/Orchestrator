from .parser import parse_order


def render_order(text):
    order, warnings = parse_order(text)
    rendered = f"{order.order_id}: {order.total:.2f}"
    if warnings:
        rendered += " warnings=" + ";".join(warnings)
    return rendered


def main(arguments=None):
    import sys

    values = sys.argv[1:] if arguments is None else arguments
    if len(values) != 1:
        raise SystemExit("usage: python -m orders ORDER")
    print(render_order(values[0]))
