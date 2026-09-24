from app import solve
assert solve({'initial': 'a', 'events': [{'kind': 'read'}]}) == {'reads': ['a'], 'current': 'a'}
