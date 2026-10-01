"""Visible smoke covers an ordinary same-key hit only."""
import json
import subprocess
import sys

trace = {"events": [
    {"op": "put", "namespace": "demo", "token": "k", "value": 7},
    {"op": "get", "namespace": "demo", "token": "k"},
]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(trace) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"results": [
    {"status": "stored"}, {"status": "hit", "value": 7}]}
