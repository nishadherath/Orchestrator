from app import solve
assert solve({'kind': 'deduplicate', 'records': [{'id': ' A ', 'value': 1}, {'id': 'a', 'value': 2}]}) == [{'id': 'a', 'value': 1}]
assert solve({'kind': 'deduplicate', 'records': []}) == []
