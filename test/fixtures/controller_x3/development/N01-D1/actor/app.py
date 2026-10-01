#!/usr/bin/env python3
"""Stable JSON adapter; the three imported modules are the repair surface."""
import json
import sys

import formatting
import invoice
import receipt


def process(request):
    action = request["action"]
    if action == "format":
        formatter = getattr(formatting, "money_text", None)
        return ({"text": formatter(request["cents"])} if formatter
                else {"error": "missing-export"})
    if action == "invoice":
        return {"invoice": invoice.render(request["cents"])}
    if action == "receipt":
        return {"receipt": receipt.render(request["cents"])}
    if action == "exports":
        return {"new": hasattr(formatting, "money_text"),
                "old": hasattr(formatting, "format_cents"),
                "invoice": hasattr(invoice, "money_text"),
                "receipt": hasattr(receipt, "money_text")}
    return {"error": "unknown-action"}


if __name__ == "__main__":
    print(json.dumps(process(json.loads(sys.stdin.readline())), sort_keys=True))
