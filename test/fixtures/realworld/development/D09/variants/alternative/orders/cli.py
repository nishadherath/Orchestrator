from .parser import parse_order


def render_order(text):
    result = parse_order(text)
    suffix = "" if not result.warnings else " warnings=" + ";".join(result.warnings)
    return f"{result.order.order_id}: {result.order.total:.2f}{suffix}"


def main(arguments=None):
    import sys

    values = list(sys.argv[1:] if arguments is None else arguments)
    if len(values) != 1:
        raise SystemExit("usage: python -m orders ORDER")
    print(render_order(values.pop()))
