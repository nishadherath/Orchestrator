from app import solve
assert solve({'kind': 'page_merge', 'pages': [[{'id': 'r'}], [{'id': 's'}, {'id': 't'}]], 'offset': 0, 'limit': 1}) == {'items': [{'id': 'r'}], 'next_offset': 1}
assert solve({'kind': 'page_merge', 'pages': [[{'id': 1}], [{'id': 2}]], 'offset': 1, 'limit': 1}) == {'items': [{'id': 2}], 'next_offset': None}
