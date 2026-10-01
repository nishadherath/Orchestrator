"""Visible smoke checks one delivery, not replay or ordering."""
import json
import subprocess
import sys

request = {"deliveries": [{"delivery_id": "d1", "customer": "alice",
                           "sequence": 1, "amount": 5}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"totals": {"alice": 5},
                                    "applied": ["d1"]}
