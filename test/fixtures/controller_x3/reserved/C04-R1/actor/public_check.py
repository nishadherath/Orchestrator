"""Visible smoke covers the already-scoped report listing."""
import json
import subprocess
import sys

own = {"id": "r-a", "tenant": "acme", "state": "active", "body": "A"}
foreign = {"id": "r-b", "tenant": "beta", "state": "active", "body": "B"}
request = {"tenant": "acme", "operation": "list", "reports": [own, foreign]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == [own]
