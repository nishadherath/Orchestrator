"""Visible smoke checks only the new reader after cutover."""
import json
import subprocess
import sys

request = {"phase": "cutover", "reader": "shadow", "value": 9,
           "record": {"legacy": 2, "shadow": 2}}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + "\n", text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"read": 9}
