"""Visible smoke covers only one ASCII message."""
import json
import subprocess
import sys

request = {"operation": "roundtrip", "messages": ["ok"]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"messages": ["ok"]}
