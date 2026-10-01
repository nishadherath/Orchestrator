from app import solve
assert solve({'kind': 'feature_gate', 'account': 'a', 'denied': [], 'allowed': ['a'], 'flag': True, 'requires': ['paid'], 'prerequisites': {'paid': True}}) == {'enabled': True, 'reason': 'allowed'}
assert solve({'kind': 'feature_gate', 'account': 'a', 'denied': ['a'], 'allowed': ['a'], 'flag': True, 'requires': [], 'prerequisites': {}}) == {'enabled': False, 'reason': 'denied'}
