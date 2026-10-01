from app import solve
assert solve({'kind': 'dependency_diagnosis', 'status': {'db': 'bad', 'api': 'bad'}, 'depends_on': {'api': ['db']}}) == {'root_failures': ['db'], 'downstream': ['api'], 'complete': False}
assert solve({'kind': 'dependency_diagnosis', 'status': {'db': 'ok', 'api': 'bad'}, 'depends_on': {'api': ['db']}}) == {'root_failures': ['api'], 'downstream': [], 'complete': False}
