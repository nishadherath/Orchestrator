"""Visible smoke only verifies the record value."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input='{"action":"read"}\n', text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["value"] == "record-7"
