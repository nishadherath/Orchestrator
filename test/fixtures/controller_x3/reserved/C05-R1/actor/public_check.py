"""Visible smoke covers only one enqueued batch."""
import json
import subprocess
import sys

request = {"capacity": 2,
           "operations": [{"kind": "enqueue", "batch": ["a"]}]}
result = subprocess.run([sys.executable, "-B", "app.py"],
                        input=json.dumps(request) + chr(10), text=True,
                        capture_output=True, timeout=3)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout) == {
    "results": ["accepted"], "pending": [["a"]], "consumed": []}
