from app import solve
assert solve({'operations': [{'kind': 'put', 'tenant': 'a', 'key': 'k', 'value': 1}, {'kind': 'get', 'tenant': 'a', 'key': 'k'}]}) == {'reads': [1]}
