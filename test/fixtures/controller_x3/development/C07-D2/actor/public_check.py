"""Visible smoke checks a timestamp far from local midnight."""
import json
import subprocess
import sys

request = {"timestamp": "2026-06-15T02:00:00+00:00"}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"window_day": "2026-06-15"}
