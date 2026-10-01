from app import solve
assert solve({'kind': 'config_precedence', 'key': 'port', 'environment': {'port': 8080}, 'file': {'port': 80}, 'defaults': {'port': 40}}) == {'value': 8080, 'source': 'environment'}
assert solve({'kind': 'config_precedence', 'key': 'port', 'environment': {}, 'file': {'port': 80}, 'defaults': {'port': 40}}) == {'value': 80, 'source': 'file'}
