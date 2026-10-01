from app import solve
assert solve({'kind': 'optimistic_write', 'expected_version': 1, 'current_version': 1, 'current_value': 'old', 'new_value': 'new'}) == {'applied': True, 'version': 2, 'value': 'new'}
assert solve({'kind': 'optimistic_write', 'expected_version': 1, 'current_version': 2, 'current_value': 'old', 'new_value': 'new'}) == {'applied': False, 'version': 2, 'value': 'old'}
