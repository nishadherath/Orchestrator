"""Visible smoke covers only the untouched CLI pin."""
import json
import subprocess
import sys

request = {"action": "release", "service": "cli"}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "pin": {"version": "1.0.0", "digest": "sha256:cc00"}}
