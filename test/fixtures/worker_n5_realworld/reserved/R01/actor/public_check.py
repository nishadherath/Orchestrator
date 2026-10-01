from app import solve
assert solve({'kind': 'config_precedence', 'key': 'timeout', 'environment': {'timeout': 0}, 'file': {}, 'defaults': {'timeout': 10}}) == {'value': 0, 'source': 'environment'}
assert solve({'kind': 'config_precedence', 'key': 'timeout', 'environment': {}, 'file': {'timeout': None}, 'defaults': {'timeout': 10}}) == {'value': 10, 'source': 'defaults'}
