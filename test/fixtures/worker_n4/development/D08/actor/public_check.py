from app import solve
assert solve({'requests': [{'key': 'a', 'outcome': 'ok'}]}) == {'executions': 1, 'results': ['ok']}
