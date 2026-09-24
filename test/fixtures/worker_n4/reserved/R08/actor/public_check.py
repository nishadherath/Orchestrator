from app import solve
assert solve({'capacity': 1, 'shutdown_at': 10, 'drain_deadline': 10, 'tasks': [{'id': 'a', 'duration': 2}]}) == {'completed': ['a'], 'rejected': []}
