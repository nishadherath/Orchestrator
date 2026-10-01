"""Visible smoke covers the unchanged default, not the new override key."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps({"action": "client"}) + "\n",
                        text=True, capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"timeout_s": 0.75, "retries": 2}
