from app import solve
assert solve({'kind': 'message_delivery', 'already_delivered': ['z'], 'retry_limit': 2, 'messages': [{'id': 'z', 'outcome': 'ok', 'attempt': 1}, {'id': 'y', 'outcome': 'fail', 'attempt': 1}]}) == {'delivered': [], 'retry': ['y'], 'dead_letter': []}
assert solve({'kind': 'message_delivery', 'already_delivered': [], 'retry_limit': 1, 'messages': [{'id': 'a', 'outcome': 'fail', 'attempt': 1}, {'id': 'b', 'outcome': 'ok', 'attempt': 1}]}) == {'delivered': ['b'], 'retry': [], 'dead_letter': ['a']}
