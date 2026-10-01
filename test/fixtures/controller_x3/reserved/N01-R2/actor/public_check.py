"""Visible smoke checks only the unchanged request identifier."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input='{"action":"header"}\n', text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["fields"]["REQUEST_ID"] == 1
