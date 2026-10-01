from app import solve
assert solve({'kind': 'message_delivery', 'already_delivered': [], 'retry_limit': 3, 'messages': [{'id': 'a', 'outcome': 'ok', 'attempt': 1}]}) == {'delivered': ['a'], 'retry': [], 'dead_letter': []}
assert solve({'kind': 'message_delivery', 'already_delivered': ['a'], 'retry_limit': 3, 'messages': [{'id': 'a', 'outcome': 'fail', 'attempt': 3}]}) == {'delivered': [], 'retry': [], 'dead_letter': []}
