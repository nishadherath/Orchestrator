"""Visible API smoke does not inspect the formatter's import path."""
import json
import subprocess
import sys

request = {"action": "api", "customer": "Ada", "cents": 250}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["label"] == "Ada | USD 2.50"
