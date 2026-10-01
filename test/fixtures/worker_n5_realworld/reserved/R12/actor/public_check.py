from app import solve
assert solve({'kind': 'dependency_diagnosis', 'status': {'a': 'ok', 'b': 'bad', 'c': 'bad'}, 'depends_on': {'b': ['a'], 'c': ['b']}}) == {'root_failures': ['b'], 'downstream': ['c'], 'complete': False}
assert solve({'kind': 'dependency_diagnosis', 'status': {'x': 'bad'}, 'depends_on': {}}) == {'root_failures': ['x'], 'downstream': [], 'complete': False}
