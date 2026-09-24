from app import solve
assert solve({'checkpoint': 0, 'records': [{'seq': 1, 'value': 'a'}]}) == {'values': ['a'], 'checkpoint': 1}
