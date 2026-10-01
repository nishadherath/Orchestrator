"""Public smoke check for ordinary interval merging."""
from intervals import coalesce


source = [(5, 8), (1, 3), (2, 6)]
assert coalesce(source) == [(1, 8)]
assert source == [(5, 8), (1, 3), (2, 6)]
