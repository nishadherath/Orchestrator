from app import solve
assert solve({'kind': 'inventory_reconcile', 'opening': {'x': 1}, 'events': [{'sku': 'x', 'delta': -2}, {'sku': 'x', 'delta': -1}, {'sku': 'x', 'delta': 1}]}) == {'stock': {'x': 1}, 'rejected': [0]}
assert solve({'kind': 'inventory_reconcile', 'opening': {'p': 2}, 'events': []}) == {'stock': {'p': 2}, 'rejected': []}
