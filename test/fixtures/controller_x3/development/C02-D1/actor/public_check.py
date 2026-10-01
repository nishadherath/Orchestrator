#!/usr/bin/env python3
"""Visible new-column read; legacy fallback and backfill are not exercised."""
import json
import subprocess
import sys

request = {"op": "read", "records": [{"id": "p1", "current": 13}]}
completed = subprocess.run([sys.executable, "-B", "app.py"],
                           input=json.dumps(request) + "\n", text=True,
                           capture_output=True, timeout=3)
assert completed.returncode == 0, completed.stderr
assert json.loads(completed.stdout) == {"values": [{"id": "p1", "value": 13}]}
