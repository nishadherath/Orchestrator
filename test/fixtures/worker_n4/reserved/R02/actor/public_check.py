from app import solve
assert solve({'root': '/srv/data', 'requested': 'a/file.txt'}) == {'ok': True, 'path': '/srv/data/a/file.txt'}
