#!/usr/bin/env python3
"""Visible oversized limit; the one-extra-row bug is not exercised."""
import json
import subprocess
import sys

request = {"items": ["p", "q"], "limit": 5}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"selected": ["p", "q"]}
