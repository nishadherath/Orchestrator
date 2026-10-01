"""Visible smoke covers only a same-feed replay."""
import json
import subprocess
import sys

request = {"events": [
    {"feed": "public", "epoch": 1, "seq": 7, "record": "visible"},
    {"feed": "public", "epoch": 1, "seq": 7, "record": "visible"}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"emitted": ["visible"]}
