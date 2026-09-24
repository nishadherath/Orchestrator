from app import solve
assert solve({'etag': 'v1', 'if_none_match': None, 'body': 'hello'}) == {'status': 200, 'body': 'hello', 'etag': 'v1'}
