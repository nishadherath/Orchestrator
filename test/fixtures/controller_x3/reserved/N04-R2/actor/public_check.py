"""Visible smoke checks only the existing API fixture name."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input='{"action":"fixture","name":"api"}\n',
                        text=True, capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["service"] == "api"
