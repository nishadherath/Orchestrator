"""Visible smoke covers a minimal legacy envelope only."""
import json
import subprocess
import sys

request = {"op": "rewrite", "name": "new", "record": {
    "version": 1, "id": "public", "payload": {"name": "old"}}}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"record": {
    "version": 1, "id": "public", "payload": {"name": "new"}}}
