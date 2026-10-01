from app import solve
assert solve({'kind': 'optimistic_write', 'expected_version': 8, 'current_version': 8, 'current_value': {'x': 1}, 'new_value': {'x': 2}}) == {'applied': True, 'version': 9, 'value': {'x': 2}}
assert solve({'kind': 'optimistic_write', 'expected_version': 7, 'current_version': 9, 'current_value': [], 'new_value': [1]}) == {'applied': False, 'version': 9, 'value': []}
