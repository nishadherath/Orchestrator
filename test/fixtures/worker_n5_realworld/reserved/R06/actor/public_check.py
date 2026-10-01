from app import solve
assert solve({'kind': 'incident_triage', 'required': ['cache', 'db'], 'checks': {'cache': 'slow', 'db': 'ok'}}) == {'status': 'degraded', 'failing': ['cache'], 'missing_evidence': []}
assert solve({'kind': 'incident_triage', 'required': ['x', 'y'], 'checks': {'x': 'bad', 'y': 'bad'}}) == {'status': 'degraded', 'failing': ['x', 'y'], 'missing_evidence': []}
