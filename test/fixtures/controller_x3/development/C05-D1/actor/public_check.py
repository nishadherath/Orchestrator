#!/usr/bin/env python3
"""Visible small match; streaming retention and window rejection are absent."""
import json
import subprocess
import sys

request = {"left": [{"id": "L0", "key": "a", "time": 10}],
           "right": [{"id": "R0", "key": "a", "time": 11}], "window": 2}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"pairs": [["L0", "R0"]]}
