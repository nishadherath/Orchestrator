"""Visible smoke exercises one heading only."""
import json
import subprocess
import sys

request = {"steps": [{"kind": "heading", "text": "A"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"rendered": ["A"]}
