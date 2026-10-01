"""Visible smoke checks that search remains enabled."""
import json
import subprocess
import sys

request = {"action": "flags", "flags": {"beta_exports": True, "search": True},
           "audit": []}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["flags"]["search"] is True
