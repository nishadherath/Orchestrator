from app import solve
assert solve({'cli': 'blue', 'environment': 'green', 'file': 'red', 'default': 'black'}) == {'value': 'blue', 'source': 'cli'}
