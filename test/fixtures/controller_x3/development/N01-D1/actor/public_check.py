"""Visible invoice smoke; it does not inspect the renamed public symbol."""
import json
import subprocess
import sys

request = {"action": "invoice", "cents": 200}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"invoice": "Invoice: USD 2.00"}
