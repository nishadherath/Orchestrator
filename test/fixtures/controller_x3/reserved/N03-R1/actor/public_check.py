"""Visible smoke covers a modern client that sends trace context."""
import json
import subprocess
import sys

request = {"client_version": "2.2", "has_trace": True}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"accepted": True}
