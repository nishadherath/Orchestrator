"""Visible smoke covers a consistent index entry only."""
import json
import subprocess
import sys

request = {"key": "visible", "rows": [
    {"key": "visible", "rev": 1, "value": "current", "deleted": False}],
    "snapshot": {"visible": {"rev": 1, "value": "current"}}}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"status": "found", "value": "current"}
