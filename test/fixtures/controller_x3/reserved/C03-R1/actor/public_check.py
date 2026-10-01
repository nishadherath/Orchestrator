"""Visible smoke covers one owner, not overlap or takeover."""
import json
import subprocess
import sys

request = {"events": [
    {"op": "claim", "worker": "A", "at": 0, "lease": 5},
    {"op": "complete", "worker": "A", "token": 1, "at": 1,
     "value": "v1"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "results": [{"status": "claimed", "token": 1},
                {"status": "committed"}],
    "owner": "A", "token": 1, "committed": "v1"}
