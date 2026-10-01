"""Visible smoke covers only a new-writer/new-reader roundtrip."""
import json
import subprocess
import sys

request = {"operation": "roundtrip_new", "value": 7}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"value": 7}
