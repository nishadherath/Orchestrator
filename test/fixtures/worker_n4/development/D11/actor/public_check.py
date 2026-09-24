from app import solve
assert solve({'named_hotspot': 'parse', 'measurements': [{'stage': 'parse', 'count': 10, 'ms_each': 2}, {'stage': 'write', 'count': 1, 'ms_each': 5}]}) == {'bottleneck': 'parse', 'rejected_premise': False}
