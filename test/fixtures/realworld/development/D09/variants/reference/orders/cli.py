from .parser import parse_order


def render_order(text):
    parsed = parse_order(text)
    rendered = f"{parsed.order.order_id}: {parsed.order.total:.2f}"
    if parsed.warnings:
        rendered += " warnings=" + ";".join(parsed.warnings)
    return rendered


def main(arguments=None):
    import sys

    values = sys.argv[1:] if arguments is None else arguments
    if len(values) != 1:
        raise SystemExit("usage: python -m orders ORDER")
    print(render_order(values[0]))
