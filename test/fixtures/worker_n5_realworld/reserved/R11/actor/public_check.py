from app import solve
assert solve({'kind': 'token_bucket', 'capacity': 4, 'start': 0, 'refill_per_second': 1, 'requests': [{'at': 2, 'cost': 3}, {'at': 1, 'cost': 2}]}) == {'allowed': [True, False], 'remaining': 1}
assert solve({'kind': 'token_bucket', 'capacity': 1, 'start': 0, 'refill_per_second': 1, 'requests': [{'at': 0, 'cost': 2}, {'at': 1, 'cost': 1}]}) == {'allowed': [False, True], 'remaining': 0}
