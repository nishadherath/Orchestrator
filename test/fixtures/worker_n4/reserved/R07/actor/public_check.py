from app import solve
assert solve({'completions': [{'key': 'a', 'version': 1, 'value': 'new'}]}) == {'cache': {'a': {'version': 1, 'value': 'new'}}}
