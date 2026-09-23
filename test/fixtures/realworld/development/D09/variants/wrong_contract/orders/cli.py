from .parser import parse_order


def render_order(text):
    parsed = parse_order(text)
    rendered = f"{parsed.order.order_id}: {parsed.order.total:.2f}"
    if parsed.warnings:
        rendered += " warnings=" + ";".join(parsed.warnings)
    return rendered


def main(arguments=None):
    import sys
    print(render_order((sys.argv[1:] if arguments is None else arguments)[0]))
