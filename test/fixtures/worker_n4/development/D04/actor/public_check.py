from app import solve
assert solve({'budget_ms': 100, 'hops_ms': [10]}) == {'completed_hops': 1, 'elapsed_ms': 10, 'timed_out': False}
