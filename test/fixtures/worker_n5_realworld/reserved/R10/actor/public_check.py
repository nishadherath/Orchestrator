from app import solve
assert solve({'kind': 'lease_fencing', 'owner': None, 'expiry': 0, 'fence': 3, 'requests': [{'owner': 'x', 'at': 2, 'ttl': 3}, {'owner': 'y', 'at': 5, 'ttl': 3}]}) == {'owner': 'y', 'expiry': 8, 'fence': 5, 'results': [{'granted': True, 'fence': 4}, {'granted': True, 'fence': 5}]}
assert solve({'kind': 'lease_fencing', 'owner': 'x', 'expiry': 3, 'fence': 4, 'requests': []}) == {'owner': 'x', 'expiry': 3, 'fence': 4, 'results': []}
