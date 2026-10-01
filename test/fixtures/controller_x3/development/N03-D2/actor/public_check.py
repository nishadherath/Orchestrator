"""Visible smoke covers north, not the requested pilot move."""
import json
import subprocess
import sys

result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps({"tenant": "north"}) + "\n",
                        text=True, capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"tenant": "north", "region": "us-west-2"}
