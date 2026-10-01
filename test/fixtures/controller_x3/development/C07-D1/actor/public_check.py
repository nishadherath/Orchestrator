#!/usr/bin/env python3
"""Visible whole-cent path; fractional-cent rounding is not exercised."""
import json
import subprocess
import sys

request = {"amounts": ["1.25", "2.25"]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"ledger": "3.50", "statement": "3.50"}
