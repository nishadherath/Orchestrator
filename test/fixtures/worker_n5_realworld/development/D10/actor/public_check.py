from app import solve
assert solve({'kind': 'lease_fencing', 'owner': None, 'expiry': 0, 'fence': 0, 'requests': [{'owner': 'a', 'at': 1, 'ttl': 5}]}) == {'owner': 'a', 'expiry': 6, 'fence': 1, 'results': [{'granted': True, 'fence': 1}]}
assert solve({'kind': 'lease_fencing', 'owner': 'a', 'expiry': 10, 'fence': 2, 'requests': [{'owner': 'b', 'at': 9, 'ttl': 4}]}) == {'owner': 'a', 'expiry': 10, 'fence': 2, 'results': [{'granted': False, 'fence': 2}]}
