from app import solve
assert solve({'capacity': 1, 'events': [{'kind': 'acquire', 'id': 'a'}]}) == {'active': ['a'], 'waiting': [], 'cancelled': []}
