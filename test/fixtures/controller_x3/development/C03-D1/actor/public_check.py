#!/usr/bin/env python3
"""Visible smoke check; it does not cover retries or tenant separation."""
import json
import subprocess
import sys

request = {"attempts": [{"tenant": "acme", "key": "p1", "amount": 100,
                         "phase": "commit"}]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {
    "results": [{"status": "committed", "balance": 100}],
    "balances": {"acme": 100}}
