"""Visible smoke covers one successful checkout only."""
import json
import subprocess
import sys

request = {"events": [{"tenant": "acme", "fail": False}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout)["observed"] == [
    {"status": "ok", "tenant_seen": "acme"}]
