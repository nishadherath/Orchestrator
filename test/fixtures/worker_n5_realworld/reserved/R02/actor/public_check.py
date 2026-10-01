from app import solve
assert solve({'kind': 'retry_decision', 'status': 408, 'attempt': 1, 'max_attempts': 2, 'base_ms': 10, 'cap_ms': 100}) == {'retry': True, 'delay_ms': 10}
assert solve({'kind': 'retry_decision', 'status': 502, 'attempt': 2, 'max_attempts': 4, 'base_ms': 25, 'cap_ms': 60}) == {'retry': True, 'delay_ms': 50}
