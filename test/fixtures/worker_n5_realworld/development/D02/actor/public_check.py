from app import solve
assert solve({'kind': 'retry_decision', 'status': 503, 'attempt': 1, 'max_attempts': 3, 'base_ms': 100, 'cap_ms': 1000}) == {'retry': True, 'delay_ms': 100}
assert solve({'kind': 'retry_decision', 'status': 200, 'attempt': 1, 'max_attempts': 3, 'base_ms': 100, 'cap_ms': 1000}) == {'retry': False, 'delay_ms': 0}
