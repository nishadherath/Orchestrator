from app import solve
assert solve({'external_key': None, 'local_checks': [True, False, True]}) == {'status': 'partial', 'local_passed': 2, 'blocked_on': 'external_key'}
