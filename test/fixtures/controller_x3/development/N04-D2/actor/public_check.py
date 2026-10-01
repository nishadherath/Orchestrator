"""Visible smoke checks only the pre-rotation status."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps({"action": "status"}) + "\n",
                        text=True, capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
status = json.loads(result.stdout)
assert "blue" in status["accepted"] and status["signer"] in status["accepted"]
