from app import solve
assert solve({'kind': 'incident_triage', 'required': ['db', 'api'], 'checks': {'db': 'ok', 'api': 'fail'}}) == {'status': 'degraded', 'failing': ['api'], 'missing_evidence': []}
assert solve({'kind': 'incident_triage', 'required': ['db'], 'checks': {}}) == {'status': 'blocked', 'failing': ['db'], 'missing_evidence': ['db']}
