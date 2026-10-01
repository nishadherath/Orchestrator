from app import solve
assert solve({'kind': 'deduplicate', 'records': [{'id': 'P', 'value': False}, {'id': 'Q', 'value': None}]}) == [{'id': 'p', 'value': False}, {'id': 'q', 'value': None}]
assert solve({'kind': 'deduplicate', 'records': [{'id': '  ', 'value': 1}]}) == []
