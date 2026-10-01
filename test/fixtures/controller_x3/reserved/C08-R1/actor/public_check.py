"""Visible smoke covers only one ordered record."""
import json
import subprocess
import sys

request = {"capacity": 2, "records": [{"sequence": 1, "value": "A"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
value = json.loads(result.stdout)
assert value["emitted"] == ["A"]
assert value["statuses"] == ["emitted"]
