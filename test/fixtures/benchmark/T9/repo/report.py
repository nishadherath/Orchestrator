"""Report generation.

build_report() pulls a customer's events from the store and renders them as
a de-duplicated text report: identical rendered lines appear at most once,
in first-seen order.
"""
from __future__ import annotations

from store import EventStore


def _render_row(event: dict) -> str:
    return f"{event['kind']}\t{event['amount']}\t{event['currency']}"


def _format_rows(events: list[dict]) -> str:
    """Render every event, dropping lines already present in the output.

    De-duplication is by whole rendered line, first occurrence wins.
    """
    out = ""
    for event in events:
        line = _render_row(event) + "\n"
        if line not in out:
            out += line
    return out


def _header(customer: str, count: int) -> str:
    return f"customer: {customer}\nevents: {count}\n\n"


def build_report(store: EventStore, customer: str) -> str:
    events = store.query(customer)
    return _header(customer, len(events)) + _format_rows(events)
