from app import solve
assert solve({'kind': 'token_bucket', 'capacity': 3, 'start': 0, 'refill_per_second': 1, 'requests': [{'at': 0, 'cost': 2}, {'at': 0, 'cost': 2}]}) == {'allowed': [True, False], 'remaining': 1}
assert solve({'kind': 'token_bucket', 'capacity': 3, 'start': 0, 'refill_per_second': 1, 'requests': [{'at': 1, 'cost': 3}, {'at': 2, 'cost': 1}]}) == {'allowed': [True, True], 'remaining': 0}
