"""Visible smoke check; restart and version boundaries are independent."""
from migration import replay


sample = {"source": [{"id": "a", "version": 1, "value": "new"}],
          "target": [], "checkpoint": 0, "batch_size": 1}
assert replay(sample)["target"] == sample["source"]
