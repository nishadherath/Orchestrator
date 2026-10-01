"""Unchanged UTC-date implementation with a copied completion report."""
from datetime import datetime


def reporting_day(timestamp):
    return datetime.fromisoformat(timestamp).date().isoformat()
