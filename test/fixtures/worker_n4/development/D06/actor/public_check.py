from app import solve
assert solve({'required': ['v1'], 'applied': []}) == {'apply': ['v1'], 'complete': False}
