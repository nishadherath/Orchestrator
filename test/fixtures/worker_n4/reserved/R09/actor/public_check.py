from app import solve
assert solve({'records': [{'id': 'a'}, {'id': 'b'}], 'cursor': None, 'limit': 1}) == {'ids': ['a'], 'next_cursor': 'a'}
