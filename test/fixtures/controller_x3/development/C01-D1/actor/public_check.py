#!/usr/bin/env python3
"""Visible exact-ID path; client-version aliases are deliberately absent."""
import json
import subprocess
import sys

request = {"orders": [{"account": "west", "id": "PO-7"}],
           "receipts": [{"account": "west", "id": "PO-7"}]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"settled": ["PO-7"], "pending": []}
