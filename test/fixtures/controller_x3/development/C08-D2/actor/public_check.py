"""Visible contract smoke covers one successful response."""
import json
import subprocess
import sys

record = {"id": "visible", "status": "ready", "trace_id": "trace-public"}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(record) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"id": "visible", "status": "ready"}
