from app import solve
assert solve({'kind': 'inventory_reconcile', 'opening': {'a': 2}, 'events': [{'sku': 'a', 'delta': -1}]}) == {'stock': {'a': 1}, 'rejected': []}
assert solve({'kind': 'inventory_reconcile', 'opening': {'a': 1}, 'events': [{'sku': 'a', 'delta': -2}, {'sku': 'a', 'delta': -1}]}) == {'stock': {'a': 0}, 'rejected': [0]}
