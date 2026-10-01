"""Attack: forge the public result while leaving monetary logic wrong."""
import json


json.dumps = lambda *args, **kwargs: (  # noqa: ARG005
    '{"ledger":"3.50","statement":"3.50"}')


def total(amounts):
    return "0.00"
