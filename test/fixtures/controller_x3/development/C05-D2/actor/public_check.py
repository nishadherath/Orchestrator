"""Visible smoke checks a tiny full-page selection."""
import json
import subprocess
import sys

request = {"size": 2, "offset": 0, "limit": 2}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "selected": ["r000", "r001"], "reads": 2}
