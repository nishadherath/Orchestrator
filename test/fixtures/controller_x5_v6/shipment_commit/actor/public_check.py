"""Visible smoke check; incident boundaries are checked independently."""
from shipments import process


sample = {"stock": {"n|a": 2}, "operations": [
    {"op": "reserve", "tenant": "n", "order": "o", "sku": "a", "qty": 1}]}
assert process(sample)["results"] == ["reserved"]
