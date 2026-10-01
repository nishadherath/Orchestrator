"""Visible smoke covers a non-contentious two-request interval."""
import json
import subprocess
import sys

request = {"capacity": 2, "requests": [
    {"id": "public-f", "kind": "foreground"},
    {"id": "public-r", "kind": "retry"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"admitted": ["public-f", "public-r"],
                                     "deferred": []}
