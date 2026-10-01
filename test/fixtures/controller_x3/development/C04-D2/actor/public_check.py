"""Visible smoke checks the first attempt, which never enters retry.forward."""
import json
import subprocess
import sys

request = {"job": {"id": "visible", "payload": {"op": "send"},
                   "context": {"tenant": "demo", "trace": "t0"}},
           "attempt": 1, "field": "tenant"}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"value": "demo"}
