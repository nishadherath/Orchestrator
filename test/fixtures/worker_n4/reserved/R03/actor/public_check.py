from app import solve
assert solve({'threshold': 2, 'reset_ticks': 2, 'events': ['ok']}) == {'admitted': [True], 'state': 'closed'}
