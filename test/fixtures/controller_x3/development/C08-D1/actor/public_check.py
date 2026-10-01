#!/usr/bin/env python3
"""Visible settlement path; the opposing reservation order is not checked."""
import json
import subprocess
import sys

request = {"caller": "settlement"}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"order": ["account", "inventory"]}
