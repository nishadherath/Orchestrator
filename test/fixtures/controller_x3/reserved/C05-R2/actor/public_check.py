"""Visible smoke covers a current-reader roundtrip only."""
import json
import subprocess
import sys

request = {"operation": "roundtrip", "decoder": "current",
           "payload_hex": "4f4b"}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {"payload_hex": "4f4b"}
