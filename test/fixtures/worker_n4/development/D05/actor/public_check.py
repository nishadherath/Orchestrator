from app import solve
assert solve({'rows': [{'id': 'a', 'amount': 1}]}) == {'committed': ['a'], 'error': None}
