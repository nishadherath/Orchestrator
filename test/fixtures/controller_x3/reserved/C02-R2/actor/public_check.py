"""Visible smoke covers a plain update, not deletion or additive boundaries."""
import json
import subprocess
import sys

request = {"log": [{"op": "put", "key": "a", "value": 2},
                   {"op": "put", "key": "a", "value": 5}],
           "checkpoint": 2}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["state"] == {"a": 5}
