#!/usr/bin/env python3
"""Visible aligned-clock path; skew is not exercised."""
import json
import subprocess
import sys

request = {"leases": [
    {"id": "job-p", "server_now": 8, "worker_now": 8, "expires_at": 10}]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"renewable": ["job-p"], "expired": []}
