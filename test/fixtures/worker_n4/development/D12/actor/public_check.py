from app import solve
assert solve({'retention_days': None, 'records': [{'id': 'a', 'age_days': 99}]}) == {'action': 'clarify', 'missing': 'retention_days'}
