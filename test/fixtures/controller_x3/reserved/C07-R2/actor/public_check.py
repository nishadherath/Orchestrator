"""Visible smoke covers one monotonic update."""
import json
import subprocess
import sys

request = {"events": [{"sequence": 1, "revision": 1, "value": "A"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "current": {"revision": 1, "value": "A"}, "statuses": ["applied"]}
