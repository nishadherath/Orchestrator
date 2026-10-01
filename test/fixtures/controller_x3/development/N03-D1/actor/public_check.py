#!/usr/bin/env python3
"""Visible current-policy check; no new approved duration is supplied."""
import json
import subprocess
import sys

request = {"tenant": "north"}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"tenant": "north", "retention_days": 30}
