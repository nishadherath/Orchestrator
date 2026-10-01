from app import solve
assert solve({'kind': 'page_merge', 'pages': [[{'id': 'a'}, {'id': 'b'}], [{'id': 'b'}, {'id': 'c'}]], 'offset': 0, 'limit': 2}) == {'items': [{'id': 'a'}, {'id': 'b'}], 'next_offset': 2}
assert solve({'kind': 'page_merge', 'pages': [], 'offset': 0, 'limit': 3}) == {'items': [], 'next_offset': None}
