"""Visible smoke covers one uncontested promotion and write."""
import json
import subprocess
import sys

request = {"operations": [
    {"kind": "promote", "replica": "a", "term": 1, "at": 0},
    {"kind": "write", "replica": "a", "term": 1, "at": 1, "value": "A"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "statuses": ["promoted", "written"], "writes": ["A"],
    "owner": "a", "term": 1, "expires_at": 5}
