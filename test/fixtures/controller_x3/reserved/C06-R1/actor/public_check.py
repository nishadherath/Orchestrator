"""Visible smoke covers one changed key and one read."""
import json
import subprocess
import sys

request = {"cache": {"a": "old"}, "backend": {"a": "fresh"},
           "invalidated": ["a"], "waves": [["a"]]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "cache": {"a": "fresh"}, "loads": [{"tick": 0, "key": "a"}],
    "responses": [{"tick": 0, "key": "a", "status": "value",
                   "value": "fresh"}]}
