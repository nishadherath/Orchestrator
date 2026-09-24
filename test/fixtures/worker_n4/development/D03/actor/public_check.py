from app import solve
assert solve({'method': 'GET', 'statuses': [200], 'max_attempts': 3}) == {'attempts': [200], 'final': 200}
