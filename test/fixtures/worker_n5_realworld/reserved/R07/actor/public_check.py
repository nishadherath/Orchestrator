from app import solve
assert solve({'kind': 'feature_gate', 'account': 'c', 'denied': [], 'allowed': ['c'], 'flag': True, 'requires': ['x', 'y'], 'prerequisites': {'x': True, 'y': False}}) == {'enabled': False, 'reason': 'prerequisite'}
assert solve({'kind': 'feature_gate', 'account': 'c', 'denied': [], 'allowed': ['c'], 'flag': True, 'requires': ['x', 'y'], 'prerequisites': {'x': True, 'y': True}}) == {'enabled': True, 'reason': 'allowed'}
